from pathlib import Path
import re,json
BASE=Path('/private/tmp/kuch09round/student')
OUT=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch09/student')
lessons=['01-vectors','02-matrices','02b-vectorize','03-normal-equation','03b-own-model','04-transform','05-project']
D='''import numpy as np
import pandas as pd
d = pd.read_csv("deliveries.csv")
ok = d[d["actual_min"].between(1, 299)].copy()
ok["walk"] = (ok["courier"] == "пеший").astype(int)
X = ok[["distance_km", "items", "walk"]].values.astype(float)
y = ok["actual_min"].values
'''
MODEL='''class MyLinearRegression(RegressorMixin, BaseEstimator):
    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        w = np.linalg.solve(X1.T @ X1, X1.T @ np.asarray(y, dtype=float))
        self.intercept_, self.coef_ = w[0], w[1:]
        return self

    def predict(self, X):
        return np.asarray(X, dtype=float) @ self.coef_ + self.intercept_
'''
TIMER='''import time
def best_time(f, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        f()
        times.append(time.perf_counter() - t0)
    return float(min(times))
'''
solutions={}
def put(l,t,code,goal,where,expect,full=False):
    solutions[(l,t)]=dict(code=code,goal=goal,where=where,expect=expect,full=full)
l=lessons[0]
put(l,'revenue','revenue = qty @ price','Узнать дневную выручку, чтобы сверить кассу.','В блоке про скалярное произведение показано qty @ price.','Сумма выручек четырёх напитков в одном числе.')
put(l,'plan','plan = q * 1.05 + 10\ntotal = plan.sum()','Составить план чашек с ростом и дегустациями.','Векторная арифметика в начале урока.','Каждый напиток вырастет на 5% и 10 чашек; total сложит план.')
put(l,'p-predict','''import numpy as np
w = np.array([3.9, 1.7, 18.5])
b = 8.0
orders = [np.array([1.0, 2, 1]), np.array([4.0, 1, 0]), np.array([6.0, 4, 0])]
for x in orders:
    print(round(float(x @ w + b), 1))''','Получить минуты трёх доставок.','Доступные строки Parsons и формула x @ w + b.','Напечатаются 33.8, 25.3, 38.2 минуты.',True)
