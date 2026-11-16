# Глава 14. Независимая предметная проверка

## Исходная редакция

Обмен ошибочных классов при сохранении общей точности и присвоение каждому наблюдению одинаковой пары времени и ячейки приняты. Дублирование оповещения в одном эпизоде уже отклоняется. Исправленная модель в исходном режиме дала вечерние полноту 1,000 и точность 0,922 для пустой ячейки на показанном дне. Для нового дня нужны фиксированные правило и нормировка, сравнение событий по реальному времени и отдельная оценка наблюдаемого простоя.

14 ноября 2026 г. выполнены 15 контрольных запусков на локальном Pyodide 314.0.7 с данными из `site/data` и текущим `site/assets/harness.py`. Первый аргумент [набора проб](../../audit-2026-11-13/ch14/expert-probes.mjs) — JSON-экспорт уроков. SHA-256 экспорта этой главы начинается с `0189f982d1f3cf50`. В журнале `true` означает, что учебная проверка приняла конкретную попытку.

```text
02-filters/pool reference max/min window axes true
02-filters/pool use min pooling false max_pool(t, 2) = [[[0.0, 2.0], [8.0, 10.0]], [[16.0, 18.0], [24.0, 26.0]]].
04-cnn/out-size explicit floor equivalent true
04-cnn/out-size incorrect same-output shape false out_size: (n + 2·pad − k) // stride + 1.
04c-detection/iou reference true
04c-detection/iou ignore box separation along x true
05-project/light empty figure with no requested brightness line true
05-project/fix reference normalization and fit true
05-project/fix swap wrong product classes while preserving aggregate quality true
05-project/hours saved correct occupancy table true
05-project/hours drop time and metadata correspondence true
05-project/alerts correct first alert per detected run true
05-project/alerts send duplicate alerts false Оповещений 25, а нужно 24. Похоже, оповещения повторяются внутри одной серии — нужно только её начало: «пусто» в t и t − 15, но не в t − 30.
05-project/restock equivalent mean interval occupancy true
05-project/restock treat readings as hours false saved_hours = 60.
```

[Предыдущая рецензия](../../audit-2026-11-13/ch14/review.md) и [диапазон правок в плане](../../course-improvement-evidence.md#ch14) относятся к предшествующему аудиту. Для приёмки редакции нужны новые попытки студента и повторный прогон по изменённым урокам.

## Приёмка обновлённой редакции

На экспорте всех глав SHA-256 `e26715108330b7bf` повторены 15 исторических вариантов. Для этой главы независимо запущен [нативный набор](../../../tools/checks/ch14_acceptance.py); зарегистрировано 6 строк успешных проб. [Исходные замечания](../../audit-2026-11-13/ch14/review.md) · [План и свидетельства](../../course-improvement-evidence.md#ch14) · [Оценка методиста](methodist.md).

| Исторический ID | Вердикт по новой редакции |
|---|---|
| S14-01 | Исправлено. Нативная проба BatchNorm проверила параметры и buffers раздельно: eval тела сохраняет оба, голова обновляется; после общего train buffers меняются. |
| S14-02 | Исправлено и проверено настоящими весами ImageNet. На одинаковых 500 контрольных и 204 вечерних кадрах следующего дня при 200 фото на класс случайные фильтры дали 0,940/0,804, ResNet-18 — 0,982/0,765. Лидер зависит от освещения. Эффект будущей тысячи снимков не измерен. |
| S14-03 | Исправлено. 15 ячейко-часов — наблюдаемый простой в утреннем окне. Сценарии оцениваются за весь день при заданном потенциальном спросе; подмена суммы whole_day отклонена. |

Фактическое покрытие и степень самостоятельности приведены в [новом журнале ученика](student-retest.md).

При переносе проверены настоящие локальные веса torchvision и обе группы контрольных кадров, отдельно проверены режимы BatchNorm. В stress проверен действительный сдвиг с заполнением края 0,8: accuracy 0,810 / 0,858 / 0,866; циклическая подстановка отклонена. Штатные авторские пробы проверили координаты и независимый день. На новой нормированной модели по первому дню для правил 1/2/3 рассчитаны 1110/480/1500 ₽ в нативном sklearn; у студента в браузере для одного кадра 1230 ₽. В обеих средах минимальная стоимость у двух кадров. Ученик отдельно сдал choose-k-before-nextday и schedule-scenarios. При двух кадрах следующий день дал 18 сигналов, 2 пропущенных эпизода, 1 повтор и среднюю задержку 14,12 минуты. В последней редакции augment принят: средняя яркость левой полосы 0,7411 для wrapped и 0,8000 для cropped. Подмена cropped = wrapped.copy() отклонена. Пустой график light ещё принимается; это отдельное ограничение визуальной проверки.

| Задание и вариант | До | После |
|---|---|---|
| `02-filters/pool reference max/min window axes` | зачёт | зачёт |
| `02-filters/pool use min pooling` | отказ | отказ |
| `04-cnn/out-size explicit floor equivalent` | зачёт | зачёт |
| `04-cnn/out-size incorrect same-output shape` | отказ | отказ |
| `04c-detection/iou reference` | зачёт | зачёт |
| `04c-detection/iou ignore box separation along x` | зачёт | отказ |
| `05-project/light empty figure with no requested brightness line` | зачёт | зачёт |
| `05-project/fix reference normalization and fit` | зачёт | зачёт |
| `05-project/fix swap wrong product classes while preserving aggregate quality` | зачёт | отказ |
| `05-project/hours saved correct occupancy table` | зачёт | зачёт |
| `05-project/hours drop time and metadata correspondence` | зачёт | отказ |
| `05-project/alerts correct first alert per detected run` | зачёт | зачёт |
| `05-project/alerts send duplicate alerts` | отказ | отказ |
| `05-project/restock equivalent mean interval occupancy` | зачёт | зачёт |
| `05-project/restock treat readings as hours` | отказ | изменилась постановка/код |
