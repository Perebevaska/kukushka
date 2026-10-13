#!/usr/bin/env python3
"""Отчёт «Где было трудно» по progress/progress.json — для правки уроков.

    uv run tools/hard_spots.py            # печатает Markdown
    uv run tools/hard_spots.py > build/трудные-места.md
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    state = json.loads((ROOT / 'progress' / 'progress.json').read_text(encoding='utf-8'))
    course = (ROOT / 'site' / 'assets' / 'course.js').read_text(encoding='utf-8')
    course = json.loads(re.sub(r'^window\.DSC_COURSE = |;\s*$', '', course.strip()))
    titles, lessons = {}, {}
    for ch in course:
        for ls in ch['lessons']:
            lessons[f'{ch["id"]}/{ls["id"]}'] = f'{ls["n"]}. {ls["title"]}'
            for t in ls['tasks']:
                titles[f'{ch["id"]}/{ls["id"]}/{t["id"]}'] = t['title']
    rows = []
    for k, e in state.get('tasks', {}).items():
        if k not in titles:
            continue
        score = max(0, (e.get('att') or 0) - 1) + 2 * (e.get('hints') or 0) + (4 if e.get('help') == 2 else 0) + \
            (0 if e.get('solved') else (2 if e.get('att') else 0))
        if score >= 2:
            rows.append((score, k, e))
    rows.sort(reverse=True)
    print('# Где было трудно\n')
    print('## Задачи\n')
    print('| Урок | Задача | Попыток | Подсказок | Решение открыто | Решена |\n|---|---|---|---|---|---|')
    for score, k, e in rows:
        lesson = k.rsplit('/', 1)[0]
        print(f'| {lessons[lesson]} | {titles[k]} (`{k.rsplit("/", 1)[1]}`) | {e.get("att") or 0} | {e.get("hints") or 0} | '
              f'{"да" if e.get("help") == 2 else ""} | {"да" if e.get("solved") else "нет"} |')
    fb = [(k, v) for k, v in state.get('fb', {}).items() if v.get('v', 0) < 0]
    if fb:
        print('\n## Разделы «Не очень понятно»\n')
        for k, v in fb:
            lesson, sec = k.split('#')
            print(f'- {lessons.get(lesson, lesson)} → «{v.get("h") or sec}»' + (f': «{v["c"]}»' if v.get('c') else ''))
    quiz = [k for k, v in state.get('quiz', {}).items() if not v.get('ok')]
    if quiz:
        print('\n## Неверные ответы «Предскажите вывод»\n')
        for k in quiz:
            lesson, q = k.split('#')
            print(f'- {lessons.get(lesson, lesson)} — вопрос {q}')
    for k, v in state.get('exam', {}).items():
        if v.get('done'):
            print(f'\n## Контрольная {k}: {v.get("score")}% (лучший {v.get("best")}%)')


if __name__ == '__main__':
    main()
