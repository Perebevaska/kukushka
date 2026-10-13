#!/usr/bin/env bash
# Запуск курса на Linux: ./Курс-Linux.sh (или bash Курс-Linux.sh). Окно терминала не закрывайте, пока учитесь.
cd "$(dirname "$0")" || exit 1
if command -v uv >/dev/null 2>&1; then exec uv run --no-project python tools/serve.py "$@"; fi
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    exec "$py" tools/serve.py "$@"
  fi
done
echo "Не найден Python 3.8 или новее. Установите его, например:"
echo "  Ubuntu/Debian: sudo apt install python3"
echo "  Fedora:        sudo dnf install python3"
echo "  Arch:          sudo pacman -S python"
read -r -p "Нажмите Enter, чтобы закрыть окно…" _
exit 1
