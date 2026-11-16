# Происхождение исполнения

Разрешённый вход: /private/tmp/kuch13round/student/. Все свои файлы созданы только в docs/reaudit-2026-11-16/ch13/student/. Чужие отчёты, AGENTS, content, keys/hints/check/solution/setup JSON вне пакета не читались. Единственная UI hint получена через публичный bridge после собственной попытки. Публичный check_notebook.py прочитан и использован только в режиме --no-run.

Сдачи: публичный submit.py создаёт задания для изолированного Chromium bridge, input сохраняется до отправки, raw feedback после. Первые файлы сохранены, коррекции отдельно. Initial-attempts агрегат принадлежит bridge и мной не изменялся. Полные imports/starters включены в code; дополнения переопределяют placeholders. Несданный 02-tfidf.unsent-draft.jsonl — только черновик, в статистику попыток не входит.

Native: /private/tmp/ku-audit/nb-env/bin/python, Python 3.12.14, pandas 3.0.6, numpy 2.4.6, sklearn 1.8.0, matplotlib 3.10.9, pymorphy3 2.0.6, torch 2.15.0, transformers 5.23.0. Все модели запускались последовательно в предоставленное координатором CPU-окно; OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1, для torch также set_num_threads(1) и set_num_interop_threads(1), TOKENIZERS_PARALLELISM=false.

Transformer: исходная cointegrated/rubert-tiny2; локальный разрешённый кэш models--cointegrated--rubert-tiny2, snapshot e8ed3b0c8bbf4fb6984c3de043bf7d2f4e5969ae. Веса не изменялись. from_pretrained(..., local_files_only=True), HF_HUB_OFFLINE=1 и TRANSFORMERS_OFFLINE=1. Только свои вычисленные векторы сохранялись в student/extra-cache; модель не переобучалась. Другие доступные модели не использовались, новые веса не скачивались.

Попытка nbclient получила PermissionError на loopback bind в sandbox (own-execution.log). Корректное последующее исполнение — execute_native.py: отдельный процесс, чистый namespace, последовательный exec каждой code-ячейки, stdout/stderr сохраняются как реальные notebook outputs; реальный PNG графика включён display_data после открытия. Это не Jupyter/nbclient PASS. Agg сообщает о невозможности интерактивного show, однако savefig реально создал изображение, оно открыто.

Свой проект и оба extra реально выполнены; не только прочитаны. Дополнительные текстовые задания extra прочитаны, отдельно не исполнены. Времена внутри extra — измерения машинного исполнения, не времена человека. Фикстуры учебной LLM — офлайн-данные, не live API. CPUFREE передан после вычислений; затем только Markdown, JSON и статическая проверка оформления.
