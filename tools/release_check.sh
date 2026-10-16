#!/bin/sh
# Проверка перед публикацией: запускать на закоммиченном дереве.
#   sh tools/release_check.sh            # всё
#   sh tools/release_check.sh ch05 ch08  # проверки задач только этих глав
# Падает (код ≠ 0), если:
#   - разметка уроков с ошибками;
#   - пересборка сайта или блокнотов меняет закоммиченные файлы (site/ рассинхронизирован с content/);
#   - эталон не проходит, заготовка или неверное решение из tools/negatives.json проходит, пример падает;
#   - карта переносов прогресса content/moved.json противоречит текущим задачам (проверяет build.py).
set -e
cd "$(dirname "$0")/.."
fail() { echo "✗ $1"; exit 1; }

[ -z "$(git status --porcelain -- content tools site)" ] || fail "есть незакоммиченные изменения в content/, tools/ или site/ — сначала закоммитьте"

echo "1/4 разметка";   uv run -q tools/build.py --check
echo "2/4 сборка";     uv run -q tools/build.py >/dev/null
uv run -q tools/make_notebooks.py >/dev/null
# ?v= у ассетов зависит от содержимого, поэтому любое расхождение — повод пересобрать и закоммитить
[ -z "$(git status --porcelain -- site)" ] || { git status --short -- site | head -20; fail "пересборка изменила site/ — закоммитьте результат сборки"; }

echo "3/4 задачи и примеры"
uv run -q tools/build.py --export build/tasks.json >/dev/null
CHS="$*"; [ -n "$CHS" ] || CHS="ch01 ch02 ch03 ch04 ch05 ch06 ch07 ch08 ch09 ch10 ch11 ch12 ch13 ch14 ch15"
for c in $CHS; do
  printf '%s: ' "$c"
  if out=$(node tools/verify.mjs build/tasks.json "$c/" 2>&1); then ok=1; else ok=0; fi
  echo "$out" | grep -E '^✗|проверено'
  [ $ok = 1 ] || fail "verify $c"
done

echo "4/4 основной путь → углубления (справочно)"
uv run -q tools/core_refs.py | tail -1
echo "✓ можно публиковать"
