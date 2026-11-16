# Глава 13. Независимая предметная проверка

## Исходная редакция

Все отзывы, отнесённые к одной точке, и даты и тексты, развёрнутые независимо от ID, приняты. Выдуманные с нуля пять цитат уже отклоняются. Нулевые TF-IDF признаки проверки и одинаковая прибавка к обеим парным частотам приняты. Для приёмки проверить ключ review_id, пары предсказаний на одном тексте и принадлежность выбранной цитаты месту и неделе.

14 ноября 2026 г. выполнены 21 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch13/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `f6891815fa282e8d`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
01-text-prep/tokenize reference true
01-text-prep/tokenize drop ё false t = ['кофе', 'отличный', 'жики']. Не забудьте букву ё и нижний регистр.
02-tfidf/idf-by-hand equivalent log ratio true
02-tfidf/idf-by-hand omit smoothing false idf_manual = 4.3059.
02-tfidf/train-only replace sparse test features with zeros true
03b-labels/kappa replace chance-corrected score with agreement false kappa на примере из урока = 0.8, а нужно 0.375. Проверьте p_e: доли считаются отдельно для x и для y.
04b-transformers/masked-pool broadcast mask true
04b-transformers/masked-pool einsum masking true
04b-transformers/masked-pool include pads in denominator false mean_pool на примере из урока = [[1.0, 1.0]], а нужно [[2.0, 2.0]]. Форма результата — (тексты, признаки).
04c-llm/parse-llm reference parser true
04c-llm/parse-llm ignore future inputs after table produced true
04c-llm/llm-same paired counts true
04c-llm/llm-same increment both paired counts true
05-project/score store original shops true
05-project/score put every review at the same shop true
05-project/score attach dates and original text in reverse true
05-project/score reverse class probabilities false p_neg — вторая колонка predict_proba.
05-project/why reference quotes true
05-project/why five manufactured quotes false quotes: пять текстов с наибольшей p_neg, по убыванию.
05-project/adjust reference correction true
05-project/adjust incorrect denominator sign false adj = {'до': np.float64(0.351), 'после': np.float64(0.592)}, а нужно {'до': np.float64(0.378), 'после': np.float64(0.637)}.
```

[Предыдущая рецензия](../../audit-2026-11-13/ch13/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch13) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 21 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch13_acceptance.py); зарегистрировано 6 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch13/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch13) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S13-01 | Исправлено. Порог recall95 выбирается до финального теста; в итоговой выборке сообщается полученная полнота, включая возможное недостижение 95%. |
| S13-02 | Исправлено для учебной выборки. Оценки двух периодов теперь сверяют с синтетической контрольной разметкой по смыслу жалобы. Перенос на реальные жалобы требует независимой разметки; генератор её не заменяет. |
| S13-03 | Исправлено и заново измерено. models сравнивает повторы, новые фразы и общее разбиение по текстам. У 519 новых текстов темы accuracy 0,792 и macro-F1 0,761. На 81 повторе оба показателя 1,000. В групповом тесте 592 ID и полное отсутствие пересечения формулировок; accuracy тональности 0,953, темы 0,816 и macro-F1 темы 0,794. Подмена F1 или ID отвергнута, переставленные строки таблицы приняты. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

weekly стоит перед why, стабильные ID сохранены. Ученик отправил собственную попытку text-quality-groups и получил «Верно!», отдельно от weekly, why и audit. Перемешанная таблица с корректными ключами принята, чужая точка, неделю и цитату проверка отклоняет. После независимой правки приняты новый валидный JSON и пустой отказ; недопустима прибавка к двум парным счётчикам. В повторной попытке ученик назвал audit «ручной разметкой». После перечтения окончательного условия студент исправил собственную интерпретацию label_source и имени manual. Обе реплики учебного материала исправлены. Реального платного API и человеческой разметки жалоб в этой проверке не было. У парного сравнения есть заданная до оценки граница −0,02.

| Задание и вариант | До | После |
|---|---|---|
| `01-text-prep/tokenize reference` | зачёт | зачёт |
| `01-text-prep/tokenize drop ё` | отказ | отказ |
| `02-tfidf/idf-by-hand equivalent log ratio` | зачёт | зачёт |
| `02-tfidf/idf-by-hand omit smoothing` | отказ | отказ |
| `02-tfidf/train-only replace sparse test features with zeros` | зачёт | отказ |
| `03b-labels/kappa replace chance-corrected score with agreement` | отказ | отказ |
| `04b-transformers/masked-pool broadcast mask` | зачёт | зачёт |
| `04b-transformers/masked-pool einsum masking` | зачёт | зачёт |
| `04b-transformers/masked-pool include pads in denominator` | отказ | отказ |
| `04c-llm/parse-llm reference parser` | зачёт | зачёт |
| `04c-llm/parse-llm ignore future inputs after table produced` | зачёт | отказ |
| `04c-llm/llm-same paired counts` | зачёт | зачёт |
| `04c-llm/llm-same increment both paired counts` | зачёт | отказ |
| `05-project/score store original shops` | зачёт | зачёт |
| `05-project/score put every review at the same shop` | зачёт | отказ |
| `05-project/score attach dates and original text in reverse` | зачёт | отказ |
| `05-project/score reverse class probabilities` | отказ | отказ |
| `05-project/why reference quotes` | зачёт | зачёт |
| `05-project/why five manufactured quotes` | отказ | отказ |
| `05-project/adjust reference correction` | зачёт | зачёт |
| `05-project/adjust incorrect denominator sign` | отказ | отказ |

При массовом повторе сохранённой программы прежнего ученика обнаружен отдельный ложный отказ в parse-llm. Вариант с кортежем строил правильную таблицу, но проверка нового ответа ожидала словарь. После уточнения контракта этот же код принят в Pyodide при повторе без изменений. [Журнал повторов](../student-practice-replay.jsonl)
