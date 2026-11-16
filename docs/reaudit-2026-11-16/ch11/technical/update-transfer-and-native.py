"""Clarify the complete handoff and native notebook prose without changing cells."""
from pathlib import Path
import json
import hashlib

D = Path(__file__).resolve().parents[1]
ROOT = D.parents[2]
p = ROOT / 'content/ch11/05-project.md'
s = p.read_text()
anchor = 'Пусть коллега проверит результат без повторного обучения.'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '\n\nЕсли очередь рассчитана для всей партии, передайте входные пиксели этой партии и связь позиции с идентификатором. Укажите порядок 64 признаков, диапазон яркости и предобработку. Несколько контрольных примеров помогают сверить загрузку, но не заменяют полный запрос, по которому коллега заново рассчитает все вероятности и очередь.', 1)
p.write_text(s)
p = ROOT / 'content/ch11/03-mlp.md'
s = p.read_text().replace('Для картинок и текстов они вне конкуренции.', 'Для картинок и текстов сети — важный кандидат; выбор подтверждают сравнением на подходящих данных.')
p.write_text(s)
p = ROOT / 'content/figures/nn-tabular-vs-raw.svg'
s = p.read_text().replace('>здесь сети<', '>сети — важный<').replace('>вне конкуренции<', '>кандидат<')
p.write_text(s)

p = ROOT / 'site/notebooks/extra/ch11-pytorch-tabular.ipynb'
nb = json.loads(p.read_text())
digest = lambda c: hashlib.sha256(''.join(c['source']).encode()).hexdigest()
before = {str(i): digest(c) for i, c in enumerate(nb['cells']) if c['cell_type'] == 'code'}
replacements = {
    0: [
        ('В браузере PyTorch не запускается, поэтому полный цикл — здесь, на своём компьютере:', 'В поставляемой среде курса Pyodide нет PyTorch, поэтому полный цикл запускается здесь, в локальном Python:'),
        ('Числа в текстовых выводах получены на процессоре. На другом компьютере или другой версии PyTorch MAE может отличаться в сотых, а время обучения — в разы: сравнивайте время моделей между собой на своей машине, а не с нашими цифрами.', 'Сохранённые выводы показывают один прежний запуск. Запишите версии библиотек и устройство при своём повторении. Метрики и длительность могут измениться; сравнивайте модели в одной среде и на одинаковых выборках.')],
    8: [('Все результаты — и ориентиры, и сети — пишем в один журнал `results` функцией `log_result`: модель, MAE на валидации и тесте, время обучения и прогноза. Время прогноза меряем лучшим из пяти запусков — первый запуск часто медленнее из-за «прогрева».', 'В журнале подбора сравниваем MAE на валидации. После фиксации лучшей сети отдельно измеряем её качество на тесте и сравниваем с ориентирами. Код сохраняет границы измерений: обучение и полный путь от исходных признаков до прогноза в минутах. Время прогноза берём лучшим из пяти запусков; расчёт метрики выполняется после секундомера.')],
    18: [('У каждого эксперимента один и тот же `torch.manual_seed`, поэтому различия — от настроек, а не от удачи стартовых весов.', 'У каждого эксперимента один и тот же `torch.manual_seed`. Он помогает повторить опыт, но при разной архитектуре не создаёт одинаковые начальные веса и не измеряет разброс между случайными инициализациями.')],
    25: [
        ('Разница около 0.6 минуты на каждой доставке — в пользу бустинга.', 'Средняя абсолютная ошибка на этой тестовой выборке ниже примерно на 0.6 минуты у бустинга. Это разность средних ошибок, а не улучшение каждой доставки.'),
        ('Структура «класс сети → smoke-test → `train_loop` с ранней остановкой → журнал в DataFrame → сравнение с ориентирами» переносится на любую задачу. Сети выигрывают там, где признаки нужно строить из «сырых» данных — фото, текст, звук (главы 13–14).', 'Структуру «класс сети → smoke-test → train_loop с ранней остановкой → журнал → сравнение с ориентирами» можно адаптировать к другой задаче, выбрав её выход и потерю. Для фото, текста и звука сети — важный кандидат; конкретный выбор также требует сравнения (главы 13–14).')]
}
for i, pairs in replacements.items():
    cell = nb['cells'][i]
    assert cell['cell_type'] == 'markdown'
    text = ''.join(cell['source'])
    for old, new in pairs:
        assert text.count(old) == 1, (i, old)
        text = text.replace(old, new)
    cell['source'] = text.splitlines(keepends=True) if isinstance(cell['source'], list) else text
after = {str(i): digest(c) for i, c in enumerate(nb['cells']) if c['cell_type'] == 'code'}
assert before == after
p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n')
(D / 'technical/native-prose-parity.json').write_text(json.dumps({'code_cells_unchanged': True, 'code_sha256': after, 'changed_markdown_cells': sorted(replacements)}, indent=2) + '\n')
print('Clarified the full request, model comparison, and four native prose cells; code unchanged.')
