#!/bin/zsh
# Двойной клик — запускает курс в браузере. Окно Терминала не закрывайте, пока учитесь.
cd "$(dirname "$0")"
if command -v uv >/dev/null 2>&1; then exec uv run --no-project python tools/serve.py
else exec python3 tools/serve.py; fi
