"""Generator CV: base.yaml + data/applications/*.yaml -> output/*.html (opcjonalnie PDF).

Użycie:
    python build.py              # wszystkie aplikacje
    python build.py pobud        # tylko wybrane (po nazwie pliku, bez .yaml)
    python build.py --pdf        # dodatkowo PDF (wymaga: pip install playwright)
    python build.py --strict     # znaczniki SPRAWDŹ/TODO blokują build zamiast ostrzegać
"""
import argparse
import base64
import copy
import mimetypes
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Ścieżki liczone od położenia skryptu, a nie od katalogu, z którego go uruchomiono.
ROOT = Path(__file__).resolve().parent
BASE_YAML = ROOT / 'data' / 'base.yaml'
APPS_DIR = ROOT / 'data' / 'applications'
TEMPLATES_DIR = ROOT / 'templates'
OUTPUT_DIR = ROOT / 'output'
TEMPLATE_NAME = 'template.html'

# Pola, które KAŻDA aplikacja musi nadpisać. Brak = błąd, bo do CV trafiłaby wersja z bazy
# (dokładnie tak tytuł "Asystentka Notariusza" trafił do CV dla Pobud).
REQUIRED_OVERRIDES = {'personal_info': ['title', 'summary']}

# Znaczniki, które oznaczają niezweryfikowaną treść.
TODO_PATTERN = re.compile(r'SPRAWDŹ|TODO|FIXME')


def deep_merge(base, override):
    """Rekurencyjnie łączy słowniki. Listy i wartości proste są zastępowane w całości."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def unknown_keys(override, base, prefix=''):
    """Klucze z aplikacji, których nie ma w bazie (najczęściej literówka, np. 'persona_info')."""
    found = []
    for key, value in override.items():
        path = f'{prefix}{key}'
        if key not in base:
            found.append(path)
        elif isinstance(value, dict) and isinstance(base[key], dict):
            found.extend(unknown_keys(value, base[key], prefix=f'{path}.'))
    return found


def validate_app(app_path, app_data, base_data, strict):
    """Zwraca listę błędów (blokują build). Ostrzeżenia wypisuje od razu."""
    errors = []

    for path in unknown_keys(app_data, base_data):
        errors.append(f"nieznany klucz '{path}' (brak w base.yaml; literówka?)")

    for section, fields in REQUIRED_OVERRIDES.items():
        for field in fields:
            if field not in (app_data.get(section) or {}):
                errors.append(f"brak {section}.{field}: zostałaby użyta wersja z base.yaml")

    raw = app_path.read_text(encoding='utf-8')
    for lineno, line in enumerate(raw.splitlines(), start=1):
        if TODO_PATTERN.search(line):
            msg = f"linia {lineno}: niezweryfikowana treść: {line.strip()}"
            if strict:
                errors.append(msg)
            else:
                print(f"    [ostrzeżenie] {msg}")

    return errors


def embed_photo(data, source_dir):
    """Zamienia personal_info.photo_path na data URI. Wywoływane PO scaleniu,
    więc działa też, gdy aplikacja nadpisuje zdjęcie."""
    info = data.get('personal_info') or {}
    photo = info.get('photo_path')
    if not photo or str(photo).startswith('data:'):
        return
    photo_path = Path(photo)
    if not photo_path.is_absolute():
        photo_path = source_dir / photo_path
    if not photo_path.exists():
        print(f"    [ostrzeżenie] nie znaleziono zdjęcia: {photo_path}")
        info['photo_path'] = None
        return
    mime, _ = mimetypes.guess_type(photo_path.name)
    if not mime or not mime.startswith('image/'):
        print(f"    [ostrzeżenie] nieobsługiwany typ pliku zdjęcia: {photo_path.name}")
        info['photo_path'] = None
        return
    encoded = base64.b64encode(photo_path.read_bytes()).decode('ascii')
    info['photo_path'] = f'data:{mime};base64,{encoded}'


def render(data, template, name):
    data = copy.deepcopy(data)
    embed_photo(data, ROOT)
    html_path = OUTPUT_DIR / f'cv_{name}.html'
    html_path.write_text(template.render(data), encoding='utf-8')
    print(f"[+] {html_path.relative_to(ROOT)}")
    return html_path


def export_pdfs(html_paths):
    """Renderuje HTML do PDF w Chromium (powtarzalnie, bez nagłówków przeglądarki).
    Marginesy i rozmiar strony bierze z CSS szablonu (@page)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[BŁĄD] --pdf wymaga Playwright: pip install playwright && playwright install chromium")
        return False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for html_path in html_paths:
            pdf_path = html_path.with_suffix('.pdf')
            page.goto(html_path.as_uri(), wait_until='load')
            page.pdf(path=str(pdf_path), format='A4', print_background=True,
                     prefer_css_page_size=True)
            print(f"[+] {pdf_path.relative_to(ROOT)}")
        browser.close()
    return True


def main():
    parser = argparse.ArgumentParser(description='Generator CV')
    parser.add_argument('apps', nargs='*', help='nazwy aplikacji (domyślnie wszystkie)')
    parser.add_argument('--pdf', action='store_true', help='generuj także PDF')
    parser.add_argument('--strict', action='store_true',
                        help='znaczniki SPRAWDŹ/TODO są błędem, a nie ostrzeżeniem')
    args = parser.parse_args()

    if not BASE_YAML.exists():
        print(f"[BŁĄD] nie znaleziono pliku bazowego: {BASE_YAML}")
        return 1
    base_data = load_yaml(BASE_YAML)

    # autoescape: znaki & < > w treści (np. "B&R") nie zepsują HTML.
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html']),
    )
    template = env.get_template(TEMPLATE_NAME)

    OUTPUT_DIR.mkdir(exist_ok=True)
    generated = []
    failed = []

    if not args.apps:
        generated.append(render(base_data, template, 'base'))

    app_files = sorted(APPS_DIR.glob('*.yaml')) if APPS_DIR.exists() else []
    if args.apps:
        wanted = set(args.apps)
        missing = wanted - {f.stem for f in app_files}
        for name in sorted(missing):
            print(f"[BŁĄD] brak pliku data/applications/{name}.yaml")
            failed.append(name)
        app_files = [f for f in app_files if f.stem in wanted]

    for app_file in app_files:
        print(f"--- {app_file.stem}")
        app_data = load_yaml(app_file)
        errors = validate_app(app_file, app_data, base_data, args.strict)
        if errors:
            for e in errors:
                print(f"    [BŁĄD] {e}")
            print(f"[-] pominięto {app_file.stem}")
            failed.append(app_file.stem)
            continue
        merged = deep_merge(copy.deepcopy(base_data), app_data)
        generated.append(render(merged, template, app_file.stem))

    if args.pdf and generated and not export_pdfs(generated):
        return 1

    if failed:
        print(f"\nZakończono z błędami: {', '.join(failed)}")
        return 1
    print(f"\nGotowe. Pliki w {OUTPUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == '__main__':
    sys.exit(main())