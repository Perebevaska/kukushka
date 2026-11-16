# План второй приёмки главы 11

1. Сохранить вторую входную копию и проверить MANIFEST.sha256. Первые 19 SHA не менять.
2. После ROOTCPUFREE: штатные native predict.py и digits predict.py без fit; для replay.py использовать отдельную копию в second-outputs, поскольку он записывает результаты рядом с собой.
3. Загрузить сохранённые объекты независимо; запретить fit, partial_fit и optimizer.step. Native: 16 минут, metadata/scaler/state/eval/CPU/float32/1 поток; сверка по SHA признаков, одиночный запрос, перестановка строк и столбцов, поднабор.
4. Digits: по request_ids.csv и пиксельным SHA проверить 450 clean и 450 blur входов, normalization/order/blur. Получить все вероятности, классы и confidence; до чтения truth сохранить неизменённое правило capacity=37, confidence ascending then position ascending и обе очереди.
5. Затем прочесть evaluation.csv: сверить каждый position/original_index, prediction/confidence/review и пересчитать accuracy, ошибки в очереди и вне очереди. Clean использует те же ключи и truth; все строки сравнить с переданными proba/replayed артефактами. Сохранить построчную проверку.
6. Применить single/shuffle/subset и новую sigma=1.1 партию к чистым пикселям. Проверить CLI против независимого inference без подбора модели; качество нового запроса не заявлять без отдельного протокола меток.
7. Зафиксировать команды/stdout/stderr, verification2.json, неизменность обеих копий, источников и первых 19 SHA. При сбое описать первый отсутствующий шаг или расхождение без исправления пакета.

Внешние данные, восстановление через load_digits и обучение не нужны: оба полных массива уже переданы.
