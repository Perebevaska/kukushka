"""Prepare counterexamples without training or executing the exercise runtime."""
import hashlib,json,re,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=Path('/private/tmp/kuch08round/course.json')
tasks=[t for t in json.loads(BASE.read_text()) if t['lesson'].startswith('ch08/') and t['kind']=='task']
T={t['lesson'].split('/')[-1]+'/'+t['id']:t for t in tasks}
P=[]
def add(id,key,expected,reason,code=None,suffix='',**kw):
    P.append(dict(id=id,key=key,expected=expected,reason=reason,code=code if code is not None else T[key]['solution']+'\n'+suffix,**kw))
def tail(key,anchor):return T[key]['solution'][T[key]['solution'].index(anchor):]

key='01-value/p-profit'
add('profit-alt',key,True,'Другой способ: сумма вкладов каждого отправленного гостя.',code='''def profit(send,y,gain=400,cost=200):
    return sum(gain if actual else -cost for selected,actual in zip(send,y) if selected)
''')
add('profit-cost-ignored',key,False,'Параметр cost обещан сигнатурой; при cost=50 ожидается 300, а не 0.',code=T[key]['solution'].replace('cost * fp','200 * fp'))
add('profit-wrong-denominator',key,False,'Оплачены все отрицательные примеры вместо только отправленных.',code=T[key]['solution'].replace('(send & (y == 0)).sum()','(y == 0).sum()'))
key='01a-pilot/pilot-delta'
add('pilot-alt',key,True,'Считаем доли через размеры групп и суммы, не groupby.mean.',code='''import pandas as pd
b=pd.read_csv('bonus_pilot.csv')
z={name:part.churned.sum()/len(part) for name,part in b.groupby('group')}
delta=round(z['контроль']-z['бонус'],3)
online=round((z['контроль']-z['бонус'])*2400-200)
''')
add('pilot-organic-attribution',key,False,'Всех оставшихся приписали бонусу.',code=T[key]['solution'].replace('d * 2400','(1-churn["бонус"]) * 2400'))
key='01b-metric-tree/p-net-conv'
add('net-alt',key,True,'Эквивалентное взвешивание конверсий числом посетителей.',code='''import pandas as pd
s=pd.read_csv('shop_funnel.csv').query('month == "2026-09"')
rate=s.checks/s.visitors
print(round(float((rate*s.visitors).sum()/s.visitors.sum()),3))
''')
add('net-unweighted',key,False,'Среднее конверсий кофеен теряет веса посетителей.',code=T[key]['solution'].replace('sep["checks"].sum() / sep["visitors"].sum()','(sep["checks"] / sep["visitors"]).mean()'))
key='02-budget/gains-plot'
plot=tail(key,'order =')
add('gains-alt-step',key,True,'Те же пары координат, step и обратный порядок artists.',code=plot.replace('ax.plot(share, caught, label="модель")','ax.step(share, caught, where="post", label="модель")'))
add('gains-corrupt-point',key,False,'Одна внутренняя доля испорчена; точка 10% осталась верной.',code=plot+'\nwrong=caught.copy();wrong[100]=.8\nax.lines[0].set_ydata(wrong)')
add('gains-hidden-axes',key,False,'Весь Axes скрыт; график отсутствует.',code=plot+'\nax.set_visible(False)')
add('gains-hidden-label',key,False,'Подпись Y отсутствует визуально.',code=plot+'\nax.yaxis.label.set_visible(False)')
add('gains-markers',key,True,'Кривая теми же точками: plot с маркерами без соединения.',code=plot.replace('ax.plot(share, caught, label="модель")','ax.plot(share,caught,".",label="модель")'))
key='03-risk/binom'
add('binom-alt',key,True,'Подсчёт доли через count_nonzero.',code=T[key]['solution'].replace('(kept < 20).mean()','np.count_nonzero(kept < 20) / len(kept)'))
add('binom-boundary',key,False,'Условие меньше 20 подменено не больше 20.',code=T[key]['solution'].replace('kept < 20','kept <= 20'))
add('binom-global-rng',key,True,'Глобальный legacy RNG заранее сдвинут; default_rng(1) независим.',code='import numpy as np\nnp.random.seed(723); np.random.random(1000)\n'+T[key]['solution'])
key='03-risk/boot-profit'
boot='''rng=np.random.default_rng(0)
ix=rng.integers(0,len(yv),(1000,len(yv)))
s,yy=send[ix],yv[ix]
profits=400*(s & (yy==1)).sum(axis=1)-200*(s & (yy==0)).sum(axis=1)
low,high=np.percentile(profits,[2.5,97.5]).round()
p_loss=(profits<0).mean()
'''
add('boot-vectorized',key,True,'Те же парные индексы в одном двумерном вызове RNG.',code=boot)
add('boot-broken-pairs',key,False,'Предложение и факт индексируются независимо.',code=boot.replace('s,yy=send[ix],yv[ix]','jx=rng.integers(0,len(yv),(1000,len(yv)))\ns,yy=send[ix],yv[jx]'))
key='04-monitoring/p-monitor'
add('monitor-alt',key,True,'Среднее и доля через суммы Python.',code='''def month_report(p,threshold=.3):
    return dict(leads=len(p),mean_pred=round(sum(map(float,p))/len(p),3),above=round(sum(x>threshold for x in p)/len(p),3))
''')
add('monitor-threshold-ignored',key,False,'Параметр threshold не используется.',code=T[key]['solution'].replace('p > threshold','p > .3'))
add('monitor-boundary',key,False,'Строго выше порога подменено >=.',code=T[key]['solution'].replace('p > threshold','p >= threshold'))
key='04b-segments/report-text'
report=T[key]['solution']
add('report-alt',key,True,'Тот же bootstrap и показатели при другом порядке и предложениях.',code=report+'''\nreport=(f"На {report_metrics['n']} заявках соцсетей получено {report_metrics['deals']} договоров. "
f"Факт {report_metrics['fact_rate']:.3f}, средний прогноз {report_metrics['pred_mean']:.3f}. "
f"AUC {report_metrics['auc']:.3f}, 95 % ДИ от {report_metrics['ci_low']:.2f} до {report_metrics['ci_high']:.2f}.")
''')
add('report-pred-fact',key,False,'Прогноз и наблюдаемая доля переставлены.',suffix='report_metrics["pred_mean"],report_metrics["fact_rate"]=report_metrics["fact_rate"],report_metrics["pred_mean"]')
add('report-n-deals',key,False,'Число заявок и договоров перепутаны.',suffix='report_metrics["n"],report_metrics["deals"]=report_metrics["deals"],report_metrics["n"]')
add('report-rng-isolated',key,True,'Лишние вызовы глобального RNG не влияют на локальный seed=0.',code='np.random.seed(582)\nnp.random.normal(size=1000)\n'+report)
key='05-explain/p-pd'
add('partial-alt',key,True,'assign создаёт новую таблицу на каждом шаге.',code='''def partial(model,X,col,grid):
    return [round(float(model.predict_proba(X.assign(**{col:v}))[:,1].mean()),3) for v in grid]
''')
add('partial-column-ignored',key,False,'Функция незаметно всегда меняет a вместо переданного col.',code=T[key]['solution'].replace('X_v[col]','X_v["a"]'))
key='05b-fairness/fair-toy'
add('fair-alt',key,True,'Определения через TP и два отдельных знаменателя.',code=T[key]['solution'][:T[key]['solution'].index('selected =')]+'''counts=t.assign(tp=t.send*t.churned).groupby('group').agg(n=('send','size'),sent=('send','sum'),actual=('churned','sum'),tp=('tp','sum'))
selected=(counts.sent/counts.n).round(2)
recall=(counts.tp/counts.actual).round(2)
precision=(counts.tp/counts.sent).round(2)
''')
add('fair-wrong-denominator',key,False,'Деление TP на всех гостей вместо уходящих.',suffix='recall=(t.assign(tp=t.send*t.churned).groupby("group").tp.mean()).round(2)')
key='06-project/decision'
add('decision-alt',key,True,'Последовательный проход, допускает пустое множество и удерживает порядок.',code='''passed=[]
choice=cost_of_safety=None
for city in risk.index:
    if risk.loc[city,'p_loss']<=.025:
        passed.append(city)
        if choice is None or risk.loc[city,'mean']>risk.loc[choice,'mean']:
            choice=city
if choice is not None:cost_of_safety=max(risk['mean'])-risk.loc[choice,'mean']
''')
add('decision-all-leader',key,False,'Лидер по всем городам совпадает только на учебном входе.',code=T[key]['solution'].replace('ok["mean"].idxmax()','risk["mean"].idxmax()'))
add('decision-strict',key,False,'Ровно 2.5% исключено ошибочно.',code=T[key]['solution'].replace('<= 0.025','< 0.025'))
add('decision-no-empty',key,False,'Пустое множество не обработано.',code=T[key]['solution'].replace(' if len(ok) else None',''))
add('decision-money-units',key,False,'Тысячи рублей ошибочно превращены в рубли.',suffix='cost_of_safety=cost_of_safety*1000 if cost_of_safety is not None else None')
key='07-final-project/fp-money'
add('money-alt',key,True,'Другой допустимый заранее названный порог 0.10.',code=T[key]['solution'].replace('best_t = curve.loc[curve["profit"].idxmax(), "threshold"]','best_t = 0.10'))
add('money-units',key,False,'Расход контакта задан тысячами вместо рублей.',suffix='test_profit=1600*test_buyers-.150*test_sent')
add('money-curve-key',key,False,'Кривая с прежними прибылями приписывает их другим порогам.',suffix='curve["threshold"]=curve["threshold"].values[::-1]')
add('money-curve-reorder',key,True,'Целые строки таблицы кривой переставлены без потери соответствия.',suffix='curve=curve.iloc[::-1]')
key='07-final-project/fp-honest'
add('honest-alt',key,True,'Другой допустимый заранее названный порог 0.10.',code=T[key]['solution'].replace('best_t_incr = incr.loc[incr["margin"].idxmax(), "threshold"]','best_t_incr = 0.10'))
add('honest-ignore-organic',key,False,'Все ожидаемые покупки приписаны рассылке.',suffix='honest_profit=naive_profit')
add('honest-round-organic',key,False,'Округление доли органики до денежного расчёта.',suffix='honest_profit=round(1600*(eb-organic*n_send)-150*n_send)')

