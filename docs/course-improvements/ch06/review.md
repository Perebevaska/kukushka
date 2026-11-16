# Глава 6. Независимая предметная проверка

## Исходная редакция

После подстановки будущей метки в days_since_last или перемешивания y_train сдача prepare принята. Разворот только фактической величины на диаграмме также проходит. Переобученная на тесте модель получает зачёт с ранее рассчитанными числами. После правки перепроверить строки X/y по ID, вызывать сданную модель на тех же контрольных ID и сравнить точки в соответствующих парах.

14 ноября 2026 г. выполнены 19 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch06/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `99759023452ad49e`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
04-categorical/new-orders correct new weather true
04-categorical/new-orders new weather assigned snow false Столбцы верные, но значения не те: флаги новых заказов должны быть 0/1, недостающие — нулями.
04-categorical/shop-rate training self-target included true
04-categorical/shop-rate leave-one-out training encoding false В X_train shop_rate не совпал с долями по обучающей части.
07-regression/fact-pred matched rows true
07-regression/fact-pred reverse both, valid order true
07-regression/fact-pred reverse only observed times true
08b-groups-speed/group-split group holdout true
08b-groups-speed/group-split ordinary split row count false n_test_rows = 583 — ровно четверть строк. Так делит обычный train_test_split; GroupShuffleSplit берёт четверть гостей, и строк выходит другое число.
09-project/prepare correct split true
09-project/prepare equivalent alphabetic feature order false Столбцы X: ['app', 'avg_check', 'city_Казань', 'city_Пермь', 'city_Тюмень', 'city_Уфа', 'complaints', 'days_since_last', 'delivery_share', 'fav_category_еда', 'fav_category_кофе', 'fav_category_не кофе', 'promo_used', 'tenure_months', 'visits_90d'], а ожидались ['tenure_months', 'app', 'visits_90d', 'days_since_last', 'avg_check', 'delivery_share', 'promo_used', 'complaints', 'city_Казань', 'city_Пермь', 'city_Тюмень', 'city_Уфа', 'fav_category_еда', 'fav_category_кофе', 'fav_category_не кофе']. get_dummies от g без трёх столбцов, dtype=int.
09-project/prepare target smuggled as days_since_last true
09-project/prepare train labels shuffled in place true
09-project/final train-only reference true
09-project/final refit model on test after calculating scores true
09-project/top correct ranking true
09-project/top equivalent stable ranking true
09-project/top overwritten top contains lowest risk true
09-project/top incorrect IDs false top_ids — guest_id 60 гостей с наибольшим риском, в порядке убывания риска: g.loc[top.index, "guest_id"].
```

[Предыдущая рецензия](../../audit-2026-11-13/ch06/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch06) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 19 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch06_acceptance.py); зарегистрировано 8 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch06/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch06) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S06-01 | Исправлено. Глубину теперь выбирают на валидации; эталон и независимая альтернатива приняты, ученик выполнил depth. |
| S06-02 | Исправлено в исходной карточке. Импорт NumPy сопровождает использование сетки порогов; шаг 0,05 начинается с 0,10. |
| S06-03 | Исправлено. Учебная демонстрация утечки и финальная оценка разделены по ID. Рабочая выдача строится на свежих признаках без целевой метки; студент сформировал настоящий список. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

Подмена признаков, метки и переданной модели отклонены. При повторной рецензии устранены зачёт неверных пар scatter и замена Series top самым низким риском. Упорядочивание равных рисков проверено отдельным правильным nlargest после сортировки ID. В shop-rate эталон по-прежнему включает собственную метку учебной строки и не принимает leave-one-out как эквивалент данного условия; безопасная схема OOF разбирается отдельно.

| Задание и вариант | До | После |
|---|---|---|
| `04-categorical/new-orders correct new weather` | зачёт | зачёт |
| `04-categorical/new-orders new weather assigned snow` | отказ | отказ |
| `04-categorical/shop-rate training self-target included` | зачёт | зачёт |
| `04-categorical/shop-rate leave-one-out training encoding` | отказ | отказ |
| `07-regression/fact-pred matched rows` | зачёт | зачёт |
| `07-regression/fact-pred reverse both, valid order` | зачёт | зачёт |
| `07-regression/fact-pred reverse only observed times` | зачёт | отказ |
| `08b-groups-speed/group-split group holdout` | зачёт | зачёт |
| `08b-groups-speed/group-split ordinary split row count` | отказ | отказ |
| `09-project/prepare correct split` | зачёт | зачёт |
| `09-project/prepare equivalent alphabetic feature order` | отказ | зачёт |
| `09-project/prepare target smuggled as days_since_last` | зачёт | отказ |
| `09-project/prepare train labels shuffled in place` | зачёт | отказ |
| `09-project/final train-only reference` | зачёт | зачёт |
| `09-project/final refit model on test after calculating scores` | зачёт | отказ |
| `09-project/top correct ranking` | зачёт | зачёт |
| `09-project/top equivalent stable ranking` | зачёт | изменилась постановка/код |
| `09-project/top overwritten top contains lowest risk` | зачёт | отказ |
| `09-project/top incorrect IDs` | отказ | отказ |