put(l,'norm','by_hand = float((v ** 2).sum() ** 0.5)\nby_numpy = np.linalg.norm(v)\nunit = (v / by_numpy).round(3)\nunit_len = round(float(np.linalg.norm(v / by_numpy)), 3)','Найти длину и направление вектора отдельно.','Раздел длины и задание деления на norm.','Длины 13, нормированный вектор примерно [0.231,0.308,0.923], длина 1.')
put(l,'dist','d = np.linalg.norm(others - me, axis=1)\nnearest = int(d.argmin())','Выбрать самого близкого гостя по трём признакам.','Пример расстояний от A и argmin.','Ближайшим станет строка 1; её отличия небольшие по всем координатам.')
put(l,'manhattan','d_euclid = np.linalg.norm(couriers-shop,axis=1)\nd_manh = np.abs(couriers-shop).sum(axis=1)\nnear_euclid = int(d_euclid.argmin())\nnear_manh = int(d_manh.argmin())\ndetour = round(float(d_manh[near_euclid]-d_manh[near_manh]),1)','Выбрать курьера по уличному пути и понять цену ошибки прямой.','Раздел манхэттенского расстояния с abs и sum.','По прямой ближе 0, по улицам 1; лишний путь 1.2 км.')
put(l,'neighbors-scale','''import numpy as np
import pandas as pd
cols = ["visits_90d", "days_since_last", "tenure_months"]
G = pd.read_csv("guests_churn.csv")[cols].values.astype(float)
def nearest(A, i, k=5):
    distances = np.linalg.norm(A-A[i],axis=1)
    distances[i] = np.inf
    return np.argsort(distances)[:k].tolist()
near_raw = nearest(G,0)
near_scaled = nearest((G-G.mean(axis=0))/G.std(axis=0),0)
common = len(set(near_raw) & set(near_scaled))
dominant = cols[int(G.std(axis=0).argmax())]''','Сравнить пять соседей гостя 0 при двух масштабах.','Разбор nearest_to_A, argsort и явные столбцы CSV в условии.','Списки исключат саму строку 0; common покажет устойчивость соседей, dominant — самый широкий сырой столбец.',True)
put(l,'cosine','def cos(a,b):\n    return float(a @ b/(np.linalg.norm(a)*np.linalg.norm(b)))\ns = [cos(shops[0],v) for v in shops[1:]]\nsims = np.round(s,3).tolist()\nmost_similar = int(np.argmax(s))+1','Найти кофейню с наиболее похожим составом напитков.','Формула cos и пример small/big.','Кофейня 1 должна быть почти копией состава; размер не помешает.')
put(l,'dot-model','manual = round(float(X.iloc[0].values @ model.coef_ + model.intercept_),2)\nsk = round(float(model.predict(X.iloc[[0]])[0]),2)','Сверить ручной прогноз первой доставки с sklearn.','Формула линейного прогноза в теории и готовый fit.','manual и sk совпадут до сотых минуты.')
put(l,'recommend','sims = guests @ me/(np.linalg.norm(guests,axis=1)*np.linalg.norm(me))\ntwin = int(sims.argmax())\nuntried = np.flatnonzero(me == 0)\nadvice = drinks[int(untried[np.argmax(guests[twin,untried])])]','Порекомендовать непробованный напиток по похожему вкусу.','Формула cos и фильтр me==0 из условия.','Выберу максимально похожую строку, затем её лучшую оценку среди нулей me.')
l=lessons[1]
put(l,'shape','rows, cols = M.shape\nsecond_row = M[1]\nlast_col = M[:,-1]','Определить размер таблицы и извлечь нужные срезы.','Первый пример M.shape и X[:,0].','3 строки,4 столбца; строка [2,40,0,1], последний столбец [0,1,1].')
put(l,'predict-all','pred = X @ w + b\nlongest = int(pred.argmax())','Найти самый долгий прогноз из четырёх заказов.','Раздел матрицы на вектор.','Получатся четыре прогноза, longest укажет строку с максимумом.')
put(l,'p-cost','''import numpy as np
recipes = np.array([[18, 150, 0], [18, 220, 0]])
prices = np.array([[2.4, 2.1], [0.09, 0.11], [0.8, 0.6]])
cost = recipes @ prices
print(cost.shape)''','Посчитать себестоимость двух напитков у двух поставщиков.','Строки Parsons и матрица рецептов.','Форма (2,2): напиток × поставщик.',True)
put(l,'supplier','cost = recipes @ prices\nmonthly = (sold @ cost).round(2)\nbest = ["А","Б"][int(monthly.argmin())]','Выбрать поставщика по месячному объёму, а не одной чашке.','Пример recipes@prices и указанное sold@cost.','Два месячных расхода; best укажет минимальный.')
put(l,'network','''import numpy as np
sales = np.array([[420,310,90],[260,280,40],[510,330,120],[300,200,60]])
price = np.array([190,210,260])
by_shop = sales @ price
by_drink = sales.sum(axis=0)*price
best_shop = int(by_shop.argmax())
share_raf = round(float(by_drink[2]/by_shop.sum()),3)
growth = int(sales.sum(axis=0) @ np.array([10,10,0]))''','Посчитать выручку сети, лидера и эффект новых цен.','Пример выручки сети прямо над практикой.','Обе суммы сойдутся; growth учитывает только капучино и латте.',True)
put(l,'by-hand','C = A @ B\nc10 = sum(A[1,k]*B[k,0] for k in range(A.shape[1]))','Понять происхождение клетки второй строки первого столбца.','Раздел строка × столбец.','c10 = 4*7+5*9+6*11 =139, совпадёт с C[1,0].')
put(l,'gram',D+'''X = ok[["distance_km","items"]].values
G = X.T @ X
diag_ok = bool(np.allclose(np.diag(G),(X**2).sum(axis=0)))
off_ok = bool(np.isclose(G[0,1],(X[:,0]*X[:,1]).sum()))
Xc = X-X.mean(axis=0)
cov = Xc.T @ Xc/(len(X)-1)
cov_ok = bool(np.allclose(cov,np.cov(X,rowvar=False)))
corr = round(float(cov[0,1]/np.sqrt(cov[0,0]*cov[1,1])),3)''','Расшифровать X.T@X и связь с ковариацией.','Блок ковариации и формула центрирования.','diag_ok,off_ok,cov_ok=True; корреляция нормирует ковариацию.',True)
put(l,'predict-df','manual = X.values @ model.coef_ + model.intercept_\nmax_diff = float(np.max(np.abs(manual-model.predict(X))))\nsame = bool(max_diff < 1e-9)','Сверить пакетный прогноз своей формулой с моделью.','Раздел X@w и заготовка модели.','same=True, разность на уровне округления.')
put(l,'intercept-col','X1 = np.column_stack([np.ones(len(X)),X.values])\nw1 = np.r_[model.intercept_,model.coef_]\npred1 = X1 @ w1','Встроить свободный член в общий матричный прогноз.','Транспонирование/единицы и прямое описание задачи.','X1 формы (n,4), pred1 совпадёт со sklearn.')
l=lessons[2]
put(l,'disc','to_pay = np.where(amount>500,amount*0.9,amount)\nsaved = round(float((amount-to_pay).sum()),1)','Посчитать оплату и общую экономию акции.','Пример np.where с надбавкой.','Ровно500 без скидки, 501 со скидкой10%.')
put(l,'best-of',TIMER+'\nt_sum = best_time(lambda: sum(range(1_000_000)))','Измерить минимум пяти реальных длительностей суммы.','Теория perf_counter и best_time.','Положительное измеренное float-время; точные секунды заранее неизвестны.',True)
put(l,'tiers','''import numpy as np
import pandas as pd
km = pd.read_csv("deliveries.csv")["distance_km"].values
bonus = np.where(km>5,90,np.where(km>2,40,0))
total_bonus = int(bonus.sum())
n_mid = int((bonus==40).sum())
n_far = int((bonus==90).sum())''','Посчитать фонд надбавок за дальность.','Вложенный np.where и границы из условия.','2 км получает0,5км получает40, свыше5 получает90.',True)
put(l,'apply-col',D+TIMER+'''def fee_apply(r):
    if r["amount"] > 1500:
        return 0
    if r["items"] >= 4:
        return 60
    return 15 * r["items"]
def fee_col(d):
    return np.where(d["amount"]>1500,0,np.where(d["items"]>=4,60,15*d["items"]))
assert np.allclose(d.apply(fee_apply,axis=1),fee_col(d))
t_apply = best_time(lambda: d.apply(fee_apply,axis=1))
t_col = best_time(lambda: fee_col(d))
speedup = t_apply/t_col if t_col else None
total = int(fee_col(d).sum())''','Заменить построчный сбор за упаковку столбцами и сравнить скорость.','Блок apply — скрытый цикл; правило fee_apply в заготовке.','Расчёты совпадут; времена измерю реально, нулевой t_col даст None.',True)
put(l,'vectorize','''def pay_vec(km,rain):
    p = 60+14*km+np.where(km>8,100,0)
    return np.where(rain,p*1.3,p)
'''+TIMER+'''same = bool(np.allclose(pay_loop(km,rain),pay_vec(km,rain)))
t_loop = best_time(lambda: pay_loop(km,rain))
t_vec = best_time(lambda: pay_vec(km,rain))
speedup = t_loop/t_vec if t_vec else None
total = int(round(float(pay_vec(km,rain).sum())))''','Получить тот же фонд выплат без100000 проходов Python.','Пример np.where, дождь применяется ко всей сумме.','same=True, total включает дальность до дождевого множителя; отношение фактически измеренных времён.')
put(l,'nearest-shop','''def nearest_vec(orders,shops):
    dist = np.column_stack([np.abs(orders-shop).sum(axis=1) for shop in shops])
    return dist.argmin(axis=1)
'''+TIMER+'''assert np.array_equal(nearest_loop(orders,shops),nearest_vec(orders,shops))
t_loop = best_time(lambda: nearest_loop(orders,shops))
t_vec = best_time(lambda: nearest_vec(orders,shops))
speedup = t_loop/t_vec if t_vec else None
load = np.bincount(nearest_vec(orders,shops),minlength=len(shops))
busiest = int(load.argmax())''','Распределить30000заказов по шести ближайшим кофейням.','Абзац про векторизацию длинного цикла и column_stack.','Номера совпадут с двумя циклами, сумма load=30000; измерю скорости.')
l=lessons[3]
put(l,'solve2','A = np.array([[3,2],[1,4]])\nb = np.array([740,880])\nprices = np.linalg.solve(A,b)','Восстановить цены двух напитков по чекам.','Пример кассы наоборот через solve.','Эспрессо120, капучино190; обе суммы чеков сойдутся.')
put(l,'dup-receipt','rank = int(np.linalg.matrix_rank(A))\ndet_abs = round(float(abs(np.linalg.det(A))),6)\nsolvable = bool(rank == A.shape[1])\nA2 = np.array([[2,1],[1,3]])\nrank2 = int(np.linalg.matrix_rank(A2))\nprices2 = np.linalg.solve(A2,np.array([590,820]))','Отличить дублированный чек от независимого.','Предупреждение проверять ранг до solve.','rank1,det0,solvableFalse; после исправления цены190и210.')
put(l,'inverse','A_inv = np.linalg.inv(A)\ncheck = A_inv @ A\nis_identity = bool(np.allclose(check,np.eye(3)))','Проверить обратное действие матрицы.','Блок A^-1 A=I.','is_identity=True с точностью float.')
put(l,'p-normal','''import numpy as np
X = np.array([[1.0], [2.0], [3.0], [4.0]])
y = np.array([3.0, 5.0, 7.0, 9.0])
X1 = np.column_stack([np.ones(len(X)), X])
w = np.linalg.solve(X1.T @ X1, X1.T @ y)
print(w.round(2).tolist())''','Получить прямую по четырём точкам.','Строки Parsons и нормальное уравнение.','Свободный член1 и вес2.',True)
put(l,'my-ols','X = ok[["distance_km","items","auto"]].values\nX1 = np.column_stack([np.ones(len(X)),X])\nw = np.linalg.solve(X1.T @ X1,X1.T @ y)\npred = X1 @ w\nmae = round(float(np.abs(y-pred).mean()),2)','Самостоятельно обучить минуты по км,позициям и авто.','Раздел Теперь на доставках, заменяю walk на auto как задано.','Четыре веса и реальные прогнозы; mae на обучении, не оценка будущего качества.')
put(l,'no-ones','w_no = np.linalg.solve(X.T @ X,X.T @ y)\nX1 = np.column_stack([np.ones(len(X)),X])\nw_with = np.linalg.solve(X1.T @ X1,X1.T @ y)\nmae_no = round(float(np.abs(y-X @ w_no).mean()),2)\nmae_with = round(float(np.abs(y-X1 @ w_with).mean()),2)\nbias_no = round(float((y-X @ w_no).mean()),2)','Оценить цену принудительного прохода через ноль.','Предупреждение о забытых единицах.','Без intercept MAE выше, средняя ошибка уже не обязана быть0.')
put(l,'rank','full = np.column_stack([np.ones(len(ok)),ok["distance_km"],pd.get_dummies(ok["courier"],dtype=int)])\nfixed = np.column_stack([np.ones(len(ok)),ok["distance_km"],pd.get_dummies(ok["courier"],drop_first=True,dtype=int)])\nrank_full = int(np.linalg.matrix_rank(full))\nrank_fixed = int(np.linalg.matrix_rank(fixed))\ncols_full = full.shape[1]\ncols_fixed = fixed.shape[1]\nok_fixed = bool(rank_fixed == cols_fixed)','Проверить дублирование константы всеми флагами.','Раздел ловушки флагов и drop_first.','full5столбцов,ранг4; fixed4столбца,ранг4.')
put(l,'orthogonal','w = np.linalg.solve(X1.T @ X1,X1.T @ y)\nresid = y-X1 @ w\ndots = X1.T @ resid\nmax_dot = float(np.abs(dots).max())\nresid_mean = float(resid.mean())\nis_orth = bool(max_dot<1e-6)\nw_bad = w.copy()\nw_bad[1] += 0.5\nsse_ratio = round(float(((y-X1 @ w_bad)**2).sum()/(resid**2).sum()),3)','Проверить, остался ли линейный след признаков в ошибках.','Разбор X1.T@resid и ортогональности.','max_dot почти0,is_orthTrue; испорченный вес увеличит SSE.')
put(l,'many-solutions','w_a = np.linalg.lstsq(full,y,rcond=None)[0]\nw_b = w_a.copy()\nw_b[0] += 10\nw_b[2:] -= 10\nmax_diff = float(np.abs(full @ w_a-full @ w_b).max())\nweights_differ = float(np.abs(w_a-w_b).max())','Продемонстрировать неоднозначные веса без изменения прогнозов.','Пояснение +10intercept,-10каждому флагу.','weights_differ10,max_diff около нуля; оба вектора оптимальны.')
put(l,'gd-preview','Xb = np.column_stack([np.ones(len(ok)),ok[["distance_km","items","walk"]].values])\nXn = np.column_stack([Xb,ok["noisy"]])\nw_base = np.linalg.solve(Xb.T @ Xb,Xb.T @ y)\nw_noisy = np.linalg.solve(Xn.T @ Xn,Xn.T @ y)\nkm_base = round(float(w_base[1]),2)\nkm_noisy = round(float(w_noisy[1]),2)\nkm_total = round(float(w_noisy[1]+1000*w_noisy[-1]),2)','Отделить нестабильный отдельный вес от общего эффекта километра.','Раздел почти-повторов и формула суммы из задания.','km_noisy может заметно измениться, суммарный эффект должен быть близок базовому.')
l=lessons[4]
perkm='''import numpy as np
class PerKmModel:
    def fit(self, km, minutes):
        self.rate_ = float(np.sum(minutes) / np.sum(km))
        return self
    def predict(self, km):
        return np.asarray(km) * self.rate_
model = PerKmModel().fit([2, 3, 5], [16, 21, 43])
'''
put(l,'p-class',perkm+'print(model.predict([4, 10]).tolist())','Упаковать правило8минут/км и применить его новым заказам.','Строки Parsons: self.rate_ хранит отношение сумм.','Прогнозы32и80минут.',True)
put(l,'fix-class',perkm+'pred = model.predict([4,10])\nprint(pred)','Исправить интерфейс обучения, чтобы прогноз читал выученную ставку.','Типичные ошибки self,атрибут,return self.','pred [32,80], цепочка fit не возвращает None.',True)
put(l,'my-class',D+'''from sklearn.base import RegressorMixin, BaseEstimator
'''+MODEL+'''new = np.array([[3.5,2,1],[8.0,4,0]])
model = MyLinearRegression().fit(X,y)
w_all = np.r_[model.intercept_,model.coef_].round(3)
pred_new = model.predict(new).round(1)''','Сохранить выученные веса модели и минуты двух новых доставок.','Класс на игрушке и задание методов fit/predict.','Четыре веса, два прогноза; predict использует обученное состояние.',True)
put(l,'mean-model',D+'''from sklearn.base import RegressorMixin, BaseEstimator
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
class MeanModel(RegressorMixin,BaseEstimator):
    def fit(self,X,y):
        self.mean_ = float(np.mean(y))
        return self
    def predict(self,X):
        return np.full(len(X),self.mean_)
cv_mean = -cross_val_score(MeanModel(),X,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
cv_lin = -cross_val_score(LinearRegression(),X,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
gain = round(float(cv_mean.mean()-cv_lin.mean()),2)''','Понять, выигрывает ли линейная модель у среднего на тех же фолдах.','Правило бизнеса — тоже модель; cross_val_score из теории.','gain положителен, средний MAE правила ожидается около8.24.',True)
put(l,'group-mean',D+'''from sklearn.base import RegressorMixin, BaseEstimator
from sklearn.model_selection import cross_val_score
Xc = ok[["courier"]]
class CourierMean(RegressorMixin,BaseEstimator):
    def fit(self,X,y):
        self.means_ = pd.DataFrame({"courier":X["courier"].to_numpy(),"y":np.asarray(y)}).groupby("courier")["y"].mean()
        return self
    def predict(self,X):
        return X["courier"].map(self.means_).to_numpy()
cv_courier = -cross_val_score(CourierMean(),Xc,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
cv_courier_mean = round(float(cv_courier.mean()),2)
walk_mean = round(float(CourierMean().fit(Xc,y).means_["пеший"]),1)
beats_mean = bool(cv_courier.mean()<8.24)''','Оценить правило диспетчера по типу курьера.','Абзац groupby в fit,map в predict.','Пять MAE и пешее среднее; beats_mean сравнит их с8.24.',True)
put(l,'class-cv',D+'''from sklearn.base import RegressorMixin, BaseEstimator
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
'''+MODEL+'''X = ok[["distance_km","items","walk","amount"]]
cv_mine = -cross_val_score(MyLinearRegression(),X,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
cv_sklearn = -cross_val_score(LinearRegression(),X,y,cv=5,scoring="neg_mean_absolute_error",n_jobs=1)
same_cv = bool(np.allclose(cv_mine,cv_sklearn))
pipe = make_pipeline(StandardScaler(),MyLinearRegression()).fit(X,y)
r2_pipe = round(float(pipe.score(X,y)),4)
top_feature = X.columns[int(np.abs(pipe[-1].coef_).argmax())]''','Проверить свой класс на копировании,CV и конвейере.','Раздел совместимости со sklearn и порядок родителей.','CV совпадёт, top_feature сравнит веса после стандартизации.',True)
l=lessons[5]
put(l,'mix','P = np.array([[0.5],[2.0]])\nscore = X @ P','Собрать один новый столбец из км и числа позиций.','Столбец P — рецепт смеси.','score формы(3,1), значения4.5,4,11.')
put(l,'diag','D = np.diag([1000,1/60])\nconverted = X @ D','Перевести км в метры, минуты в часы.','Блок масштаба диагональной матрицей.','Столбцы не смешаются, единицы сменятся.')
put(l,'p-restore','''import numpy as np
X = np.array([[1.0, 2.0], [3.0, 4.0]])
P = np.random.default_rng(0).normal(size=(2, 2))
hidden = X @ P
restored = hidden @ np.linalg.inv(P)
print(np.allclose(restored, X))''','Скрыть и вернуть те же четыре числа.','Parsons и (XP)P^-1=X.','Проверка восстановленияTrue.',True)
put(l,'invertible','mats = [P1,P2,P3]\nranks = [int(np.linalg.matrix_rank(P)) for P in mats]\nusable = [name for name,P,r in zip(["P1","P2","P3"],mats,ranks) if r==P.shape[1]]','Выбрать ключ без потери информации.','Раздел обратимости и критерий ранга.','Только P1 имеет полный ранг3.')
put(l,'drop-col','rank_d = int(np.linalg.matrix_rank(Pd))\nshape_d = (X @ Pd).shape\na = LinearRegression().fit(X,y)\nb = LinearRegression().fit(X @ Pd,y)\nr_full = r2_score(y,a.predict(X))\nr_drop = r2_score(y,b.predict(X @ Pd))\nr2_full = round(float(r_full),4)\nr2_drop = round(float(r_drop),4)\nlost = round(float(r_full-r_drop),4)','Оценить утрату флага пешего для объяснения времени.','Необратимая P и предупреждение о потере столбца.','rank2,2столбца; lost покажет падение R².')
put(l,'same-quality','a = LinearRegression().fit(X,y)\nb = LinearRegression().fit(X @ P,y)\nr2_x = round(float(r2_score(y,a.predict(X))),4)\nr2_p = round(float(r2_score(y,b.predict(X @ P))),4)\nmax_pred_diff = float(np.abs(a.predict(X)-b.predict(X @ P)).max())','Проверить сохранение МНК после обратимой смеси.','Доказательство переноса весов P^-1w.','R² одинаков, max_pred_diff близка0.')
put(l,'weights','a = LinearRegression().fit(X,y)\nb = LinearRegression().fit(X @ P,y)\nw = a.coef_\nw_p = b.coef_\nw_formula = np.linalg.inv(P) @ w\nmatch = bool(np.allclose(w_p,w_formula))\nsame_intercept = bool(np.isclose(a.intercept_,b.intercept_))','Сверить веса смеси с алгеброй.','Формула w_prime=P^-1@w и отсутствие сдвига.','matchTrue,same_interceptTrue.')
put(l,'attack','P_found = np.linalg.solve(known,hidden[:3])\nrestored = hidden @ np.linalg.inv(P_found)\nmax_err = float(np.abs(restored-X).max())\nleaked = bool(max_err<1e-6)','Проверить, вскрывает ли три известных строки остальные доставки.','Предупреждение про известные пары и условие solve.','При независимых known ключ и вся таблица восстановятся.')
put(l,'tree-vs-linear','''rows = []
for cls in [LinearRegression,lambda: DecisionTreeRegressor(max_depth=4,random_state=0),lambda: KNeighborsRegressor(n_neighbors=15,n_jobs=1)]:
    a = cls().fit(X,y)
    b = cls().fit(X @ P,y)
    rows.append([r2_score(y,a.predict(X)),r2_score(y,b.predict(X @ P))])
raw = pd.DataFrame(rows,index=["linear","tree","knn"],columns=["x","xp"])
cmp = raw.round(3)
sensitive = raw.index[(raw.x-raw.xp).abs()>0.02].tolist()''','Сравнить чувствительность трёх алгоритмов к смеси.','Таблица А дерево замечает с seed1.','linear не чувствителен, tree и knn меняют R² более0.02.')
l=lessons[6]
put(l,'look','n = len(f)\nmean_spend = round(float(f["spend_k"].mean()),1)\nsame_profile = int(f.duplicated(cols).sum())\nmax_income = f["income_k"].max()','Осмотреть5000анкет и повторяющиеся профили.','План шаг1 и duplicated по четырём признакам.','n5000; повторные профили считаю без member_id.')
put(l,'baseline','model = LinearRegression().fit(X_train,y_train)\nr2_base = round(float(r2_score(y_test,model.predict(X_test))),4)','Зафиксировать качество на отложенной четверти до смешивания.','План шаг2 и заданный split42.','Обученная model и R² только на тесте.')
put(l,'key','P = np.random.default_rng(42).normal(size=(4,4))\nrank = int(np.linalg.matrix_rank(P))\ninvertible = bool(rank==4)\ncond = round(float(np.linalg.cond(P)),1)\nhidden = X @ P\nrestore_ok = bool(np.allclose(hidden @ np.linalg.inv(P),X))','Проверить, обратим ли выбранный ключ и насколько он численно устойчив.','План шаг3 и cond.','Полный ранг4, восстановлениеTrue; cond показывает усиление ошибки.')
put(l,'hidden-quality','hidden_model = LinearRegression().fit(X_train @ P,y_train)\nr_raw = r2_score(y_test,hidden_model.predict(X_test @ P))\nsame = bool(abs(r_raw-r2_base)<=1e-9)\nr2_hidden = round(float(r_raw),4)','Убедиться, что один и тот же ключ сохраняет качество тестовых анкет.','Шаг4 и требование сравнения до округления.','sameTrue по сырым R², r2_hidden отчётно округлён.')
put(l,'weights','m1 = LinearRegression().fit(X_train,y_train)\nm2 = LinearRegression().fit(X_train @ P,y_train)\nw = m1.coef_\nw_hidden = m2.coef_\nmatch = bool(np.allclose(w_hidden,np.linalg.inv(P) @ w))\nmax_diff = float(np.abs(m1.predict(X_test)-m2.predict(X_test @ P)).max())','Проверить алгебру весов и каждый тестовый прогноз.','Шаг5 и P^-1w.','matchTrue, максимальное отклонение близко машинному округлению.')
put(l,'new-member','new = np.array([[1,34,95,3]])\npred_open = round(float(m_open.predict(new)[0]),2)\npred_hidden = round(float(m_hidden.predict(new @ P)[0]),2)\nwrong = np.random.default_rng(43).normal(size=(4,4))\npred_wrong = round(float(m_hidden.predict(new @ wrong)[0]),2)','Сделать прогноз новых трат и показать ошибку смены ключа.','Типичная ошибка новый ключ на новых анкетах.','pred_open=pred_hidden; pred_wrong может резко отличаться.')
put(l,'bad-key','bad = P.copy()\nbad[:,3] = bad[:,0]+bad[:,1]\nbad_rank = int(np.linalg.matrix_rank(bad))\nb = LinearRegression().fit(X_train @ bad,y_train)\nr = r2_score(y_test,b.predict(X_test @ bad))\nr2_bad = round(float(r),4)\nloss = round(float(r2_base-r),4)','Проверить, что зависимый ключ теряет полезный сигнал.','Шаг6 и замена столбца суммой.','bad_rank3; loss измерит потерю относительно исходной модели.')
put(l,'tree-hidden','''rows = []
for depth in [3,5,8]:
    a = DecisionTreeRegressor(max_depth=depth,random_state=0).fit(X_train,y_train)
    b = DecisionTreeRegressor(max_depth=depth,random_state=0).fit(X_train @ P,y_train)
    rows.append([r2_score(y_test,a.predict(X_test)),r2_score(y_test,b.predict(X_test @ P))])
trees = pd.DataFrame(rows,index=[3,5,8],columns=["open","hidden"]).round(4)
best_open = float(trees["open"].max())
best_hidden = float(trees["hidden"].max())''','Проверить обещание сохранения качества для другого класса моделей.','Шаг6б и теория вопросов дерева по одному признаку.','Таблицы open/hidden различаются; универсальной гарантии дереву нет.')
put(l,'attack','known = X[:4]\nP_found = np.linalg.solve(known,hidden[:4])\nkey_found = bool(np.allclose(P_found,P))\nrestored = hidden @ np.linalg.inv(P_found)\nleaked = float((np.abs(restored-X)<=0.01).all(axis=1).mean())','Проверить реальную надёжность скрытых анкет при четырёх известных профилях.','Шаг7, solve известного ключа.','key_foundTrue, leaked1 при независимых первых строках.')
# Build independently runnable submissions from visible scaffolds; no checker source is read.
bylesson={}
for lesson in lessons:
    text=(BASE/(lesson+'.md')).read_text()
    blocks=re.split(r'^## task: ',text,flags=re.M)[1:]
    entries=[]
    for block in blocks:
        task=block.split(' | ',1)[0]
        s=solutions[(lesson,task)]
        if s['full']:
            code=s['code']
        else:
            scaffold=re.search(r'```python\n(.*?)```',block,re.S).group(1)
            scaffold=scaffold.replace('    ...','    pass')
            # Replace deliberately incomplete function definitions for vector tasks.
            if task=='vectorize': scaffold=scaffold[:scaffold.index('def pay_vec')]
            if task=='nearest-shop': scaffold=scaffold[:scaffold.index('def nearest_vec')]
            code=scaffold.rstrip()+'\n'+s['code']
        e={'lesson':lesson,'task':task,'code':code,'expect':f"Q1: {s['goal']} Q2: {s['where']} Q3: {s['expect']}"}
        entries.append(e)
    bylesson[lesson]=entries
