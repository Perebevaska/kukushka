# Q1–Q4 по фактическим отправкам

Q1–Q3 ниже сохранены в input до helper; Q4 записан из полного сохранённого feedback. Это повтор с использованием своих прежних решений, не первое обучение.

## 01-neuron/collapse — 01-neuron-collapse.input.jsonl

Q1 показать схлопывание линейных слоёв. Q2 формула ассоциативности и numpy из карточки. Q3 W формы (3,2), same=True, with_relu_same=False.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 02-backprop/backprop-check — 02-backprop-backprop-check.input.jsonl

Q1 проверить скрытый градиент. Q2 формулы outer, маска ReLU и копии W1 для центральной разности. Q3 значения совпадут до 6 знаков, относительная ошибка будет много меньше 1e-4.

Q4: Да, так и есть. Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 02-backprop/grad-check — 02-backprop-grad-check.input.jsonl

Q1 проверить p-y. Q2 центральная разность L(z) при eps=1e-5 из теории. Q3 analytic и numeric около -0.40131 и совпадут до 5 знаков.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/alpha-sweep — 03-mlp-alpha-sweep.input.jsonl

Q1 решить alpha-sweep. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 четыре alpha, res с train/validation, лучший по округлённой validation; 600 final не участвовали.

Q4: Верно! Следующая задача → Вердикт True. Публичный вывод: ["/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (500) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (500) reached and the optimization hasn't converged yet.\n  warnings.warn("]. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/arch-grid — 03-mlp-arch-grid.input.jsonl

Q1 решить arch-grid. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 CV=3 внутри pipeline, четыре кандидата, test_auc и hgb_auc на общих600; не делаю общего вывода обо всех таблицах.

Q4: Да, так и есть. Вердикт True. Публичный вывод: ["/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn(\n/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (300) reached and the optimization hasn't converged yet.\n  warnings.warn("]. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/depth — 03-mlp-depth.input.jsonl

Q1 решить depth. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 три архитектуры на1350/450, params растёт с шириной; выбор по450validation.

Q4: Верно! Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/epoch-gap — 03-mlp-epoch-gap.input.jsonl

Q1 решить epoch-gap. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 два списка длины150 без округления; лучший индекс+1 по validation. Формы1350/450 проверяю явно.

Q4: Да, так и есть. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/loss-curve — 03-mlp-loss-curve.input.jsonl

Q1 решить loss-curve. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 curve из200 эпох train; first>last, halved_at от1; графикtrain не заменяетvalidation.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ["/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (200) reached and the optimization hasn't converged yet.\n  warnings.warn("]. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/regression-net — 03-mlp-regression-net.input.jsonl

Q1 решить regression-net. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 две MAE в минутах на тех же461заказах; winner по меньшейMAE, warning при2000 допустим.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ["/lib/python3.14/site-packages/sklearn/neural_network/_multilayer_perceptron.py:785: ConvergenceWarning: Stochastic Optimizer: Maximum iterations (2000) reached and the optimization hasn't converged yet.\n  warnings.warn("]. Следующий шаг: перейти к следующей целевой карточке.

## 04-pytorch/float32 — 04-pytorch-float32.input.jsonl

Q1 решить float32. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 ratio=2, revenue32=123456792, lost_rub=2.88; ошибка X по двум значащим цифрам.

Q4: Да, так и есть. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 04-pytorch/zero-grad — 04-pytorch-zero-grad.input.jsonl

Q1 решить zero-grad. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 с обнулением потери стабилизируются, без накопление даст первый рост; final это последняя записанная loss до обновления.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 04b-softmax/batches — 04b-softmax-batches.input.jsonl

Q1 нарезать все 10 строк без потерь и рассогласования. Q2 общая permutation для X и y, yield из теории. Q3 sizes=[4,4,2], covered=True; произвольные метки проверю отдельно на 11 заказах.

Q4: Да, так и есть. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 04b-softmax/head-loss — 04b-softmax-head-loss.input.jsonl

Q1 выбрать потери под три цели. Q2 MSE и logaddexp из теории. Q3 три конечные неотрицательные потери; n_cats=[1,2,1,3], потому что sigmoid(z)>.5 при z>0.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 04c-debug/dropout-net — 04c-debug-dropout-net.input.jsonl

Q1 решить dropout-net. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 сравню0,.3,.5 на60train/390validation;150final не трогаю. Одна маска forward/backward.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 05-project/blur-transfer — 05-project-blur-transfer-final.input.jsonl

