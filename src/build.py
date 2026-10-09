import yaml
import os
import base64
import copy
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


def render_and_save(data, template, output_filename):
    """Funkcja pomocnicza do renderowania i zapisywania pliku HTML"""
    output_html = template.render(data)
    output_path = Path('output') / output_filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    print(f"[+] Wygenerowano: {output_filename}")


def main():
    print("Rozpoczynam generowanie CV...\n")

    base_yaml_path = Path('data/base.yaml')
    apps_dir = Path('data/applications')
    os.makedirs('output', exist_ok=True)

    # 1. Wczytanie bazy (Single Source of Truth)
    if not base_yaml_path.exists():
        print(f"[BŁĄD] Nie znaleziono pliku bazowego: {base_yaml_path}")
        return

    with open(base_yaml_path, 'r', encoding='utf-8') as f:
        base_data = yaml.safe_load(f)

    # 2. Magia Base64 - robimy to tylko raz dla bazy
    photo_path_str = base_data.get('personal_info', {}).get('photo_path')
    if photo_path_str:
        photo_path = Path(photo_path_str)
        if photo_path.exists():
            with open(photo_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                ext = photo_path.suffix.lower().replace('.', '')
                mime_type = f"image/{ext}" if ext in ['png', 'jpeg', 'jpg'] else "image/png"
                base_data['personal_info']['photo_path'] = f"data:{mime_type};base64,{encoded_string}"
        else:
            print(f"[!] Ostrzeżenie: Nie znaleziono zdjęcia: '{photo_path}'")

    # 3. Konfiguracja Jinja2
    env = Environment(loader=FileSystemLoader('templates'))
    try:
        template = env.get_template('template.html')
    except Exception as e:
        print(f"[BŁĄD] Nie można załadować szablonu: {e}")
        return

    # 4. Generowanie wersji bazowej (czyste CV bez nadpisań)
    render_and_save(base_data, template, "cv_base.html")

    # 5. Automatyczne generowanie wszystkich profili z folderu applications/
    if apps_dir.exists():
        for app_file in apps_dir.glob('*.yaml'):
            with open(app_file, 'r', encoding='utf-8') as f:
                app_data = yaml.safe_load(f)

            if app_data:
                # KLUCZOWE: Tworzymy głęboką kopię bazy, żeby jej nie "zabrudzić"
                merged_data = deep_merge(copy.deepcopy(base_data), app_data)
                output_filename = f"cv_{app_file.stem}.html"
                render_and_save(merged_data, template, output_filename)

    print("\nZakończono pomyślnie! Wszystkie pliki znajdują się w folderze 'output/'.")


if __name__ == "__main__":
    main()