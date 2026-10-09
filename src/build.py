import yaml
import base64
import os
from jinja2 import Environment, FileSystemLoader

# 1. Wczytanie danych z pliku YAML
with open('cv_data.yaml', 'r', encoding='utf-8') as file:
    cv_data = yaml.safe_load(file)

# --- NOWOŚĆ: Automatyczne osadzanie zdjęcia (Base64) ---
# Pobieramy ścieżkę do zdjęcia z pliku YAML
photo_path = cv_data['personal_info'].get('photo_path')

# Jeśli ścieżka nie jest pusta i plik faktycznie istnieje na dysku
if photo_path and os.path.exists(photo_path):
    # Otwieramy zdjęcie i konwertujemy je na ciąg znaków Base64
    with open(photo_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

        # Zastępujemy zwykłą ścieżkę gotowym kodem data:URI
        # Zakładam format PNG (zgodnie z przesłanym obrazkiem)
        cv_data['personal_info']['photo_path'] = f"data:image/png;base64,{encoded_string}"
else:
    print(f"Ostrzeżenie: Nie znaleziono pliku ze zdjęciem: '{photo_path}'")
# --------------------------------------------------------

# 2. Konfiguracja środowiska Jinja2
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.html')

# 3. Renderowanie HTML z wstrzykniętymi danymi
output_html = template.render(cv_data)

# 4. Zapisanie gotowego pliku
with open('cv_gotowe.html', 'w', encoding='utf-8') as file:
    file.write(output_html)

print("Sukces! Wygenerowano plik cv_gotowe.html")