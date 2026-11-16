import json
from pathlib import Path
out=Path(__file__).parent
rows=[]
def task(lesson, name, code, expect): rows.append(dict(lesson=lesson,task=name,code=code,expect=expect))
def q(lesson,kind,n,choice,expect): rows.append(dict(question=f'{lesson}/{kind}/{n}',choice=choice,expect=expect))
def save(lesson):
 p=out/f'{lesson}.jsonl'; p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)); rows.clear()
L='01-probability'
preamble='import pandas as pd\nd=pd.read_csv("deliveries.csv")\nok=d[d.actual_min.between(1,299)].copy()\nok["late"]=ok.actual_min>ok.promised_min\n'
task(L,'p-late',preamble+'p_late=round(ok.late.mean(),3)\np_on_time=round(1-ok.late.mean(),3)','Около 0.24 и 0.76: доля опоздавших и дополнение до единицы.')
task(L,'p-sim','import numpy as np\nrng=np.random.default_rng(42)\nheads=rng.random(100_000)<0.5\nshare=heads.mean()\nprint(round(share,2))','Около 0.5: доля орлов при большом числе бросков.')
task(L,'shift','import numpy as np\nrng=np.random.default_rng(21)\ncounts=(rng.random((200_000,20))<0.24).sum(axis=1)\np_8plus=round((counts>=8).mean(),4)\ntypical=int(np.bincount(counts).argmax())','Мода около 5, вероятность восьми и более меньше 0.1: среднее 4.8.')
q(L,'predict',1,1,'Доля на 100000 опытах должна приблизиться к 0.5 с ошибкой меньше 0.01.')
task(L,'running','import numpy as np\nimport matplotlib.pyplot as plt\nrng=np.random.default_rng(11)\nlate=rng.random(5000)<0.24\nrunning=late.cumsum()/np.arange(1,5001)\nfig,ax=plt.subplots()\nax.plot(running)\nax.axhline(0.24)\nafter_100=abs(running[99]-0.24)\nafter_5000=abs(running[4999]-0.24)','Накопленная доля в конце ближе к 0.24; график и два отклонения.')
task(L,'small-groups','import numpy as np\nrng=np.random.default_rng(8)\nshares=(rng.random((20,30))<0.24).mean(axis=1)\nspread=round(shares.max()-shares.min(),2)','20 шумных долей и их размах; одинаковые вероятности не гарантируют одинаковые наблюдаемые доли.')
q(L,'quiz',1,3,'У двух условных вероятностей разные знаменатели.')
task(L,'cond',preamble+'p_late_walk=round(ok.loc[ok.courier.eq("пеший"),"late"].mean(),3)\np_walk_late=round(ok.loc[ok.late,"courier"].eq("пеший").mean(),3)','Около 0.74 и 0.68, соответственно среди пеших и среди опозданий.')
task(L,'snow-table',preamble+'t=pd.crosstab(ok.weather.eq("снег"),ok.late,margins=True)\nn_snow_late=int(t.loc[True,True])\np_late_snow=round(n_snow_late/t.loc[True,"All"],3)\np_snow_late=round(n_snow_late/t.loc["All",True],3)\nextra=round(t.loc[True,"All"]*ok.late.mean(),1)\nadded=round(n_snow_late-extra,1)','Риск в снег выше общего; превышение положительно, знаменатели берутся из строки и столбца.')
q(L,'quiz',2,1,'Независимость означает равенство условной и общей вероятности.')
task(L,'independence',preamble+'snow=ok.weather.eq("снег")\njoint=(snow & ok.late).mean()\nproduct=snow.mean()*ok.late.mean()\np_joint=round(joint,4)\np_product=round(product,4)\nratio=round(joint/product,2)','Отношение больше 1: в снег опаздывают чаще общей частоты.')
task(L,'two-late','p=0.24\nassert abs(p*p+(1-p)**2+2*p*(1-p)-1)<1e-12\nboth=round(p*p,3)\nnone=round((1-p)**2,3)\nexactly_one=round(2*p*(1-p),3)','Вероятности до округления дают 1; ровно одно имеет два варианта.')
task(L,'at-least','import numpy as np\np,n=0.24,5\nrng=np.random.default_rng(5)\np_formula=round(1-(1-p)**n,3)\np_sim=round((rng.random((100000,n))<p).any(axis=1).mean(),3)','Около 0.746; формула дополнения и симуляция согласуются.')
save(L)
L='02-distributions'
q(L,'predict',1,1,'Ожидание 50*0.3+200*0.2=55.')
q(L,'quiz',1,2,'Ожидание определяет суммарный средний расход, не сумму индивидуального купона.')
task(L,'ev-toy','import numpy as np\nvalues=np.array([0,1,2,3])\nprobs=np.array([.55,.35,.08,.02])\nx=(values*probs).sum()\nev=round(x,2)\nper_500=round(x*500)','0.57 десерта на заказ и 285 на 500; взвешенное среднее.')
task(L,'ev-comp',preamble+'import numpy as np\nlate_min=ok.actual_min-ok.promised_min\nok["coupon"]=np.select([late_min<=5,late_min<=20],[0,150],default=400)\ncoupon=ok["coupon"]\np_150=round((coupon==150).mean(),4)\np_400=round((coupon==400).mean(),4)\nev=round(coupon.mean(),2)\nweek=round(coupon.mean()*200)','Купон 0 для опоздания до 5 включительно; расход — среднее рассчитанного столбца.')
q(L,'predict',2,2,'Ожидается 200*0.24=48 опозданий.')
q(L,'quiz',2,1,'Фиксировано n, вероятность p и независимые бинарные попытки.')
task(L,'pmf','from scipy import stats\nn,p=20,.24\np5=round(stats.binom.pmf(5,n,p),4)\np_le3=round(stats.binom.cdf(3,n,p),4)','Ровно пять через pmf, не больше трех через cdf с включением трех.')
task(L,'tail','from scipy import stats\np_bad=round(stats.binom.sf(7,20,.24),4)','Около 8%; sf(7) включает восемь.')
task(L,'binom-moments','from scipy import stats\nn,p=200,.24\nmu=round(n*p,2)\nsigma=round((n*p*(1-p))**.5,2)\np60=round(stats.binom.sf(59,n,p),4)','48, примерно 6.04; хвост около 3%.')
task(L,'pmf-plot','from scipy import stats\nimport matplotlib.pyplot as plt\nn,p=30,.24\nk=range(n+1)\nfig,ax=plt.subplots()\nax.bar(k,stats.binom.pmf(k,n,p))\nax.axvline(n*p)\nax.set_xlabel("опозданий")\nax.set_ylabel("вероятность")','31 столбик вероятностей и линия среднего 7.2.')
task(L,'binom-hand','from scipy import stats\nfrom itertools import product\nways=sum(sum(v)==2 for v in product([0,1],repeat=4))\nx=.24**2*.76**2\none=round(x,4)\np_hand=round(ways*x,4)\np_scipy=round(stats.binom.pmf(2,4,.24),4)','Шесть вариантов, каждый с двумя успехами и двумя неудачами. Не округляю one для итогового произведения.')
q(L,'predict',3,1,'У Пуассона среднее и дисперсия равны параметру 3.')
task(L,'poisson-queue','import pandas as pd\nfrom scipy import stats\na=pd.read_csv("arrivals.csv")\nk=a.loc[a.shop_id.eq("UFA-1"),"guests"]\nm=k.mean()\nlam=round(m,3)\nratio=round(k.var()/m,2)\np_queue=round(stats.poisson.sf(3,m),4)\nshare_queue=round((k>=4).mean(),4)\nper_day=round(24*stats.poisson.sf(3,m),2)','Четыре и больше — sf(3); отношение дисперсии к среднему позволяет оценить применимость модели.')
save(L)
L='02b-normal'
q(L,'predict',1,3,'Симметричный колокол: слева от среднего половина площади.')
task(L,'p-norm','from scipy import stats\nsborka=stats.norm(loc=12,scale=3)\np=sborka.sf(15)\nprint(round(p,3))','Около 0.159: правый хвост за одним стандартным отклонением.')
task(L,'quantile','from scipy import stats\nx=stats.norm(12,3)\nt90=round(x.ppf(.9),3)\np_9_15=round(x.cdf(15)-x.cdf(9),3)','t90 около 15.845, центральная полоса ±σ около 68%.')
q(L,'quiz',1,1,'Ожидаемых успехов всего 2, слишком мало для нормального приближения.')
task(L,'norm-approx','import math\nfrom scipy import stats\nn,p,k=500,.24,140\ne=stats.binom.sf(k-1,n,p)\na=stats.norm.sf(k-.5,n*p,math.sqrt(n*p*(1-p)))\nexact=round(e,4)\napprox=round(a,4)\nrel_err=round(abs(a-e)/e,3)\nrule_ok=n*p>=10 and n*(1-p)>=10','Оба хвоста несколько процентов; правило выполнено, относительная ошибка считается до округления.')
task(L,'zday','import pandas as pd\nd=pd.read_csv("deliveries.csv",parse_dates=["created"])\nn=d.groupby(d.created.dt.date).size()\nz=(n-n.mean())/n.std()\nz_max=round(z.max(),2)\nn_unusual=int((z.abs()>2).sum())','Максимальный z около 2.84: агрегирую все заказы по дню, без фильтра по времени.')
task(L,'pilot50','from scipy import stats\nn,p,observed=50,.24,20\nexpected=n*p\np_20plus=round(stats.binom.sf(observed-1,n,p),4)\nz=round((observed-expected)/(n*p*(1-p))**.5,2)','Среднее 12, двадцать заметно выше; точный биномиальный хвост мал.')
q(L,'quiz',2,3,'Правая асимметрия означает более тяжелый правый хвост, чем у колокола; модель занизит риск в контексте урока.')
task(L,'tails','import numpy as np\nimport pandas as pd\nfrom scipy import stats\nimport matplotlib.pyplot as plt\nd=pd.read_csv("deliveries.csv")\na=d.amount\nm,s=a.mean(),a.std()\nr=(a>m+2*s).mean()\nn=stats.norm.sf(2)\nreal_tail=round(r,4)\nnormal_tail=round(n,4)\nratio=round(r/n,1)\nfig,ax=plt.subplots()\nax.hist(a,bins=40,density=True)\nx=np.linspace(a.min(),a.max(),300)\nax.plot(x,stats.norm.pdf(x,m,s))','Денежный хвост тяжелее нормального; считаю отношение исходных долей, показываю наложение.')
task(L,'log','import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nd=pd.read_csv("deliveries.csv")\nt=d.loc[d.actual_min.between(1,299),"actual_min"]\nl=np.log(t)\nskew_raw=round(t.skew(),2)\nskew_log=round(l.skew(),2)\nfig,axes=plt.subplots(1,2)\naxes[0].hist(t,bins=40)\naxes[0].set_title("минуты")\naxes[1].hist(l,bins=40)\naxes[1].set_title("log(минуты)")','После логарифма асимметрия должна приблизиться к нулю; сравнение двух гистограмм.')
save(L)
L='03-sampling'
tpre='import pandas as pd\nd=pd.read_csv("deliveries.csv")\nt=d.loc[d.actual_min.between(1,299),"actual_min"]\n'
arr=tpre+'import numpy as np\nt=t.to_numpy()\n'
task(L,'population',tpre+'mu=round(t.mean(),2)\nsigma=round(t.std(ddof=0),2)','Параметры всей учебной совокупности; беру ddof=0, потому что это совокупность.')
task(L,'one-sample',tpre+'m=t.sample(50,random_state=7).mean()\nm50=round(m,2)\nerror=round(abs(m-t.mean()),2)','Выборочное среднее близко к среднему совокупности, но не обязано совпасть.')
task(L,'p-means',arr+'rng=np.random.default_rng(3)\nmeans=[rng.choice(t,size=25).mean() for _ in range(1000)]\nprint(round(np.std(means),1))','Разброс средних около sigma/5; меньше разброса отдельных доставок.')
q(L,'quiz',1,4,'ЦПТ описывает распределение средних, сами данные не изменяет.')
task(L,'clt','import numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nd=pd.read_csv("deliveries.csv")\nkm=d.distance_km.to_numpy()\nrng=np.random.default_rng(4)\nmeans=np.array([rng.choice(km,size=50).mean() for _ in range(3000)])\nskew_data=round(pd.Series(km).skew(),2)\nskew_means=round(pd.Series(means).skew(),2)\nfig,axes=plt.subplots(1,2)\naxes[0].hist(km,bins=40)\naxes[1].hist(means,bins=40)','Средние менее скошены, чем исходные расстояния; наглядное проявление ЦПТ.')
q(L,'predict',1,1,'Увеличили n в четыре раза, SE уменьшилась вдвое: отношение 2.')
q(L,'quiz',2,4,'SE пропорциональна 1/sqrt(n), нужно учетверить выборку.')
task(L,'se-check',arr+'rng=np.random.default_rng(2)\nmeans=np.array([rng.choice(t,size=30).mean() for _ in range(3000)])\nse_sim=round(means.std(),2)\nse_formula=round(t.std()/np.sqrt(30),2)','Симуляционная и формульная SE примерно равны.')
task(L,'se-fn','import math\ndef se(sigma,n):\n    return sigma/math.sqrt(n)\nses=[round(se(11,n),2) for n in [25,100,400]]','2.2, 1.1, 0.55; каждый раз четыре n дают половину SE.')
task(L,'n-needed','import math\nsigma=11\nn_needed=math.ceil((sigma/.5)**2)','484 доставки: решаю sigma/sqrt(n)<=0.5.')
task(L,'coverage',arr+'rng=np.random.default_rng(9)\nmeans=np.array([rng.choice(t,size=40).mean() for _ in range(4000)])\nse=t.std()/np.sqrt(40)\nshare_within=(abs(means-t.mean())<=1.96*se).mean()','Доля должна быть около 0.95, интервалы заданы через известные параметры учебной совокупности.')
task(L,'se-share','import math\nimport numpy as np\nrng=np.random.default_rng(6)\np=.24\nse_100=round(math.sqrt(p*(1-p)/100),4)\nshares=(rng.random((5000,100))<p).mean(axis=1)\nse_sim=round(shares.std(),4)\nn_2pp=math.ceil(p*(1-p)/.02**2)','Около .0427; для SE .02 нужно 456 доставок.')
q(L,'predict',2,1,'Взвешивание по чекам завышает частоту до 5.83 против 3 по людям.')
q(L,'quiz',3,2,'Случайный обзвон лучше отражает базу: приложение смещено к активным.')
task(L,'hall-survey','import pandas as pd\ng=pd.read_csv("guests_churn.csv")\nv=g.visits_90d\nt=v.mean()\nh=g.sample(500,weights="visits_90d",replace=True,random_state=5).visits_90d.mean()\ntrue_mean=round(t,2)\nhall_mean=round(h,2)\nbias=round(h-t,2)\ntheory=round((v*v).sum()/v.sum(),2)','Опрос чеков завысит частоту: активные гости имеют больший вес.')
task(L,'app-survey','import pandas as pd\ng=pd.read_csv("guests_churn.csv")\nt=g.churned.mean()\na=g.loc[g.app.eq(1),"churned"].mean()\nc=g.sample(150,random_state=7).churned.mean()\ntrue_rate=round(t,3)\napp_rate=round(a,3)\ncall_rate=round(c,3)\nerr_app=round(abs(a-t),3)\nerr_call=round(abs(c-t),3)\nse_call=round((c*(1-c)/150)**.5,3)\nbetter="call" if abs(c-t)<abs(a-t) else "app"','Ожидаю call: случайная маленькая выборка может быть ближе большой смещенной.')
save(L)
task('03-sampling','p-means','import pandas as pd\nimport numpy as np\nd = pd.read_csv("deliveries.csv")\nt = d.loc[d["actual_min"].between(1, 299), "actual_min"].to_numpy()\nrng = np.random.default_rng(3)\nmeans = [rng.choice(t, size=25).mean() for _ in range(1000)]\nprint(round(np.std(means), 1))','Повторная сдача: собираю ровно выданные строки Parsons. Ожидаю принятый вывод разброса около σ/5.')
save('03-sampling-retry')
L='04-confidence'
q(L,'quiz',1,1,'95% относится к покрытию процедурой, не к отдельным доставкам.')
ppr=tpre+'import numpy as np\np=t[d.loc[t.index,"shop_id"].eq("PRM-1")]\n'
task(L,'ci-mean',ppr+'m=p.mean()\nse=p.std()/np.sqrt(len(p))\nlo=round(m-1.96*se,2)\nhi=round(m+1.96*se,2)','Симметричный интервал среднего, ширина определяется SE, а не σ.')
task(L,'t-interval',ppr+'from scipy import stats\na,b=stats.t.interval(.95,len(p)-1,loc=p.mean(),scale=p.std()/np.sqrt(len(p)))\nlo_t=round(a,2)\nhi_t=round(b,2)\nt_mult=round(stats.t.ppf(.975,len(p)-1),3)','Чуть шире интервала с 1.96; t-множитель близок к 1.96 на достаточно большой группе.')
task(L,'coverage-small',arr+'from scipy import stats\nmu=t.mean()\nrng=np.random.default_rng(13)\nhits=[]\nfor _ in range(4000):\n    s=rng.choice(t,size=8)\n    se=s.std(ddof=1)/np.sqrt(8)\n    lo,hi=stats.t.interval(.95,7,loc=s.mean(),scale=se)\n    hits.append(lo<=mu<=hi)\ncoverage=round(np.mean(hits),3)','Покрытие может отличаться от .95 из-за малой выборки и асимметрии.')
q(L,'predict',1,1,'Даже без наблюдаемых опозданий верхняя граница положительна, нижняя ноль.')
task(L,'p-wilson','from statsmodels.stats.proportion import proportion_confint\nlate, n = 12, 40\nlo, hi = proportion_confint(late, n, method="wilson")\nprint(round(lo, 3), round(hi, 3))','Границы вокруг 0.3, обе внутри [0,1].')
task(L,'courier-ci',preamble+'from statsmodels.stats.proportion import proportion_confint\ng=ok.groupby("courier").late.agg(["size","sum","mean"])\na,b=proportion_confint(g["sum"],g["size"],method="wilson")\nci=pd.DataFrame({"n":g["size"],"late":g["mean"].round(3),"lo":a.round(3),"hi":b.round(3)})','Таблица размера группы, доли и интервала с индексом типа курьера.')
task(L,'widths',tpre+'import numpy as np\nfrom scipy import stats\nu=t[d.loc[t.index,"shop_id"].eq("UFA-1")]\nwidths={}\nfor level in [.90,.95,.99]:\n    lo,hi=stats.t.interval(level,len(u)-1,loc=u.mean(),scale=u.std()/np.sqrt(len(u)))\n    widths[level]=round(hi-lo,2)','Ширины возрастают вместе с уровнем доверия.')
task(L,'errorbars',preamble+'import matplotlib.pyplot as plt\nfrom statsmodels.stats.proportion import proportion_confint\ng=ok.groupby("shop_id").late.agg(["sum","size","mean"]).sort_values("mean")\nlo,hi=proportion_confint(g["sum"],g["size"],method="wilson")\nfig,ax=plt.subplots()\nax.errorbar(g.index,g["mean"],yerr=[g["mean"]-lo,hi-g["mean"]],fmt="o",capsize=4)\nax.set_ylabel("доля опозданий")','Точки отсортированы по доле, усы — расстояния до границ, не сами границы.')
task(L,'bootstrap',tpre+'import numpy as np\nt=t[d.loc[t.index,"courier"].eq("вело")].to_numpy()\nrng=np.random.default_rng(12)\nboot=[np.median(rng.choice(t,size=len(t),replace=True)) for _ in range(5000)]\nmed=np.median(t)\nlo,hi=np.percentile(boot,[2.5,97.5])','Медиана внутри процентильного интервала, выборки того же размера с повторами.')
q(L,'quiz',2,1,'Ноль вне интервала разницы, но величина эффекта известна неточно.')
task(L,'diff-ci',preamble.replace('pd.read_csv("deliveries.csv")','pd.read_csv("deliveries.csv",parse_dates=["created"])')+'import numpy as np\npeak=ok.created.dt.hour.isin([12,13,18,19])\na=ok.loc[peak,"late"]\nb=ok.loc[~peak,"late"]\nx=a.mean()-b.mean()\nse=np.sqrt(a.mean()*(1-a.mean())/len(a)+b.mean()*(1-b.mean())/len(b))\nl=x-1.96*se\nh=x+1.96*se\ndiff=round(x*100,1)\nlo=round(l*100,1)\nhi=round(h*100,1)\nzero_inside=bool(l<=0<=h)','Разница пик минус остальное и границы в процентных пунктах; ноль проверяю до округления.')
save(L)
L='05-hypotheses'
perm_prefix=preamble+'import numpy as np\nlate=ok.late.to_numpy()\nsnow=ok.weather.eq("снег").to_numpy()\n'
task(L,'observed',perm_prefix+'observed=round((late[snow].mean()-late[~snow].mean())*100,1)','Разница снег минус остальное положительна, около 11 п.п.')
task(L,'p-perm','import numpy as np\ngrp = np.array([True, True, True, True, False, False, False, False])\nrng = np.random.default_rng(0)\nlate = np.array([1, 0, 0, 1, 1, 0, 0, 0])\nshuffled = rng.permutation(grp)\nprint(late[shuffled].mean() - late[~shuffled].mean())','Одна случайная разница долей при сохраненном числе ярлыков групп.')
q(L,'quiz',1,1,'Это вероятность таких или более крайних данных при условии отсутствия эффекта.')
task(L,'perm-snow',perm_prefix+'rng=np.random.default_rng(0)\nobserved=late[snow].mean()-late[~snow].mean()\ndiffs=[]\nfor _ in range(3000):\n    g=rng.permutation(snow)\n    diffs.append(late[g].mean()-late[~g].mean())\ndiffs=np.array(diffs)\np_value=(abs(diffs)>=abs(observed)).mean()','Двустороннее p мало, снег связан с опозданиями; меняются ярлыки, не ответы.')
task(L,'perm-fn','import numpy as np\nimport pandas as pd\ndef perm_test(a,b,n_perm=2000,seed=0):\n    rng=np.random.default_rng(seed)\n    observed=np.mean(a)-np.mean(b)\n    pool=np.concatenate([a,b])\n    diffs=[]\n    for _ in range(n_perm):\n        x=rng.permutation(pool)\n        diffs.append(x[:len(a)].mean()-x[len(a):].mean())\n    return observed,(np.abs(diffs)>=abs(observed)).mean()\nd=pd.read_csv("deliveries.csv")\nok=d[d.actual_min.between(1,299)]\nauto=ok.loc[ok.courier.eq("авто"),"actual_min"].to_numpy()\nvelo=ok.loc[ok.courier.eq("вело"),"actual_min"].to_numpy()\nres=perm_test(auto,velo)','Возвращаются разница авто минус вело и двустороннее p; общий пул переставляется и делится по исходным размерам.')
q(L,'predict',1,1,'0.03 ниже 0.05; 0.18 выше порога.')
task(L,'decision','def decision(p,alpha=0.05):\n    return "отвергаем H0" if p<alpha else "не отвергаем H0"\nanswers=[decision(p) for p in [.001,.049,.05,.3]]','Первые две отвергаем, вторые две нет; граница строго меньше.')
q(L,'quiz',2,4,'Не отвергнув ложную H0 могли пропустить эффект — ошибка II рода.')
zloop='''        a=rng.random(n)<pa
        b=rng.random(n)<pb
        pool=(a.sum()+b.sum())/(2*n)
        se=np.sqrt(pool*(1-pool)*2/n)
        p=2*stats.norm.sf(abs((a.mean()-b.mean())/se))
        hits+=p<.05
'''
task(L,'aa','import numpy as np\nfrom scipy import stats\nrng=np.random.default_rng(3)\nn=250\npa=pb=.24\nhits=0\nfor _ in range(2000):\n'+zloop+'false_rate=hits/2000','Ложных тревог около 5%, поскольку обе группы одинаковы.')
task(L,'power','import numpy as np\nfrom scipy import stats\nrng=np.random.default_rng(4)\ndef power(n,pa=.24,pb=.30,sims=2000):\n    hits=0\n    for _ in range(sims):\n'+zloop+'    return hits/sims\npower_200=power(200)\npower_800=power(800)','Мощность при 800 выше, чем при 200: истинную разницу легче заметить.')
task(L,'many','import numpy as np\nfrom scipy import stats\nrng=np.random.default_rng(5)\nn=300\npa=pb=.24\nany_hits=0\nfor _ in range(2000):\n    hits=0\n    for segment in range(20):\n'+''.join('    '+line+'\n' for line in zloop.splitlines())+'    any_hits+=hits>0\np_any=any_hits/2000\np_formula=round(1-.95**20,3)','Хотя бы одна ложная тревога примерно в 64% исследований; существенно больше alpha одного теста.')
task(L,'one-sided',preamble+'import numpy as np\nx=ok[ok.shop_id.isin(["TMN-1","PRM-1"])]\nlate=x.late.to_numpy()\ngrp=x.shop_id.eq("TMN-1").to_numpy()\nrng=np.random.default_rng(1)\nobserved=late[grp].mean()-late[~grp].mean()\ndiffs=[]\nfor _ in range(5000):\n    g=rng.permutation(grp)\n    diffs.append(late[g].mean()-late[~g].mean())\ndiffs=np.array(diffs)\np_two=(abs(diffs)>=abs(observed)).mean()\np_one=(diffs>=observed).mean()\nsame_verdict=bool((p_two<.05)==(p_one<.05))','Одностороннее p меньше, но оба вероятно выше .05: решения совпадут.')
save(L)
L='06-tests'
task(L,'welch',preamble+'from scipy import stats\na=ok.loc[ok.courier.eq("пеший"),"actual_min"]\nb=ok.loc[ok.courier.eq("вело"),"actual_min"]\nr=stats.ttest_ind(a,b,equal_var=False)\nt_stat=round(r.statistic,4)\np_value=r.pvalue','Пешие дольше вело, t положительное и p очень мало; сохраняю p без округления.')
task(L,'one-sample',preamble+'from scipy import stats\nx=ok.loc[ok.promised_min.eq(30),"actual_min"]\nr=stats.ttest_1samp(x,30)\nmean_30=round(x.mean(),1)\np_value=r.pvalue\nbeyond=bool(x.mean()>30 and p_value<.05)','Сравнение среднего с 30, beyond требует одновременно превышения и значимости.')
q(L,'quiz',1,1,'Связанные измерения одних кофеен сравниваются внутри пар.')
task(L,'paired',preamble.replace('pd.read_csv("deliveries.csv")','pd.read_csv("deliveries.csv",parse_dates=["created"])')+'from scipy import stats\nok["month"]=ok.created.dt.month\nm=ok.pivot_table(index="shop_id",columns="month",values="late",aggfunc="mean")\nmean_change=round((m[11]-m[10]).mean()*100,1)\np_value=round(stats.ttest_rel(m[11],m[10]).pvalue,3)','Изменение около +4.8 п.п. по кофейням, p около .19; пары не независимые строки.')
task(L,'p-ztest','from statsmodels.stats.proportion import proportions_ztest\ncount = [30, 45]\nnobs = [200, 210]\nz, p = proportions_ztest(count, nobs)\nprint(round(p, 3))','Вывод двустороннего p для двух долей.')
task(L,'agree',preamble+'import numpy as np\nfrom statsmodels.stats.proportion import proportions_ztest\nx=ok[ok.shop_id.isin(["KZN-2","KZN-1"])]\nlate=x.late.to_numpy()\ngrp=x.shop_id.eq("KZN-2").to_numpy()\nrng=np.random.default_rng(2)\na=late[grp]\nb=late[~grp]\np_z=proportions_ztest([a.sum(),b.sum()],[len(a),len(b)])[1]\no=a.mean()-b.mean()\ndiffs=[]\nfor _ in range(4000):\n    g=rng.permutation(grp)\n    diffs.append(late[g].mean()-late[~g].mean())\np_perm=(np.abs(diffs)>=abs(o)).mean()\ndiff_pp=round(o*100,1)','Два малых p близки, разница порядка 11 п.п.; методы согласуются.')
task(L,'chi2',preamble+'from scipy import stats\nct=pd.crosstab(ok.weather,ok.late)\nstat,chi2_p,dof,expected=stats.chi2_contingency(ct)\ne=pd.DataFrame(expected,index=ct.index,columns=ct.columns)\nmax_gap_weather=(ct[True]-e[True]).idxmax()','Погода связана с опозданием; максимальное положительное отклонение ожидаю в снег.')
q(L,'predict',1,3,'Одинаковые выборки дают нулевую разницу и p=1.')
task(L,'mwu',preamble+'from scipy import stats\nr=ok.dropna(subset=["rating"])\na=r.loc[r.weather.eq("снег"),"rating"]\nb=r.loc[~r.weather.eq("снег"),"rating"]\nmed_snow=a.median()\nmed_other=b.median()\np_value=round(stats.mannwhitneyu(a,b).pvalue,4)','Ранговый тест оценок, не равенства средних; пропуски оценок исключены.')
q(L,'quiz',2,1,'Большое p для greater не поддерживает увеличение; переворачивать гипотезу после результата нельзя.')
task(L,'alt-rain',preamble+'from scipy import stats\nx=ok[ok.shop_id.eq("KZN-2")]\nrain=x.loc[x.weather.eq("дождь"),"actual_min"]\nclear=x.loc[x.weather.eq("ясно"),"actual_min"]\np_two=round(stats.ttest_ind(rain,clear,equal_var=False,alternative="two-sided").pvalue,4)\ng=stats.ttest_ind(rain,clear,equal_var=False,alternative="greater").pvalue\np_greater=round(g,4)\np_less=round(stats.ttest_ind(rain,clear,equal_var=False,alternative="less").pvalue,4)\nadd_5min=bool(g<.05)','Для заранее сформулированного направления используем greater дождь относительно ясно, решение по его p.')
q(L,'quiz',3,3,'Малая надежная разница может не окупать изменение меню.')
task(L,'choose','def choose_test(kind,groups,paired=False,skewed=False):\n    if kind=="share" and groups==2: return "proportions_ztest"\n    if kind=="category": return "chi2_contingency"\n    if kind=="mean" and groups==1: return "ttest_1samp"\n    if kind=="mean" and groups==2 and paired: return "ttest_rel"\n    if kind=="rank" and groups==2 and not paired: return "mannwhitneyu"\n    if kind=="mean" and groups==2: return "ttest_ind"','Параметр mean: H0 равенство средних, даже при skewed; rank: совпадение распределений по рангам, это другая H0.')
task(L,'report',preamble+'import numpy as np\nfrom statsmodels.stats.proportion import proportions_ztest\ndef compare_shares(late_a,late_b):\n    a=np.asarray(late_a)\n    b=np.asarray(late_b)\n    pa,pb=a.mean(),b.mean()\n    d=pa-pb\n    se=np.sqrt(pa*(1-pa)/len(a)+pb*(1-pb)/len(b))\n    lo,hi=(d-1.96*se)*100,(d+1.96*se)*100\n    p=proportions_ztest([a.sum(),b.sum()],[len(a),len(b)])[1]\n    return f"A: {pa*100:.1f} %, B: {pb*100:.1f} %, разница {d*100:.1f} п.п. (95 % ДИ {lo:.1f}…{hi:.1f}), p = {p:.4f}"\nlate=ok.late\nphrase=compare_shares(late[ok.shop_id.eq("KZN-2")].to_numpy(),late[ok.shop_id.eq("KZN-1")].to_numpy())','Фраза объединяет доли, разницу, ее интервал и p; многоточие односимвольное.')
save(L)
L='07-ab'
abpre='import pandas as pd\nab=pd.read_csv("ab_push.csv")\n'
powerpre='import math\nfrom statsmodels.stats.proportion import proportion_effectsize\nfrom statsmodels.stats.power import NormalIndPower\n'
q(L,'quiz',1,3,'Для примерно вдвое меньшей разницы требуется примерно вчетверо больше наблюдений.')
task(L,'p-power','import math\nfrom statsmodels.stats.proportion import proportion_effectsize\nfrom statsmodels.stats.power import NormalIndPower\nh = proportion_effectsize(0.22, 0.20)\nn = NormalIndPower().solve_power(effect_size=h, alpha=0.05, power=0.8)\nprint(math.ceil(n))','Размер на группу, alpha .05 и мощность .8, округленный вверх.')
task(L,'sample-size',powerpre+'def n_for(pb):\n    return NormalIndPower().solve_power(effect_size=proportion_effectsize(pb,.09),alpha=.05,power=.8)\nn_needed=math.ceil(n_for(.10))\nn_double_mde=math.ceil(n_for(.11))\nratio=round(n_needed/n_double_mde,1)','Рост на 1 п.п. требует почти вчетверо большего n, чем рост на 2 п.п.')
task(L,'mde',powerpre+'p_a=.09\nh=NormalIndPower().solve_power(nobs1=3000,alpha=.05,power=.8)\np_b=math.sin((h+2*math.asin(math.sqrt(p_a)))/2)**2\nmde_pp=round((p_b-p_a)*100,2)','MDE чуть больше двух п.п., поскольку 3000 меньше требуемых для двух пунктов.')
q(L,'quiz',2,3,'Проверка SRM должна предшествовать метрикам; нельзя исправлять перекос удалением строк.')
task(L,'srm',abpre+'from scipy import stats\nsizes=ab.group.value_counts().sort_index()\nsrm_p=stats.chisquare(sizes).pvalue\nsrm_ok=bool(srm_p>=.01)','Около 3000 в группе и большое p: 2976 против 3024 допустимо.')
task(L,'conv',abpre+'rates=ab.groupby("group").ordered.mean()\nconv=rates.round(4).to_dict()\nlift_pp=round((rates["B"]-rates["A"])*100,2)','Около 9% и 11%, B-A около двух п.п.')
task(L,'ztest',abpre+'import numpy as np\nfrom statsmodels.stats.proportion import proportions_ztest\na=ab.loc[ab.group.eq("A"),"ordered"]\nb=ab.loc[ab.group.eq("B"),"ordered"]\np_value=round(proportions_ztest([a.sum(),b.sum()],[len(a),len(b)])[1],4)\nd=b.mean()-a.mean()\nse=np.sqrt(a.mean()*(1-a.mean())/len(a)+b.mean()*(1-b.mean())/len(b))\nci_lo=round((d-1.96*se)*100,2)\nci_hi=round((d+1.96*se)*100,2)','p около .009, ДИ B-A не содержит нуля, нижняя граница примерно .5 п.п.')
task(L,'per-buyer',abpre+'from scipy import stats\narpu=ab.groupby("group").revenue.mean().round(1).to_dict()\nx=ab[ab.ordered.eq(1)]\nper_buyer=x.groupby("group").revenue.mean().round(1).to_dict()\np_buyer=round(stats.ttest_ind(x.loc[x.group.eq("B"),"revenue"],x.loc[x.group.eq("A"),"revenue"],equal_var=False).pvalue,3)','ARPU выросла за счет конверсии, выручка покупателя должна быть близкой.')
task(L,'boot-arpu',abpre+'import numpy as np\na=ab.loc[ab.group.eq("A"),"revenue"].to_numpy()\nb=ab.loc[ab.group.eq("B"),"revenue"].to_numpy()\nrng=np.random.default_rng(1)\nboot=[rng.choice(b,len(b),replace=True).mean()-rng.choice(a,len(a),replace=True).mean() for _ in range(3000)]\ndiff=round(b.mean()-a.mean(),1)\nlo,hi=np.percentile(boot,[2.5,97.5])\nzero_inside=bool(lo<=0<=hi)','Положительная разница ARPU, интервал вероятно выше нуля и допустимого -2 рубля.')
task(L,'ab-report',abpre+'from scipy import stats\nfrom statsmodels.stats.proportion import proportions_ztest\ndef ab_report(df,metric):\n    a=df.loc[df.group.eq("A"),metric]\n    b=df.loc[df.group.eq("B"),metric]\n    s=stats.chisquare([len(a),len(b)]).pvalue\n    p=proportions_ztest([a.sum(),b.sum()],[len(a),len(b)])[1]\n    return {"n_a":len(a),"n_b":len(b),"srm_p":s,"a":round(a.mean(),4),"b":round(b.mean(),4),"diff_pp":round((b.mean()-a.mean())*100,2),"p":round(p,4),"significant":bool(p<.05 and s>=.01)}\nreport=ab_report(ab,"ordered")','Итоговый словарь хранит размеры, доли и p, significant требует также исправного разбиения.')
save(L)
L='08-pitfalls'
q(L,'quiz',1,1,'Многократный поиск первого малого p увеличивает долю ложных побед.')
peek='''import numpy as np
from scipy import stats
rng=np.random.default_rng(2)
days,per_day,sims=7,200,1000
p_rows=[]
for _ in range(sims):
    a=rng.random((days,per_day))<.1
    b=rng.random((days,per_day))<.1
    ca=a.sum(axis=1).cumsum()
    cb=b.sum(axis=1).cumsum()
    n=np.arange(1,days+1)*per_day
    pool=(ca+cb)/(2*n)
    z=(cb-ca)/n/np.sqrt(pool*(1-pool)*2/n)
    p_rows.append(2*stats.norm.sf(abs(z)))
p_rows=np.array(p_rows)
'''
task(L,'peeking',peek+'peek_rate=(p_rows<.05).any(axis=1).mean()\nfinal_rate=(p_rows[:,-1]<.05).mean()','Подглядывание даст больше ложных находок, чем один финальный анализ с частотой около .05.')
q(L,'predict',1,2,'0.05/5=.01.')
pvals='pvals=[.001,.004,.008,.02,.03,.04,.3,.6]\n'
task(L,'bonferroni',pvals+'threshold=.05/len(pvals)\nsignificant=sum(p<threshold for p in pvals)','Порог .00625, проходят два p.')
task(L,'holm','from statsmodels.stats.multitest import multipletests\n'+pvals+'r,p_adj,_,_=multipletests(pvals,method="holm")\nreject=r.tolist()\nn_holm=int(r.sum())','Холм отвергнет три гипотезы, немного мощнее Бонферрони.')
task(L,'p-holm','from statsmodels.stats.multitest import multipletests\npvals = [0.01, 0.02, 0.2]\nreject, p_adj, _, _ = multipletests(pvals, method="holm")\nprint([round(float(p), 2) for p in p_adj])','Скорректированные p .03,.04,.2; список после округления.')
task(L,'strict-peek',peek+'strict_rate=(p_rows<.05/7).any(axis=1).mean()','Строгий порог снизит общую ложную тревогу до не более примерно 5%.')
task(L,'holm-rescue','import numpy as np\nfrom scipy import stats\nfrom statsmodels.stats.multitest import multipletests\nrng=np.random.default_rng(5)\nn=300\na=rng.binomial(n,.24,size=(2000,20))\nb=rng.binomial(n,.24,size=(2000,20))\npool=(a+b)/(2*n)\nz=(a/n-b/n)/np.sqrt(pool*(1-pool)*2/n)\npvals=2*stats.norm.sf(abs(z))\nraw=(pvals<.05).any(axis=1)\nholm=(pvals.min(axis=1)<.05/20)\np_any_raw=raw.mean()\np_any_holm=holm.mean()\nsame=all(bool(multipletests(row,method="holm")[0].any())==bool(flag) for row,flag in zip(pvals[:100],holm[:100]))','Хотя бы одна гипотеза Холма отвергается ровно когда минимум p проходит первый порог .05/20. Ожидаю raw около .64, holm около .05, same True.')
task(L,'segments',abpre+'from statsmodels.stats.proportion import proportions_ztest\nfrom statsmodels.stats.multitest import multipletests\npvals={}\nfor city,x in ab.groupby("city"):\n    g=x.groupby("group").ordered.agg(["sum","size"])\n    pvals[city]=proportions_ztest(g["sum"],g["size"])[1]\np_city={c:round(p,4) for c,p in pvals.items()}\nraw_sig=sorted(c for c,p in pvals.items() if p<.05)\nr=multipletests(list(pvals.values()),method="holm")[0]\nholm_sig=sorted(c for c,flag in zip(pvals,r) if flag)','В городах мощности меньше; ожидаю отсутствие значимых городов до и после поправки.')
task(L,'practical','from statsmodels.stats.proportion import proportions_ztest\nna=nb=2000000\npa=400000/na\npb=402400/nb\np_value=proportions_ztest([400000,402400],[na,nb])[1]\ndiff_pp=round((pb-pa)*100,2)\nrel_pct=round((pb-pa)/pa*100,1)\nworth_it=bool((pb-pa)/pa*100>=2 and p_value<.05)','0.12 п.п., относительные .6%, p мало, но worth_it False по порогу бизнеса.')
q(L,'quiz',2,2,'Отбор лучших включает удачу, которая может не повториться; нужна контрольная группа.')
task(L,'regression','import numpy as np\nrng=np.random.default_rng(3)\nshops,n,p=50,80,.24\nm1=(rng.random((shops,n))<p).mean(axis=1)\nm2=(rng.random((shops,n))<p).mean(axis=1)\nworst=np.argsort(m1)[-5:]\nworst_m1=round(m1[worst].mean(),3)\nworst_m2=round(m2[worst].mean(),3)\nimproved=bool(m2[worst].mean()<m1[worst].mean())','Худшие по первому месяцу вероятно улучшатся сами, хотя мера не применялась.')
save(L)
L='09-project'
proj='import pandas as pd\nimport numpy as np\nfrom scipy import stats\nfrom statsmodels.stats.proportion import proportions_ztest\nab=pd.read_csv("ab_promise.csv",parse_dates=["ts"])\norders=ab[ab.ordered.eq(1)]\n'
q(L,'quiz',1,3,'Предел -25, нижняя -23 выше него; ноль для защитной метрики не является порогом решения.')
task(L,'design',proj+'sizes=ab.group.value_counts().sort_index()\nsrm_p=stats.chisquare(sizes).pvalue\nshort=ab[ab.distance_km<2]\npromise_ok=bool(short.loc[short.group.eq("A"),"promise_min"].eq(30).all() and short.loc[short.group.eq("B"),"promise_min"].eq(40).all())\nfar_same=bool(ab.loc[ab.distance_km.between(2,5,inclusive="left"),"promise_min"].eq(45).all() and ab.loc[ab.distance_km>=5,"promise_min"].eq(60).all())','Ожидаю исправный SRM и True для обеих построчных проверок обещания; ровно 2 км относится к дальней зоне.')
sharefn='''def share_result(df,metric):
    a=df.loc[df.group.eq("A"),metric]
    b=df.loc[df.group.eq("B"),metric]
    d=b.mean()-a.mean()
    se=np.sqrt(a.mean()*(1-a.mean())/len(a)+b.mean()*(1-b.mean())/len(b))
    p=proportions_ztest([b.sum(),a.sum()],[len(b),len(a)])[1]
    return a.mean(),b.mean(),d,d-1.96*se,d+1.96*se,p
'''
task(L,'late',proj+sharefn+'a,b,d,lo,hi,p_late=share_result(orders,"late")\nlate_a=round(a,4)\nlate_b=round(b,4)\ndiff_pp=round(d*100,1)\nci=(round(lo*100,1),round(hi*100,1))','Обещание 40 вместо 30 должно снизить долю опозданий; считаю только среди заказов, интервал B-A в п.п.')
task(L,'conversion',proj+sharefn+'a,b,d,lo,hi,p_all=share_result(ab,"ordered")\nd_all=round(d*100,2)\na,b,d,lo,hi,p_short=share_result(ab[ab.distance_km<2],"ordered")\nd_short=round(d*100,2)\na,b,d,lo,hi,p_far=share_result(ab[ab.distance_km>=2],"ordered")\nd_far=round(d*100,2)','Ожидаю снижение конверсии в пешей зоне; дальше эффект должен быть слабее, обещание там не меняли.')
task(L,'ratings',proj+'r=orders.dropna(subset=["rating"])\na=r.loc[r.group.eq("A"),"rating"]\nb=r.loc[r.group.eq("B"),"rating"]\nrating_a=round(a.mean(),2)\nrating_b=round(b.mean(),2)\nlow_a=round((a<=4).mean(),3)\nlow_b=round((b<=4).mean(),3)\np_rating=stats.mannwhitneyu(a,b).pvalue','Рейтинги могут улучшиться при меньшем числе опозданий, но вывод только об оценивших.')
moneycode='''a=ab.loc[ab.group.eq("A"),"amount"]
b=ab.loc[ab.group.eq("B"),"amount"]
d=b.mean()-a.mean()
se=np.sqrt(a.var(ddof=1)/len(a)+b.var(ddof=1)/len(b))
rev_lo=d-1.96*se
rev_hi=d+1.96*se
'''
task(L,'money',proj+moneycode+'rev_a=round(a.mean(),1)\nrev_b=round(b.mean(),1)\np_rev=stats.ttest_ind(b,a,equal_var=False).pvalue','Интервал выручки включает неопределенность потери; правило сравнит его с -10, не только с нулём.')
task(L,'cities',proj+sharefn+'from statsmodels.stats.multitest import multipletests\nrows=[]\nfor city,x in orders.groupby("city"):\n    a,b,d,lo,hi,p=share_result(x,"late")\n    rows.append({"city":city,"late_a":a,"late_b":b,"diff_pp":d*100,"p":p})\nby_city=pd.DataFrame(rows).set_index("city")\nby_city["p_holm"]=multipletests(by_city.p,method="holm")[1]\nall_cities=bool(((by_city.p_holm<.05)&(by_city.diff_pp<0)).all())','По всем городам проверяю направление и скорректированное p; устойчивость не заменяет общий результат.')
task(L,'chart',proj+'import matplotlib.pyplot as plt\nfrom statsmodels.stats.proportion import proportion_confint\nfig,axes=plt.subplots(1,2,figsize=(11,4))\nfor ax,df,metric,title in [(axes[0],orders,"late","Меньше нарушенных обещаний"),(axes[1],ab[ab.distance_km<2],"ordered","Цена нового обещания в конверсии")]:\n    g=df.groupby("group")[metric].agg(["sum","size","mean"])\n    lo,hi=proportion_confint(g["sum"],g["size"],method="wilson")\n    bars=ax.bar(g.index,g["mean"]*100,yerr=[(g["mean"]-lo)*100,(hi-g["mean"])*100],capsize=5)\n    ax.bar_label(bars,labels=[f"{v*100:.1f}" for v in g["mean"]])\n    ax.set_title(title)\n    ax.set_ylabel("%")\nfig.tight_layout()','Два графика с процентами, подписями и Уилсоном для отдельных долей; разницу и ее интервал помещу в блокнот.')
reportfn='''def promise_report(ab):
    sizes=ab.group.value_counts().sort_index()
    srm_ok=bool(stats.chisquare(sizes).pvalue>=.01)
    o=ab[ab.ordered.eq(1)]
    _,_,ld,_,_,lp=share_result(o,"late")
    _,_,cd,_,_,cp=share_result(ab[ab.distance_km<2],"ordered")
    a=ab.loc[ab.group.eq("A"),"amount"]
    b=ab.loc[ab.group.eq("B"),"amount"]
    rd=b.mean()-a.mean()
    se=np.sqrt(a.var(ddof=1)/len(a)+b.var(ddof=1)/len(b))
    lo,hi=rd-1.96*se,rd+1.96*se
    rp=stats.ttest_ind(b,a,equal_var=False).pvalue
    if not srm_ok or not(ld<0 and lp<.05) or hi < -10:
        decision="не внедрять"
    elif lo > -10:
        decision="внедрять"
    else:
        decision="неопределённо"
    return {"srm_ok":srm_ok,"late_diff_pp":round(ld*100,1),"late_p":lp,"conv_short_diff_pp":round(cd*100,2),"conv_short_p":cp,"rev_diff":round(rd,1),"rev_p":rp,"rev_lo":round(lo,1),"rev_hi":round(hi,1),"decision":decision}
'''
task(L,'decision',proj+sharefn+reportfn+'report=promise_report(ab)','Функция следует записанному плану и принимает решение по полным границам до округления; итог зависит от положения -10 внутри или вне интервала.')
save(L)
L='test'
for n,choice,expect in [
(1,3,'Дополнение к двум своевременным: 1-.75**2=.4375.'),
(2,2,'Биномиальное ожидание n*p=20*.25=5.'),
(3,4,'Ожидаемых опозданий только 2, ниже правила десяти.'),
(4,2,'SE описывает распределение оценки среднего между выборками.'),
(5,2,'Более высокий уровень доверия требует большего множителя и ширины.'),
(6,4,'Перевыборки дают интервал медианы и другой статистики без простой формулы.'),
(7,2,'Отсутствие оснований отвергнуть не доказывает H0.'),
(8,4,'Две независимые достаточно большие бинарные выборки — z-тест двух долей; 2x2 хи-квадрат также проверяет связь.'),
(9,4,'Постоянный ID связывает посещения одного человека, вариант нужен при каждом посещении для проверки закрепления.'),
(10,3,'MDE — минимальный различимый эффект при заданных мощности, alpha и объеме.'),
(11,2,'Найденный после перебора сегмент требует нового независимого подтверждения.'),
(12,4,'Повторные проверки увеличивают частоту ложной победы; они зависимы, поэтому не просто 14*.05.'),
(13,1,'Отбор худших включает невезение, возможна регрессия к среднему; нужен контроль.')]: q(L,'quiz',n,choice,expect)
save(L)
