#!/usr/bin/env python3
"""Экспорт одного урока для verify.mjs — когда остальной курс в работе.

    python3 tools/export_one.py content/ch06/02-split.md build/one.json
    node tools/verify.mjs build/one.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
ch, ls = src.parent.name, src.stem
build.CH_DISPLAY[ch] = True
build.export({(ch, ls): build.parse_lesson(src)}, out)
