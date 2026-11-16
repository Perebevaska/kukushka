# Покрытие 61 task до и после редакции

`N/P` — CPython/Pyodide; `T` зачёт, `F` отказ. Автор/ALT ожидают T/T, ошибочная программа ожидает F/F. У Parsons изменённый код — harness-only. Старые программы и ожидания не менялись.

| Task | Публичная цель/метод сверены | Author N/P before → after | ALT N/P before → after | Ошибка N/P before → after |
|---|---|---|---|---|
| ch14/01-pixels/load | Да | T/T → T/T | T/T → T/T | T/T → F/F |
| ch14/01-pixels/p-show H | Да | F/T → T/T | T/T → T/T | T/T → T/T |
| ch14/01-pixels/crop | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01-pixels/overflow | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01-pixels/dark-rule | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01-pixels/centroid | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01-pixels/shift | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01-pixels/gray | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01-pixels/cells | Да | T/T → T/T | T/T → T/T | T/T → F/F |
| ch14/01-pixels/where | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01b-files/memory | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01b-files/formats | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01b-files/small | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01b-files/batches | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01b-files/quality | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/01b-files/mask | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/conv | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/p-size H | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/edges | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/pool | Да | T/T → T/T | T/T → T/T | T/T → F/F |
| ch14/02-filters/denoise | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/features | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/global | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/modes | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/orient | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/02-filters/edge-rule | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/flat | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/p-knn H | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/confusion | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/importance | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/knn-k | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/augment | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/stress | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/bright-aug | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/03-classic/light | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/params | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/p-shapes H | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/layer | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/softmax | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/random | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/rand-light | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/out-size | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/receptive | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04-cnn/pool-size | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04b-transfer/folders | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04b-transfer/head | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04b-transfer/trainable | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04b-transfer/frozen-bug | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04b-transfer/few-shot | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04c-detection/iou | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04c-detection/match | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04c-detection/iou-hand | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04c-detection/box-format | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04c-detection/mask-iou | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/04c-detection/nms | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/05-project/day | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/05-project/light | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/05-project/fix | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/05-project/hours | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/05-project/alerts | Да | T/T → T/T | T/T → T/T | F/F → F/F |
| ch14/05-project/restock | Да | T/T → T/T | T/T → T/T | F/F → F/F |
