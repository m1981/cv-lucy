#!/bin/bash

echo "========================================"
echo "   Generator CV (Base + Overrides)      "
echo "========================================"
echo ""
echo "Dostępne profile w folderze data/applications/:"
ls -1 data/applications/*.yaml 2>/dev/null | xargs -n 1 basename | sed 's/\.yaml$//' || echo "  (brak profili - wygeneruje tylko bazę)"
echo ""

read -p "Wpisz nazwę profilu (np. nowak) lub wciśnij ENTER dla bazy: " profile_name

if [ -z "$profile_name" ]; then
    uv run build.py
else
    # Automatycznie dodajemy .yaml jeśli użytkownik tego nie zrobił
    if [[ "$profile_name" != *.yaml ]]; then
        profile_name="${profile_name}.yaml"
    fi

    # Automatycznie budujemy pełną ścieżkę
    full_path="data/applications/$profile_name"

    uv run build.py "$full_path"
fi