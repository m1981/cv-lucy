import yaml
import sys
import os
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def deep_merge(base, override):
    """Rekurencyjnie łączy dwa słowniki (nadpisuje bazę danymi z override)"""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def main():
    # 1. Ustalenie ścieżek w nowej architekturze
    base_yaml_path = Path('data/base.yaml')

    if len(sys.argv) > 1:
        app_yaml_path = Path(sys.argv[1])
        output_filename = f"cv_{app_yaml_path.stem}.html"
    else:
        app_yaml_path = None
        output_filename = "cv_base.html"

    # 2. Wczytanie bazy (Single Source of Truth)
    if not base_yaml_path.exists():
        print(f"[BŁĄD] Nie znaleziono pliku bazowego: {base_yaml_path}")
        sys.exit(1)

    with open(base_yaml_path, 'r', encoding='utf-8') as f:
        cv_data = yaml.safe_load(f)

    # 3. Wczytanie i nałożenie nadpisań (jeśli podano plik profilu)
    if app_yaml_path and app_yaml_path.exists():
        with open(app_yaml_path, 'r', encoding='utf-8') as f:
            app_data = yaml.safe_load(f)
            if app_data:
                cv_data = deep_merge(cv_data, app_data)
        print(f"[*] Nałożono profil: {app_yaml_path.name}")
    else:
        print("[*] Generowanie wersji bazowej (brak profilu).")

    # 4. Magia Base64 - osadzanie zdjęcia w HTML
    photo_path_str = cv_data.get('personal_info', {}).get('photo_path')
    if photo_path_str:
        photo_path = Path(photo_path_str)
        if photo_path.exists():
            with open(photo_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                # Rozpoznanie formatu (png/jpg)
                ext = photo_path.suffix.lower().replace('.', '')
                mime_type = f"image/{ext}" if ext in ['png', 'jpeg', 'jpg'] else "image/png"
                # Podmiana ścieżki na gotowy kod Base64
                cv_data['personal_info']['photo_path'] = f"data:{mime_type};base64,{encoded_string}"
        else:
            print(f"[!] Ostrzeżenie: Nie znaleziono zdjęcia pod ścieżką: '{photo_path}'")

    # 5. Konfiguracja Jinja2 i ładowanie szablonu
    env = Environment(loader=FileSystemLoader('templates'))
    try:
        template = env.get_template('template.html')
    except Exception as e:
        print(f"[BŁĄD] Nie można załadować szablonu 'templates/template.html': {e}")
        sys.exit(1)

    # 6. Renderowanie i zapis
    output_html = template.render(cv_data)

    os.makedirs('output', exist_ok=True)
    output_path = Path('output') / output_filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)

    print(f"[+] Sukces! Plik wygenerowany w: {output_path.absolute()}")


if __name__ == "__main__":
    main()