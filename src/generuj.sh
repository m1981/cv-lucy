#!/bin/bash

# 1. Przejdź do folderu ze skryptem (src/)
cd "$(dirname "$0")" || exit

# 2. Sprawdź, czy 'uv' jest zainstalowane w systemie
if ! command -v uv &> /dev/null; then
    echo "Błąd: Narzędzie 'uv' nie jest zainstalowane."
    echo "Zainstaluj je wpisując w terminalu: brew install uv"
    exit 1
fi

echo "Uruchamianie przez uv..."

# 3. uv run automatycznie ogarnia venv, instaluje zależności z pyproject.toml i odpala skrypt
uv run build.py

echo "Gotowe! Plik wygenerowany w: $(pwd)/cv_gotowe.html"