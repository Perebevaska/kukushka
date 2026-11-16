# Покрытие 61 карточки: условие и три исполнимых решения

Четыре колонки результата: публичная цель/метод; author; другой корректный расчёт; правдоподобная ошибка. В ячейках native/Pyodide: `T` зачёт, `F` отказ, `—` ещё не исполнено. Parsons: мутации произвольного кода обозначены `H`, это harness-only, если такого кода нет среди видимых строк. Четыре исходных поля каждой карточки отдельно зафиксированы в source61x4-before.json.

| ID | Цель/метод прочитаны | Author N/P | Другой корректный N/P | Ошибка N/P (ожидание F/F) |
|---|---|---|---|---|
| ch14/01-pixels/load | Да; четыре поля и hints | T/T | T/T | T/T |
| ch14/01-pixels/p-show H | Да; четыре поля и hints | F/T | T/T | T/T |
| ch14/01-pixels/crop | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01-pixels/overflow | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01-pixels/dark-rule | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01-pixels/centroid | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01-pixels/shift | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01-pixels/gray | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01-pixels/cells | Да; четыре поля и hints | T/T | T/T | T/T |
| ch14/01-pixels/where | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01b-files/memory | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01b-files/formats | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01b-files/small | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01b-files/batches | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01b-files/quality | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/01b-files/mask | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/conv | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/p-size H | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/edges | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/pool | Да; четыре поля и hints | T/T | T/T | T/T |
| ch14/02-filters/denoise | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/features | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/global | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/modes | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/orient | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/02-filters/edge-rule | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/flat | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/p-knn H | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/confusion | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/importance | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/knn-k | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/augment | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/stress | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/bright-aug | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/03-classic/light | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/params | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/p-shapes H | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/layer | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/softmax | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/random | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/rand-light | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/out-size | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/receptive | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04-cnn/pool-size | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04b-transfer/folders | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04b-transfer/head | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04b-transfer/trainable | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04b-transfer/frozen-bug | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04b-transfer/few-shot | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04c-detection/iou | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04c-detection/match | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04c-detection/iou-hand | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04c-detection/box-format | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04c-detection/mask-iou | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/04c-detection/nms | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/05-project/day | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/05-project/light | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/05-project/fix | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/05-project/hours | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/05-project/alerts | Да; четыре поля и hints | T/T | T/T | F/F |
| ch14/05-project/restock | Да; четыре поля и hints | T/T | T/T | F/F |