for lesson,entries in bylesson.items():
    p=OUT/lesson
    p.mkdir(exist_ok=True)
    (p/'attempt-01.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in entries))
    (p/'before.md').write_text('\n\n'.join(f"## {e['task']}\n{e['expect']}" for e in entries))
print({k:len(v) for k,v in bylesson.items()})
choices={
'01-vectors':{'predict/1':2,'quiz/1':2,'predict/2':3,'quiz/2':4},
'02-matrices':{'predict/1':1,'quiz/1':1,'quiz/2':1},
'02b-vectorize':{'quiz/1':4},
'03-normal-equation':{'predict/1':2,'predict/2':1,'quiz/1':1,'predict/3':1,'quiz/2':1},
'03b-own-model':{'quiz/1':4},
'04-transform':{'predict/1':1,'quiz/1':3,'predict/2':2,'quiz/2':4},
'05-project':{'quiz/1':3},
'test':{f'quiz/{i}':c for i,c in enumerate([3,2,4,2,2,4,2,4,4,3,2,4,1,4,3,1],1)}}
reasons={
'01-vectors/predict/1':'1*4+2*0+3*(-1)=1.',
'01-vectors/quiz/1':'Соответствие позиции признака и веса задаёт смысл произведения.',
'01-vectors/predict/2':'Разности -3 и3 в сумме0, модули дают6.',
'01-vectors/quiz/2':'Положительное умножение вектора на10 сохраняет направление, но увеличивает расстояние.',
'02-matrices/predict/1':'Внутренние3совпадают, остаются4строки и5столбцов.',
'02-matrices/quiz/1':'Строка рафа взвешивается ценами всех ингредиентов поставщикаБ.',
'02-matrices/quiz/2':'Вектор3 не может умножиться слева на1841строку.',
'02b-vectorize/quiz/1':'Поэлементное произведение двух столбцов исполняется над всем массивом.',
'03-normal-equation/predict/1':'Вторая строка вдвое первая, ранг1 меньше2.',
'03-normal-equation/predict/2':'Пять единиц дают сумму квадратов5.',
'03-normal-equation/quiz/1':'Число весов4, все1841строки уже собраны в суммы.',
'03-normal-equation/predict/3':'Вторая строка вдвое первая, независима только одна.',
'03-normal-equation/quiz/2':'Сумма всех флагов повторяет столбец единиц.',
'03b-own-model/quiz/1':'Состояние coef_ принадлежит конкретному обученному объекту a, у b его нет.',
'04-transform/predict/1':'Строк100, внутренних3совпадают, новых признака2.',
'04-transform/quiz/1':'Из известных независимых пар можно решить систему для P.',
'04-transform/predict/2':'Обратные масштабы1/2 и1/4 на диагонали.',
'04-transform/quiz/2':'В обычном МНК веса P^-1w компенсируют обратимое преобразование.',
'05-project/quiz/1':'Обратимость сохраняет весь исходный набор линейных предикторов для любой цели.'}
for lesson, mapping in choices.items():
    txt=(BASE/('test.md' if lesson=='test' else lesson+'.md')).read_text()
    questions={x.split('\n',1)[0]:x.split('\n',1)[1] for x in re.split(r'^Вопрос ',txt,flags=re.M)[1:]}
    entries=[]
    for short,c in mapping.items():
        q=lesson+'/'+short
        body=questions[q]
        selected=re.search(r'^'+str(c)+r'\. (.*)$',body,re.M).group(1)
        reason=reasons.get(q,selected)
        expect=f'Q1: Хочу определить верный вывод: {selected} Q2: Нашёл это в видимом вопросе {q} и соответствующей теории. Q3: {reason}'
        entries.append({'question':q,'choice':c,'expect':expect})
    dest=OUT/lesson
    dest.mkdir(exist_ok=True)
    (dest/'choices-01.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in entries))
    (dest/'answers-before.md').write_text('\n\n'.join(f"## {e['question']}\nВыбор {e['choice']}. {e['expect']}" for e in entries))
print('59 tasks +',sum(len(v) for k,v in choices.items() if k!='test'),'lesson questions +16 final =',59+sum(map(len,choices.values())))
