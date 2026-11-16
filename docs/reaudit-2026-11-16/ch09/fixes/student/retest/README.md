# Повтор собственного проекта главы 9

`project.ipynb` содержит выводы и исполняемые повторения. `run_project.py` — подготовка, обучение и экспорт; `own_model.py` — свой МНК через lstsq. Файлы и относительные пути рассчитаны на перенос: данные по умолчанию `../../../technical/data-baseline` от папки скрипта, либо переменная COURSE_DATA, либо параметр `--data relative/path/to/data`. Данные в этом пакете не дублируются.

Python3.12, numpy,pandas,scikit-learn,joblib; для блокнота дополнительно nbformat,nbclient,ipykernel. Перед исполнением задать OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1. Запускать из папки retest.

Стандартное повторение:

```sh
python run_project.py --output artifacts/default
```

Новый ключ и новая анкета, без изменения вычислительных ячеек:

```sh
python run_project.py --key inputs/alternate-key.json --new inputs/alternate-member.json --output artifacts/alternate
```

Ключ — JSON-массив4×4 конечных чисел, строка — JSON-список `[gender,age,income_k,family_size]`. Пример: `[0,41,110,4]`. Импортируемый интерфейс: `run_project(data=None,key=None,new_member=None,output=None)`. Передавайте числовую матрицу/список, а не строку с путём; CLI читает JSON сам. Нужны обратимая матрица и достижение проверяемой точности на данных. Если проверка rank/восстановления/прогноза не проходит, это отказ входа; не подменяйте измеренную ошибку константой.

`inputs/split-ids.csv` фиксирует те же3750 train и1250 test участников и их порядок, что первый проход. Функция сопоставляет CSV по member_id, поэтому перестановка исходного CSV не меняет участников. Блокнот автоматически сравнивает train/test ID после двух ключей. Для совершенно нового набора участников нужно отдельное решение о разбиении, эта проверка его не маскирует.

Для каждого output отдельно:

- `internal`: train ID, test ID/факты/прогнозы, key.npy, hidden-model.joblib, новая открытая строка и её прогноз, метрики, деревья, summary, письмо и receiver-information.json.
- `contractor-demo`: смеси train/test/new, цель только для train. Здесь нет member_id, ключа или открытой новой анкеты.

Код, README, split-ids и стандартный seed — внутренний комплект воспроизведения. Не передавайте его как часть contractor-demo: знание seed и генератора восстанавливает ключ. Даже без них обратимая смесь не гарантирует приватность отдельных полей. Внешняя отправка и новый Git не выполнялись.

Чистый запуск: Restart Kernel/Run All для project.ipynb. Официальная общая самопроверка: `python /path/to/public/check_notebook.py project.ipynb`, без --project, поскольку протокол свой. Исходник checker не читается. Это повторный эксперимент после уже просмотренного теста, не новая независимая оценка выбранного алгоритма.
