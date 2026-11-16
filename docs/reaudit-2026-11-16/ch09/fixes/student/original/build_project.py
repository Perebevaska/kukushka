from pathlib import Path
import json
OUT=Path(__file__).parent
cells=[]
def md(s): cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(True)})
def code(s): cells.append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':s.splitlines(True)})
md('''# Анкеты семейной программы: сохранение прогноза и границы приватности

## 1. Цель
Руководителю данных нужно решить, можно ли передать подрядчику преобразованные анкеты, сохранив прогноз годовых трат. Проверю обычный МНК без штрафа на одной отложенной четверти: разница R² не выше 1e-9, максимальная разница прогнозов ниже 1e-7 тыс. ₽. Сравню со средним, повреждённым ключом и деревьями. Отдельно проверю восстановление по известным парам и объясню, почему сохранённая информация не означает приватность.

Результат: воспроизводимый блокнот, собственная модель, внутренние ID/прогнозы, пример новой анкеты и отдельный учебный пакет подрядчика без member_id. Перенос на реальные персональные данные требует отдельного решения владельца данных; математическая маскировка сама по себе не обеспечивает защиту.''')
code('''import os
import sys
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from own_model import MyOLS

RANDOM_STATE = 42
DATA = Path(os.environ.get("COURSE_DATA", "../technical/data-baseline"))
ARTIFACTS = Path("artifacts")
INTERNAL = ARTIFACTS / "internal"
CONTRACTOR = ARTIFACTS / "contractor-demo"
for p in [INTERNAL, CONTRACTOR]:
    p.mkdir(parents=True,exist_ok=True)
print("Python",sys.version.split()[0],"numpy",np.__version__,"pandas",pd.__version__,"sklearn",sklearn.__version__)
print("Случайность",RANDOM_STATE,"данные",DATA)
''')
md('''## 2. Данные
Одна строка — участник семейной программы; файл учебный family_members.csv. Период сбора в пакете не указан, цель spend_k — годовые траты в тыс. ₽. Признаки строго gender, age, income_k, family_size. member_id оставляю только для внутренней связи с прогнозом.
''')
code('''f = pd.read_csv(DATA / "family_members.csv")
cols = ["gender","age","income_k","family_size"]
print("Строк/столбцов",f.shape)
print("Пропуски",f.isna().sum().to_dict())
print("Полные дубли",int(f.duplicated().sum()),"повторные ID",int(f.member_id.duplicated().sum()))
print("Повторные профили",int(f.duplicated(cols).sum()))
print(f[cols+["spend_k"]].describe().round(2).to_string())
''')
md('''**Вывод по данным.** Фактические размеры, диапазоны и пропуски напечатаны выше; количество повторных профилей не равно дубликатам людей. Проверяю уникальный ID, конечность чисел и допустимые значения; разные участники с одинаковыми анкетами остаются разными строками.

## 3. Предобработка
Фиксирую разбиение по индексам до анализа связи с целью. Не подбираю ключ по качеству теста. Генерирую его один раз от seed42 и проверяю ранг/обусловленность. В собственном классе использую lstsq расширенной матрицы вместо обращения X.T@X, чтобы не усиливать округление.
''')
code('''assert not f.isna().any().any()
assert f.member_id.is_unique
assert np.isfinite(f[cols+["spend_k"]].to_numpy()).all()
assert f.gender.isin([0,1]).all()
assert (f[["age","income_k","family_size"]]>=0).all().all()
train_idx,test_idx = train_test_split(np.arange(len(f)),test_size=0.25,random_state=RANDOM_STATE)
X = f[cols].to_numpy(dtype=float)
y = f.spend_k.to_numpy(dtype=float)
X_train,X_test = X[train_idx],X[test_idx]
y_train,y_test = y[train_idx],y[test_idx]
P = np.random.default_rng(RANDOM_STATE).normal(size=(4,4))
rank = int(np.linalg.matrix_rank(P))
cond = float(np.linalg.cond(P))
aug_rank = int(np.linalg.matrix_rank(np.column_stack([np.ones(len(X_train)),X_train])))
hidden = X @ P
restore_error = float(np.abs(hidden @ np.linalg.inv(P)-X).max())
assert rank==4 and cond<1e6 and aug_rank==5
assert np.allclose(hidden @ np.linalg.inv(P),X)
print("train/test",len(train_idx),len(test_idx),"ранг P",rank,"cond",cond)
print("ранг [1,X_train]",aug_rank,"максимальная ошибка восстановления",restore_error)
''')
md('''**Вывод по предобработке.** После проверок строки не удаляю: нет основания считать одинаковые профили ошибкой. Разбиение 3750/1250 фиксировано. Невырожденность расширенной обучающей матрицы позволяет сравнить два независимых fit и на новых строках; проверка P отдельно отвечает за обратимость преобразования.

## 4. Математическое обоснование
В исходной модели прогноз xw+b. После h=xP можно выбрать v=P⁻¹w: hv+b=xPP⁻¹w+b=xw+b. Обратимость даёт взаимное соответствие всех достижимых прогнозов, значит минимум суммы квадратов на обучении тот же. При полном ранге [1,X_train] решение единственно; два независимых fit совпадут и на новых строках. Если столбцы зависимы, два решения минимальной нормы могут расходиться вне обучающего подпространства; явный перенос весов всё равно сохранит прогноз любой строки. При сдвиге признаков меняется свободный член. Для Ridge преобразование меняет геометрию штрафа, гарантия не переносится.
''')
code('''open_model = MyOLS().fit(X_train,y_train)
hidden_model = MyOLS().fit(X_train @ P,y_train)
sk_model = LinearRegression().fit(X_train,y_train)
dummy = DummyRegressor(strategy="mean").fit(X_train,y_train)
pred_open = open_model.predict(X_test)
pred_hidden = hidden_model.predict(X_test @ P)
pred_dummy = dummy.predict(X_test)
metrics = pd.DataFrame([
    {"model":"mean","R2":r2_score(y_test,pred_dummy),"MAE_k":mean_absolute_error(y_test,pred_dummy)},
    {"model":"MyOLS open","R2":r2_score(y_test,pred_open),"MAE_k":mean_absolute_error(y_test,pred_open)},
    {"model":"MyOLS hidden","R2":r2_score(y_test,pred_hidden),"MAE_k":mean_absolute_error(y_test,pred_hidden)}
])
max_pred_diff = float(np.abs(pred_open-pred_hidden).max())
weight_match = bool(np.allclose(hidden_model.coef_,np.linalg.solve(P,open_model.coef_)))
assert np.allclose(pred_open,sk_model.predict(X_test))
assert abs(r2_score(y_test,pred_open)-r2_score(y_test,pred_hidden))<=1e-9
assert max_pred_diff<1e-7 and weight_match
print(metrics.round(6).to_string(index=False))
print("Максимальная разница прогнозов",max_pred_diff,"связь весов",weight_match)
''')
md('''**Вывод по модели.** Две версии собственного МНК дают одинаковые прогнозы до вычислительной точности, а сравнение со sklearn проверяет реализацию собственного класса. MAE выражена в тыс. ₽ годовых трат; ориентир — одно обучающее среднее. Равенство качества означает сохранение способности предсказывать в этой постановке, а не улучшение качества и не гарантию приватности.

## 5. Плохой ключ и другие модели
Не подбираю алгоритм по просмотренному тесту: деревья здесь диагностируют чувствительность к представлению. Необратимая матрица может случайно оставить всю нужную для конкретной цели информацию, но гарантии для любой цели уже нет.
''')
code('''bad = P.copy()
bad[:,3] = bad[:,0]+bad[:,1]
bad_model = MyOLS().fit(X_train @ bad,y_train)
r2_bad = float(r2_score(y_test,bad_model.predict(X_test @ bad)))
rows=[]
for depth in [3,5,8]:
    a=DecisionTreeRegressor(max_depth=depth,random_state=RANDOM_STATE).fit(X_train,y_train)
    b=DecisionTreeRegressor(max_depth=depth,random_state=RANDOM_STATE).fit(X_train @ P,y_train)
    rows.append({"depth":depth,"open":r2_score(y_test,a.predict(X_test)),"hidden":r2_score(y_test,b.predict(X_test @ P))})
trees = pd.DataFrame(rows)
print("Плохой ключ: ранг",int(np.linalg.matrix_rank(bad)),"R2",r2_bad,"потеря",r2_score(y_test,pred_open)-r2_bad)
print(trees.round(6).to_string(index=False))
''')
md('''**Вывод по альтернативам.** При плохом ключе ранг3 вместо4; изменение R² выше показывает фактическую цену потери на этих анкетах. Деревья задают пороги по отдельным признакам, поэтому сохраняющее информацию смешивание меняет доступные вопросы. Лучший из трёх результатов на этом тесте не считается независимой оценкой выбранной глубины.

## 6. Известные пары, новая анкета и передача
Обычная линейная смесь скрывает смысл чисел от случайного взгляда. Если найдены четыре независимые пары, можно решить known@P=hidden_known и вернуть всю таблицу. Ранг проверяю перед solve; случайные четыре строки не обязаны быть независимыми.
''')
code('''known = X[:4]
assert np.linalg.matrix_rank(known)==4
P_found = np.linalg.solve(known,hidden[:4])
restored = hidden @ np.linalg.inv(P_found)
leaked = float((np.abs(restored-X)<=0.01).all(axis=1).mean())
new = np.array([[1,34,95,3]],dtype=float)
new_open = float(open_model.predict(new)[0])
new_hidden = float(hidden_model.predict(new @ P)[0])
wrong_P = np.random.default_rng(RANDOM_STATE+1).normal(size=(4,4))
new_wrong = float(hidden_model.predict(new @ wrong_P)[0])
assert np.isclose(new_open,new_hidden)
print("Восстановленная доля",leaked,"ключ совпал",np.allclose(P_found,P))
print("Новая анкета,тыс.руб: open",new_open,"hidden",new_hidden,"другой ключ",new_wrong)

test_predictions = pd.DataFrame({"member_id":f.iloc[test_idx].member_id.to_numpy(),"actual_spend_k":y_test,"open_pred_k":pred_open,"hidden_pred_k":pred_hidden})
test_predictions.to_csv(INTERNAL/"test-predictions.csv",index=False)
pd.DataFrame({"member_id":f.iloc[train_idx].member_id.to_numpy(),"split":"train"}).to_csv(INTERNAL/"train-ids.csv",index=False)
np.save(INTERNAL/"key.npy",P)
joblib.dump(hidden_model,INTERNAL/"hidden-model.joblib")
train_export = pd.DataFrame(X_train @ P,columns=["f1","f2","f3","f4"])
train_export["spend_k"] = y_train
train_export.to_csv(CONTRACTOR/"train-hidden.csv",index=False)
pd.DataFrame(X_test @ P,columns=["f1","f2","f3","f4"]).to_csv(CONTRACTOR/"test-hidden.csv",index=False)
pd.DataFrame(new @ P,columns=["f1","f2","f3","f4"]).to_csv(CONTRACTOR/"new-hidden.csv",index=False)
pd.DataFrame([{"gender":1,"age":34,"income_k":95,"family_size":3,"prediction_k":new_hidden,"wrong_key_prediction_k":new_wrong}]).to_csv(INTERNAL/"new-member.csv",index=False)
metrics.to_csv(INTERNAL/"metrics.csv",index=False)
trees.to_csv(INTERNAL/"tree-diagnostic.csv",index=False)
summary={"rows":len(f),"train":len(train_idx),"test":len(test_idx),"rank":rank,"condition":cond,"r2_open":float(r2_score(y_test,pred_open)),"r2_hidden":float(r2_score(y_test,pred_hidden)),"max_prediction_difference":max_pred_diff,"bad_key_r2":r2_bad,"leaked_fraction":leaked,"new_prediction_k":new_hidden,"wrong_key_prediction_k":new_wrong}
(INTERNAL/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
letter=f"""Руководителю данных

На {len(f)} учебных анкетах использовано разбиение {len(train_idx)}/{len(test_idx)}. На тесте R² обычного МНК {summary['r2_open']:.6f}, после обратимого преобразования {summary['r2_hidden']:.6f}. Максимальная разница прогнозов {max_pred_diff:.3g} тыс. ₽. Новая анкета даёт {new_hidden:.2f} тыс. ₽ в год при том же ключе; другой ключ даёт {new_wrong:.2f}.

Сохраняется множество линейных прогнозов МНК без штрафа. При полном ранге расширенной обучающей матрицы независимо обученные модели совпадают и на новых строках. Явный перенос весов через P^-1 сохраняет любой прогноз независимо от единственности решения. Деревьям и Ridge это обещание не даю. Обусловленность ключа {cond:.2f}; зависимый ключ ранга3 даёт R² {r2_bad:.6f}.

Эта смесь не обезличивание и не криптографическая защита: по четырём независимым известным парам восстановлена доля {leaked:.1%} профилей. Годовые траты передаются как цель без защиты; отсутствие member_id не предотвращает сопоставление по другим сведениям. Не рекомендую передавать реальные анкеты на основании одного этого приёма. Нужен выбранный владельцем данных защищённый контур доступа и отдельная проверка условий передачи.

В artifacts/contractor-demo только учебные смеси train/test/new и цель train. В artifacts/internal находятся ID, истинные тестовые ответы, ключ, модель и новые открытые признаки: это внутренний пакет, не комплект подрядчика. Файлы созданы локально, никуда не отправлены. Ключ генерируется один раз и хранится внутри; замена требует повторного согласованного преобразования и обучения.
"""
(INTERNAL/"letter.md").write_text(letter)
print(letter)
''')
md('''**Вывод по приватности и передаче.** Известные независимые пары восстановили все анкеты с точностью0.01, поэтому смысловой маскировки недостаточно. Внутренний CSV сохраняет member_id и порядок тестовых строк, а учебный пакет подрядчика его не содержит. Пакет остаётся локальным; ключ и реальные профили не должны уходить вместе со смесями.

## 7. Итоговые выводы
На вопрос о сохранении качества ответ положительный для обычного МНК без штрафа и обратимого P при описанных условиях; численные оценки, новая анкета и внутреннее письмо сохранены в artifacts/internal. На вопрос о надёжной защите анкет ответ отрицательный: обратимость означает наличие всей информации, а известные пары позволяют вычислить ключ. Для реальной передачи рекомендую выбрать защищённый контур, минимальный доступ и отдельно решить, кому доступны ответы и связующие идентификаторы.

Самопроверка: чистое ядро, выполнение сверху вниз, assert сохранения прогнозов, контроль рангов, проверка собственного класса против sklearn, реальная атака известными парами, пример неверного ключа. Тест уже просмотрен в диагностике, поэтому новые выводы о качестве выбранного алгоритма потребуют новых данных.
''')
(OUT/'own_model.py').write_text('''import numpy as np
from sklearn.base import RegressorMixin, BaseEstimator

class MyOLS(RegressorMixin, BaseEstimator):
    """Ordinary least squares with an intercept via lstsq."""
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        A = np.column_stack([np.ones(len(X)), X])
        weights = np.linalg.lstsq(A, np.asarray(y, dtype=float), rcond=None)[0]
        self.intercept_ = weights[0]
        self.coef_ = weights[1:]
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_
''')
nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.14'}},'nbformat':4,'nbformat_minor':5}
(OUT/'project.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
(OUT/'README.md').write_text('''# Ученический проект главы9

`project.ipynb` — самостоятельный протокол МНК и преобразования анкет, `own_model.py` — собственный sklearn-совместимый класс. Входы не копируются: по умолчанию `../technical/data-baseline/family_members.csv` от папки student, либо `COURSE_DATA`.

Запуск из этой папки в Python3.12 с numpy,pandas,sklearn,nbformat,nbclient,joblib. Задать OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1. Выполнить чистым ядром все ячейки, затем `python /private/tmp/kuch09round/student/check_notebook.py project.ipynb` (без --project: собственный протокол, не сверка эталонных переменных).

`artifacts/internal` — внутренние ID, тестовые ответы/прогнозы, ключ, модель, метрики, новая анкета и письмо. `artifacts/contractor-demo` — локальный учебный пример скрытых train/test/new; не содержит member_id или ключа. Никакого внешнего отправления или публикации не было. Не передавайте весь каталог как комплект подрядчика: обратимые смеси не обеспечивают приватность.

Это агентское прохождение текстового пакета и фактические отправки submit.py в отдельный профиль Chromium, а не ручное нажатие всех элементов курса. В соседних каталогах уроков сохранены Q1–Q3 до действий и фактический Q4 после фидбека. Человеческие эмоции и время обучения не измерялись.
''')
print('Created notebook',len(cells),'cells')