(HERE/'tasks-original.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
(HERE/'probes-original.json').write_text(json.dumps(P,ensure_ascii=False,indent=2)+'\n')
light=[p for p in P if not T[p['key']].get('setup') and 'sklearn' not in p['code'] and p['key']!='05b-fairness/fair-toy']
(HERE/'probes-light.json').write_text(json.dumps(light,ensure_ascii=False,indent=2)+'\n')
(HERE/'tasks-light.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
contracts=[]
for key,t in T.items():
    names=list(dict.fromkeys(re.findall(r"need\(['\"]([^'\"]+)",t['check'])))
    contracts.append(dict(key=key,outputs=names,check_sha256=hashlib.sha256(t['check'].encode()).hexdigest(),new_probes=[p['id'] for p in P if p['key']==key]))
(HERE/'contracts.json').write_text(json.dumps(contracts,ensure_ascii=False,indent=2)+'\n')
(HERE/'manifest-original.json').write_text(json.dumps(dict(export=str(BASE),export_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),data='../technical/data-baseline',tasks=len(tasks),probes=len(P),light_probes=len(light),note='Expectations prepared before execution. No training or bootstrap during preparation.'),ensure_ascii=False,indent=2)+'\n')
print(len(tasks),'contracts;',len(P),'probes;',len(light),'light probes')
