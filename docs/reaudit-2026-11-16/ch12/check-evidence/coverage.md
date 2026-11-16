# Охват автопроверок главы12

Все 50 авторских baseline прошли в CPython и Pyodide. 132 замороженные программы дали одинаковые пары ok/passed в обеих средах; 108 нормативных совпадений и 24 расхождения. Код и ожидания ни одной пробы не изменены после исполнения.

| Карточка | Программ | Принято | Отклонено | Расхождения expected/passed |
|---|---:|---:|---:|---|
| ch12/01-resample/anomalies | 2 | 1 | 1 |  |
| ch12/01-resample/by-hour | 3 | 1 | 2 | C108 |
| ch12/01-resample/daily | 3 | 2 | 1 | C012, C107 |
| ch12/01-resample/friday | 3 | 2 | 1 |  |
| ch12/01-resample/growth | 3 | 3 | 0 | C018 |
| ch12/01-resample/load | 2 | 2 | 0 | C008 |
| ch12/01-resample/months | 4 | 3 | 1 | C020, C109, C127 |
| ch12/01-resample/p-roll | 2 | 1 | 1 |  |
| ch12/01-resample/slice | 2 | 1 | 1 |  |
| ch12/01-resample/zeros | 3 | 1 | 2 | C110 |
| ch12/02-decompose/acf-plot | 2 | 2 | 0 | C044 |
| ch12/02-decompose/adf | 2 | 1 | 1 |  |
| ch12/02-decompose/decompose | 2 | 1 | 1 |  |
| ch12/02-decompose/diff | 2 | 2 | 0 | C034 |
| ch12/02-decompose/hour-season | 3 | 1 | 2 | C113 |
| ch12/02-decompose/multiplicative | 2 | 1 | 1 |  |
| ch12/02-decompose/p-acf | 2 | 1 | 1 |  |
| ch12/02-decompose/residual-days | 2 | 1 | 1 |  |
| ch12/02-decompose/seasonal-diff | 2 | 1 | 1 |  |
| ch12/02-decompose/toy-trend | 3 | 1 | 2 | C112 |
| ch12/03-features/calendar | 3 | 1 | 2 | C114 |
| ch12/03-features/feature-sets | 2 | 1 | 1 |  |
| ch12/03-features/leak-check | 2 | 1 | 1 |  |
| ch12/03-features/leak-test | 4 | 2 | 2 | C120 |
| ch12/03-features/make-features | 5 | 5 | 0 | C054, C123, C124, C125 |
| ch12/03-features/onehot-hours | 2 | 1 | 1 |  |
| ch12/03-features/p-lags | 2 | 1 | 1 |  |
| ch12/03-features/promo-feature | 2 | 1 | 1 |  |
| ch12/03b-time-split/check-order | 3 | 3 | 0 | C066 |
| ch12/03b-time-split/folds | 2 | 1 | 1 |  |
| ch12/03b-time-split/month-folds | 3 | 1 | 2 | C122 |
| ch12/03b-time-split/noshuffle | 2 | 1 | 1 |  |
| ch12/03b-time-split/same-period | 2 | 1 | 1 |  |
| ch12/03b-time-split/tscv | 2 | 1 | 1 |  |
| ch12/04-forecast/bias | 2 | 1 | 1 |  |
| ch12/04-forecast/by-hour-error | 3 | 2 | 1 |  |
| ch12/04-forecast/horizon-gap | 2 | 1 | 1 |  |
| ch12/04-forecast/leak-horizon | 2 | 1 | 1 |  |
| ch12/04-forecast/mean4w | 2 | 1 | 1 |  |
| ch12/04-forecast/metrics | 3 | 3 | 0 | C078 |
| ch12/04-forecast/naive | 2 | 1 | 1 |  |
| ch12/04-forecast/p-horizon | 2 | 1 | 1 |  |
| ch12/04-forecast/wape | 4 | 2 | 2 |  |
| ch12/05-project/baseline | 2 | 1 | 1 |  |
| ch12/05-project/final | 3 | 2 | 1 |  |
| ch12/05-project/grid | 3 | 1 | 2 | C121 |
| ch12/05-project/quantile | 2 | 1 | 1 |  |
| ch12/05-project/select | 2 | 1 | 1 |  |
| ch12/05-project/split | 4 | 2 | 2 | C094 |
| ch12/05-project/staffing | 9 | 3 | 6 |  |
