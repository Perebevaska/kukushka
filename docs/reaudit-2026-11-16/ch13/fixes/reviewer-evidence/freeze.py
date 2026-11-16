"""Materialise review submissions using only original public task text and baseline export."""
import hashlib
import json
import sys
from pathlib import Path

out = Path(__file__).resolve().parent
data = Path(sys.argv[1]).read_bytes()
assert hashlib.sha256(data).hexdigest() == '317ea31da6ee8fcb87c34ab2e88527228a985c6c768869d6dcd6091213fa6280'
tasks = {t['id']: t for t in json.loads(data) if t['lesson'].startswith('ch13/') and t['kind'] == 'task'}
cases = []


def add(task, name, expected, reason, *, after='', replace=None, before=''):
    code = tasks[task]['solution']
    if replace:
        old, new = replace
        assert old in code
        code = code.replace(old, new)
    cases.append(dict(id=name, task=task, expected=expected, reason=reason,
                      code=before + '\n' + code + '\n' + after))


add('parse-llm', 'R01', True, 'Произвольные строковые ID сохраняют порядок ответов.', after="parsed.index = ['ответ-' + str(91-i) for i in range(len(parsed))]")
add('parse-llm', 'R02', False, 'Первые два валидных ответа поменялись местами при прежнем числе ошибок.', after='parsed = parsed.iloc[[1,0,2,3,4,5,6,7]]')
add('parse-llm', 'R03', False, 'Функция возвращает годный результат лишь для восьми знакомых строк.', after='known = {a: parse(a) for a in raw}\ndef parse(answer):\n    return known.get(answer, dict(sentiment=None,topic=None,ok=False))')
add('clean', 'R04', True, 'Нормализатор обрабатывает новое слово с Ё, цифрами и переносами.', replace=('return re.sub(r" +", " ", text).strip()', 'return " ".join(text.split())'))
add('clean', 'R05', False, 'Правильная показанная строка, но функция возвращает исходный ответ для другого текста.', after='def normalize(text):\n    return clean')
add('topics', 'R06', True, 'Переставлены строки и столбцы с их метками. Каждая ячейка осталась у тех же тем.', after='cm = cm.iloc[::-1, [1,3,5,0,2,4]]')
add('topics', 'R07', False, 'Те же числа, но переименованы только столбцы. Ошибки приписаны другим темам.', after='cm.columns = list(cm.columns[1:]) + [cm.columns[0]]')
add('top-words', 'R08', True, 'Сортировка индекса Series сохраняет пару слово–коэффициент.', after='weights = weights.sort_index(ascending=False)')
add('top-words', 'R09', False, 'Два внутренних коэффициента обменялись словами, списки из пяти и «не» сохранены.', after='ordered = weights.sort_values().drop("не").index\na, b = ordered[15], ordered[-16]\nweights.loc[[a,b]] = weights.loc[[b,a]].to_numpy()')
add('lsa', 'R10', True, 'Смена знака одной общей координаты сохраняет косинусы для каждого ID.', after='Zn[:, 17] *= -1')
add('lsa', 'R11', False, 'Обратный порядок строк нарушает связь review_id с эмбеддингом. Длины единичные и записанные соседи прежние.', after='Zn = Zn[::-1].copy()')
add('weekly', 'R12', True, 'Ту же динамику выбранной точки показывает отдельная линия средствами matplotlib.', replace=('ax = weekly.plot', 'ax = weekly.plot'), after='plt.close("all")\nfig, ax = plt.subplots()\nax.plot(weekly.index, weekly[focus_shop], marker="o", label=focus_shop)')
add('weekly', 'R13', False, 'Меняется одна показанная ордината выбранной точки, числовая таблица сохранена.', after='plt.close("all")\nfig, ax=plt.subplots()\ncurve=weekly[focus_shop].copy()\ncurve.loc[jump_week] = 0.0\nax.plot(curve.index,curve,label=focus_shop)')
add('recall95', 'R14', True, 'Перестановка наблюдений итогового теста целиком сохраняет измерение при пороге из validation.', replace=('p_test=model.predict_proba(X_test)[:,1]', 'X_test, y_test = X_test.iloc[::-1], y_test.iloc[::-1]\np_test=model.predict_proba(X_test)[:,1]'))
add('recall95', 'R15', False, 'В финальном расчёте вместо 600 итоговых строк повторно использованы 600 валидационных строк.', replace=('p_test=model.predict_proba(X_test)[:,1]', 'X_test, y_test = X_validation.copy(), y_validation.copy()\np_test=model.predict_proba(X_test)[:,1]'))
pairs = """pairs = pd.DataFrame({'llm': ok_llm.to_numpy(), 'model': ok_model.to_numpy()}, index=check['review_id'])
pairs = pairs.iloc[::-1].copy()
{mutation}
llm_only = int((pairs.llm & ~pairs.model).sum())
model_only = int((pairs.model & ~pairs.llm).sum())
delta = pairs.llm.astype(int) - pairs.model.astype(int)
lo = delta.mean() - 1.96 * delta.std(ddof=1) / len(delta)**.5
paired_lower = round(float(lo), 3)
within_margin = bool(lo > -.02)"""
add('llm-same', 'R16', True, 'Переворот целых пар по review_id оставляет разногласия и интервал неизменными.', after=pairs.replace('{mutation}', ''))
add('llm-same', 'R17', False, 'Циклический сдвиг результатов только одной системы сохраняет accuracy, разрушает парность.', after=pairs.replace('{mutation}', 'pairs["model"] = __import__("numpy").roll(pairs.model.to_numpy(), 17)'))
add('why', 'R18', True, 'Строки тем переставлены вместе с метками, цитаты и исходные ID сохранены.', after='kzn, others = kzn.sort_index(ascending=False), others.sort_index(ascending=False)')
add('why', 'R19', False, 'Тексты оставлены на местах, ID двух цитат переставлены.', after='quote_ids[0], quote_ids[1] = quote_ids[1], quote_ids[0]')
add('adjust', 'R20', True, 'Обратный порядок каждой входной таблицы сохраняет объединение по ключу, числители и знаменатели.', replace=('labeled = n.merge(gold', 'labeled = n.iloc[::-1].merge(gold.iloc[::-1]'), after='audit = audit.iloc[::-1]')
add('adjust', 'R21', False, 'После сдвига только ключей разметки метки принадлежат другим отзывам.', replace=('labeled = n.merge', 'gold["review_id"] = __import__("numpy").roll(gold.review_id.to_numpy(), 11)\nlabeled = n.merge'))
add('adjust', 'R22', False, 'Для всех последующих расчётов 3 октября ошибочно включено в «после».', replace=('obs = n[', "n['period'] = __import__('numpy').where(n.date >= '2026-10-01', 'после','до')\nobs = n["))
add('adjust', 'R23', False, 'Один отзыв выбранной точки отсутствует в обеих производных таблицах.', replace=('obs = n[', 'n = n.drop(n.index[n.shop_id == "KZN-2"][0]).copy()\nobs = n['))
add('adjust', 'R24', False, 'В каждом периоде доля модели выдана за долю синтетических жалоб.', after='audit["manual"] = audit["observed"]')
add('adjust', 'R25', False, 'Пропущен период до границы.', after='audit = audit.loc[["после"]]')
dest = out / 'cases-before.json'
dest.write_text(json.dumps(cases, ensure_ascii=False, indent=2)+'\n')
with (out/'expectations-before.md').open('w') as f:
    f.write('# Независимые ожидания до чтения новых отчётов\n\nИсходный экспорт 563d774, 25 программ. Каждая программа зафиксирована целиком. В качестве контролируемой основы использованы исходные авторские решения. Преобразования и ожидания ниже выбраны до их исполнения и чтения других проб. Новый человеческий эталон для реального потока этими программами не создаётся.\n\n| ID | Задание | Ожидание | Основание |\n|---|---|---|---|\n')
    for c in cases:
        f.write(f"| {c['id']} | {c['task']} | {'зачёт' if c['expected'] else 'отказ'} | {c['reason']} |\n")
print(hashlib.sha256(dest.read_bytes()).hexdigest(), len(cases))
