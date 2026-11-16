# After: охват автопроверок главы12

Actual after-tasks получены из реального build-export revised.json; 50×4 поля семантически совпали с proposal. 18 текстовых отличий — только концевые переводы строк.

| Карточка | Программ исходного132 | Before→after неверные зачёты | Before→after отказы позитивам | Намеренные миграции старых позитивов |
|---|---:|---|---|---|
| ch12/01-resample/anomalies | 2 |  |  |  |
| ch12/01-resample/by-hour | 3 |  | C108 |  |
| ch12/01-resample/daily | 3 | C012 | C107 |  |
| ch12/01-resample/friday | 3 |  |  |  |
| ch12/01-resample/growth | 3 | C018 |  |  |
| ch12/01-resample/load | 2 | C008 |  |  |
| ch12/01-resample/months | 4 | C020, C127 | C109 |  |
| ch12/01-resample/p-roll | 2 |  |  |  |
| ch12/01-resample/slice | 2 |  |  |  |
| ch12/01-resample/zeros | 3 |  | C110 |  |
| ch12/02-decompose/acf-plot | 2 | C044 |  |  |
| ch12/02-decompose/adf | 2 |  |  |  |
| ch12/02-decompose/decompose | 2 |  |  |  |
| ch12/02-decompose/diff | 2 | C034 |  |  |
| ch12/02-decompose/hour-season | 3 |  | C113 |  |
| ch12/02-decompose/multiplicative | 2 |  |  |  |
| ch12/02-decompose/p-acf | 2 |  |  |  |
| ch12/02-decompose/residual-days | 2 |  |  |  |
| ch12/02-decompose/seasonal-diff | 2 |  |  |  |
| ch12/02-decompose/toy-trend | 3 |  | C112 |  |
| ch12/03-features/calendar | 3 |  | C114 |  |
| ch12/03-features/feature-sets | 2 |  |  |  |
| ch12/03-features/leak-check | 2 |  |  |  |
| ch12/03-features/leak-test | 4 |  |  | C120 |
| ch12/03-features/make-features | 5 | C054, C123, C124, C125 |  |  |
| ch12/03-features/onehot-hours | 2 |  |  |  |
| ch12/03-features/p-lags | 2 |  |  |  |
| ch12/03-features/promo-feature | 2 |  |  | C061 |
| ch12/03b-time-split/check-order | 3 | C066 |  |  |
| ch12/03b-time-split/folds | 2 |  |  |  |
| ch12/03b-time-split/month-folds | 3 |  |  | C122 |
| ch12/03b-time-split/noshuffle | 2 |  |  |  |
| ch12/03b-time-split/same-period | 2 |  |  |  |
| ch12/03b-time-split/tscv | 2 |  |  |  |
| ch12/04-forecast/bias | 2 |  |  |  |
| ch12/04-forecast/by-hour-error | 3 |  |  |  |
| ch12/04-forecast/horizon-gap | 2 |  |  |  |
| ch12/04-forecast/leak-horizon | 2 |  |  |  |
| ch12/04-forecast/mean4w | 2 |  |  |  |
| ch12/04-forecast/metrics | 3 | C078 |  |  |
| ch12/04-forecast/naive | 2 |  |  |  |
| ch12/04-forecast/p-horizon | 2 |  |  |  |
| ch12/04-forecast/wape | 4 |  |  |  |
| ch12/05-project/baseline | 2 |  |  | C095 |
| ch12/05-project/final | 3 |  |  |  |
| ch12/05-project/grid | 3 |  |  | C099, C121 |
| ch12/05-project/quantile | 2 |  |  |  |
| ch12/05-project/select | 2 |  |  | C097 |
| ch12/05-project/split | 4 | C094 |  |  |
| ch12/05-project/staffing | 9 |  |  |  |
