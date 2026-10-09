import yaml
from jinja2 import Environment, FileSystemLoader

# 1. Wczytanie danych z pliku YAML
with open('cv_data.yaml', 'r', encoding='utf-8') as file:
    cv_data = yaml.safe_load(file)

# 2. Konfiguracja środowiska Jinja2
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.html')

# 3. Renderowanie HTML z wstrzykniętymi danymi
output_html = template.render(cv_data)

# 4. Zapisanie gotowego pliku
with open('cv_gotowe.html', 'w', encoding='utf-8') as file:
    file.write(output_html)

print("Sukces! Wygenerowano plik cv_gotowe.html")