Q1 завершить перенос после фактического просмотра свежего PNG. Q2 на PNG видны расплывшиеся тёмные штрихи, серая внутренняя область нижней петли; подпись: позиция 55, истина 6, прогноз 4, p=.981. Доступны blind proba и функция открытия меток. Q3 зафиксирую confidence очередь 37 по вероятности и позиции до меток; ожидаю неотрицательные total/caught/missed, total=caught+missed и наличие ошибки вне очереди, потому что высокая уверенность не гарантирует верность. Единица digit, точность телефона неизвестна.

Q4: Верно! Вердикт True. Публичный вывод: ["FROZEN before labels confidence [223, 329, 240, 189, 206, 200, 290, 90, 112, 194, 403, 239, 184, 434, 428, 113, 300, 144, 421, 181, 407, 241, 392, 132, 321, 313, 309, 267, 413, 299, 211, 394, 286, 372, 41, 100, 115] Выбираю меньшую максимальную вероятность: это понятный сигнал сомнения для оператора; при равенстве меньшая позиция. Пример показывает ограничение: уверенная ошибка может остаться вне очереди. Правило выбираю без итоговых меток.\n{'total_errors': 32, 'caught_errors': 12, 'missed_errors': 20, 'missed_example_position': 25, 'evaluation_unit': 'digit', 'phone_accuracy': None}"]. Следующий шаг: перейти к следующей целевой карточке.

## 05-project/blur-transfer — 05-project-blur-transfer.input.jsonl

Q1 решить blur-transfer. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 сначала покажу увереннуюошибкуvalidation; меткиblindпока не открываю, ожидаю candidate>=.9 и изображение.

Q4: Пока не так. Итоговые метки ещё не открыты. Сначала разберите уверенную ошибку, сохраните правило/очередь, затем вызовите open_blur_labels. Вердикт False. Публичный вывод: ["Размер валидации: 337 вторая партия: 450\ndict_keys(['images', 'proba', 'target'])\ncandidate 55 truth 6 prediction 4 confidence 0.9807892421901745"]. Следующий шаг: посмотреть свежий PNG и завершить фиксацию правила до открытия меток.

## 05-project/mlp — 05-project-mlp.input.jsonl

Q1 решить mlp. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 proba формы450×10 совпадает с model.predict_proba; acc из тойже матрицы.

Q4: Верно! Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 05-project/simple — 05-project-simple.input.jsonl

Q1 решить simple. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 две доли верных по450цифрам; kNN близокMLP в этом наборе, не гарантия другогонабора.

Q4: Отлично, задача решена. Следующая задача → Вердикт True. Публичный вывод: ['']. Следующий шаг: перейти к следующей целевой карточке.

## 03-mlp/quiz/2 — embedded.input.jsonl

Q1 ограничить вывод общей отложенной выборкой. Q2 варианты вопроса. Q3 бустинг лучше ранжировал именно этих гостей; универсальное превосходство не следует.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Следующий шаг: перейти к следующей целевой карточке.

## 05-project/quiz/1 — embedded.input.jsonl

Q1 защититься от сдвига. Q2 вариант аугментации в вопросе и пример проекта. Q3 добавление сдвинутых копий помогает изучить такие искажения; другой сдвиг нужно оценить отдельно.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/1 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 сигмоида линейной оценки — логистическая регрессия.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 1 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/2 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 градиенты всех весов через цепное правило.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 2 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/3 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 численная разность проверяет аналитическую формулу.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 3 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/4 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 He sqrt(2/100) уменьшает разброс уже до первогошага.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 4 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/5 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 alpha силаL2, а не скорость.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 5 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/6 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 общиймасштаб помогаетустойчивомуспуску.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 6 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/7 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 backward считаетградиенты, step обновляет.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 7 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/8 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 одинкласс из5:5логитов иCE безsoftmax вforward.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 8 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/9 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 20батчей×5эпох=100шагов.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 9 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/10 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 dropout снижаетзависимость ототдельныхсвязей.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 10 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/11 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 сравнениеэталоннойипрогнознойцелойстроки безнезависимости.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: Отвечено 11 из 12. Итог появится, когда ответите на все вопросы.. Следующий шаг: перейти к следующей целевой карточке.

## test/quiz/12 — test.input.jsonl

Q1 выбрать обоснованный ответ. Q2 доступны вопрос и варианты актуального test.md после сохранённого открытого ответа. Q3 общаяvalidation дляAUC, задержкадляпрактическогоограничения; финальныйтестпослевыбора.

Q4: Верно! Ниже — почему остальные варианты не подходят. Вердикт True. Счёт: 12 из 12 — глава усвоена. Можно идти дальше. Пройти тест заново. Следующий шаг: перейти к следующей целевой карточке.

