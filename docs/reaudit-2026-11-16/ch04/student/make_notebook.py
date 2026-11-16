import json,shutil
from pathlib import Path
out=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch04/student')
(out/'data').mkdir(exist_ok=True)
for f in ['deliveries.csv','deliveries_branch.csv']:shutil.copyfile(Path('data')/f,out/'data'/f)
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):cells.append(dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=s.splitlines(True)))
md('# Почему доставка опаздывает\n\n## 1. Цель\nРуководителю доставки нужны масштаб нарушений обещания и проверяемое решение. Метрика — доля доставок позже обещанного среди доставок с пригодным временем. Критерий пилота: не менее 80% выбранной подгруппы укладываются в новый срок.\n\n**Главное.** В пригодных данных опоздали 441/1841 доставки (24.0%); для полной выгрузки крайние сценарии дают 23.5–25.4%. Самая проблемная группа — пешие: 298/403 (73.9%). При обещании 30 минут разрыв сохраняется; на исходных маршрутах п80 этой подгруппы равен 40 минутам. Предлагаю проверить срок 40 минут небольшим контролируемым пилотом и следить за отказами от заказа.')
code('''import sys
import math
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
RANDOM_STATE = 42
DATA = Path('data')
FIGURES = Path('figures')
FIGURES.mkdir(exist_ok=True)
print('Python',sys.version.split()[0], 'pandas',pd.__version__, 'matplotlib',matplotlib.__version__)
def say(s):
    display(Markdown('**Вывод.** '+s))
def save(fig,name):
    fig.tight_layout()
    fig.savefig(FIGURES / (name+'.png'),dpi=130,bbox_inches='tight')
    plt.show()
''')
md('## 2. Данные\nОдна строка — одна доставка сети за сентябрь–ноябрь 2026. Известны обещание, факт, расстояние, тип курьера, погода и добровольная оценка. Источник — публичная учебная выгрузка. Статус исключённых доставок неизвестен.')
code('''raw=pd.read_csv(DATA/'deliveries.csv',parse_dates=['created'])
print(raw.shape, raw.created.min(),raw.created.max())
print(raw.isna().sum())
print('Полные дубли:',raw.duplicated().sum())
display(raw.head())
say(f'В выгрузке {len(raw)} строк; время отсутствует у {raw.actual_min.isna().sum()}. Пропуски rating не заполняю — это добровольный ответ гостя.')''')
md('**Вывод по данным.** Период осени наблюдается целиком, но неделя на каждом краю неполная. Анализ оценок относится только к ответившим гостям.')
md('## 3. Предобработка\nПравдоподобный интервал фактического времени — 1–299 минут: крайние значения после 735 минут отделены от реальных доставок большим разрывом. Изъятие этих строк не превращает их в своевременные доставки.')
code('''ok=raw[raw.actual_min.between(1,299)].copy()
ok['late']=ok.actual_min>ok.promised_min
ok['delay']=ok.actual_min-ok.promised_min
ok['hour']=ok.created.dt.hour
log={'всего':len(raw),'без времени':int(raw.actual_min.isna().sum()),'невозможное время':int((raw.actual_min.notna()&~raw.actual_min.between(1,299)).sum()),'осталось':len(ok)}
display(pd.Series(log,name='доставок').to_frame())
missing=raw[~raw.index.isin(ok.index)].groupby('courier').size()
limits=pd.DataFrame({'late':ok.groupby('courier').late.sum(),'all':raw.groupby('courier').size(),'excluded':missing}).fillna(0)
limits['lower_pct']=limits.late/limits['all']*100
limits['upper_pct']=(limits.late+limits.excluded)/limits['all']*100
display(limits.round(1))
say(f'Осталось {len(ok)}/{len(raw)} строк. Общая доля лежит между {ok.late.sum()/len(raw):.1%} и {(ok.late.sum()+len(raw)-len(ok))/len(raw):.1%} в крайних сценариях; это не доверительный интервал.')''')
md('**Вывод по предобработке.** Исключены 25 пропусков и 11 невозможных значений. Концентрацию потерь по курьерам показал отдельно: малое число потерь в целом не гарантирует малый эффект в группе.')
md('## 4. Анализ\nПроверяю масштаб, признаки, обещание внутри курьеров, состав KZN-2, снег и недели, оценки и две собственные группы.')
md('### 4.1. Масштаб\nДлительность описываю медианой и квантилями, а нарушение обещания — долей late.')
code('''late_pct=round(ok.late.mean()*100,1)
late_median=ok.loc[ok.late,'delay'].median()
p90_late=ok.loc[ok.late,'delay'].quantile(.9)
fig,ax=plt.subplots(figsize=(8,3.5))
ax.hist(ok.delay,bins=16,range=(-40,40),color='lightgray')
ax.axvline(0,color='tab:red')
ax.set(title='Почти четверть доставок нарушает обещание',xlabel='опоздание, мин (отрицательное — раньше)',ylabel='доставок')
save(fig,'scale')
say(f'Опоздали {ok.late.sum()}/{len(ok)} ({late_pct}%). Среди опоздавших медиана задержки {late_median:.1f} мин, п90 {p90_late:.1f} мин. Окно графика −40…40; вне него {((ok.delay < -40)|(ok.delay>40)).sum()} доставок.')''')
md('**Вывод по масштабу.** Нарушение обещания встречается регулярно. Одна средняя длительность скрыла бы и своевременные доставки, и хвост задержек.')
md('### 4.2. Признаки\nРазмах доли между группами — ориентир порядка исследования, а не причинная важность.')
code('''r={}
for col in ['courier','weather','shop_id','items','hour']:
    g=ok.groupby(col).late.agg(['mean','size'])
    s=g[g['size']>=50]['mean']
    r[col]=round((s.max()-s.min())*100,1)
ranking=pd.Series(r).sort_values(ascending=False)
top_factor=ranking.index[0]
display(ranking)
g=ok.groupby(top_factor).late.agg(n='size',share='mean').sort_values('share',ascending=False)
fig,ax=plt.subplots(figsize=(7,3.5))
bars=ax.bar(g.index,g.share*100,color=['tab:red']+['lightgray']*(len(g)-1))
ax.bar_label(bars,labels=[f'{s:.1%}; n={n}' for s,n in zip(g.share,g.n)])
ax.set(title='Пешие чаще нарушают обещание',xlabel='тип курьера',ylabel='опозданий, %',ylim=(0,100))
save(fig,'factors')
say(f'Наибольший размах у {top_factor}: {ranking.iloc[0]} п.п. Число групп и их размеры различаются; это связь, не оценка причинного эффекта.')''')
md('**Вывод по признакам.** Начинаю с курьера и проверяю, не отражает ли он только короткое обещание.')
md('### 4.3. Обещание и выбранная группа\nГруппу выбираю вычислением, при равенстве — первое название по алфавиту.')
code('''chosen=ok.groupby('courier').late.mean().sort_index().idxmax()
pv=ok.pivot_table(index='promised_min',columns='courier',values='late',aggfunc='mean')*100
counts=ok.pivot_table(index='promised_min',columns='courier',values='late',aggfunc='size')
display(pv.round(1));display(counts)
s=ok[(ok.courier==chosen)&(ok.promised_min==30)]
walk_p80=s.actual_min.quantile(.8)
fair_promise=math.ceil(walk_p80/5)*5
s45=ok[(ok.courier==chosen)&(ok.promised_min==45)]
walk45_km=s45.distance_km.median();walk45_min=s45.actual_min.median()
fig,ax=plt.subplots(figsize=(8,3.5))
pv.plot(kind='bar',ax=ax)
ax.set(title='При одинаковом обещании пешие тоже опаздывают чаще',xlabel='обещание, мин',ylabel='опозданий, %',ylim=(0,100))
save(fig,'promise')
say(f'Выбраны {chosen}. При 30 мин: {s.late.sum()}/{len(s)} опозданий. П80 {walk_p80} мин; кандидат {fair_promise} мин, уложились бы {(s.actual_min<=fair_promise).sum()}/{len(s)} ({(s.actual_min<=fair_promise).mean():.1%}). При 45 мин медианы расстояния {walk45_km:.1f} км и времени {walk45_min:.1f} мин: маршруты иные. Пересчёт срока не ускоряет курьера.')''')
md('**Вывод по обещанию.** Пилот срока 40 минут имеет опору в исходных маршрутах. Если при сопоставимых маршрутах своевременность не достигает 80% или отказы растут настолько, что маржа падает, рекомендация не поддерживается.')
md('### 4.4. Кофейня KZN-2\nПроверяю разницу внутри курьера; расстояние остаётся возможным смешивающим фактором.')
code('''ok['kzn2']=ok.shop_id=='KZN-2'
a=ok.groupby(['courier','kzn2']).actual_min.median().unstack()
b=ok.groupby(['courier','kzn2']).distance_km.median().unstack()
kzn2_gap=(a[True]-a[False]).to_dict();same_distance=(b[True]-b[False]).round(1).to_dict()
display(pd.DataFrame({'разница времени, мин':kzn2_gap,'разница расстояния, км':same_distance}))
display(ok.groupby(['courier','kzn2']).size())
say(f'Разницы медианного времени KZN-2 минус остальные: {kzn2_gap}. Разницы расстояния {same_distance}; сравнение внутри курьеров ещё не уравнивает погоду, часы и маршруты.')''')
md('**Вывод по KZN-2.** Сравнение условий уточняет картину; причинную вину управляющего по общей доле установить нельзя.')
md('### 4.5. Снег и время\nИсключаю крайние неполные недели. Разница долей и отношение — разные вопросы.')
code('''ok['snow']=ok.weather=='снег'
weeks=ok.set_index('created').resample('W')[['late','snow']].mean().iloc[1:-1]*100
weeks.columns=['late_pct','snow_pct'];r_weeks=round(weeks.late_pct.corr(weeks.snow_pct),2)
fig,ax=plt.subplots(figsize=(9,3.5));weeks.plot(ax=ax)
ax.set(title='В ноябрьские недели появляются снег и больше опозданий',xlabel='неделя заканчивается',ylabel='доставок, %')
save(fig,'weeks')
display(ok.groupby(['courier','snow']).late.agg(['sum','size','mean']))
say(f'Недельная корреляция долей {r_weeks}; полных недель {len(weeks)}. Снег был только в ноябре, поэтому и другие ноябрьские изменения могли объяснять связь.')''')
md('**Вывод по снегу.** Сравнение внутри курьеров не снимает календарное смешение. Нужны сопоставимые снеговые и бесснежные маршруты, даты и часы.')
md('### 4.6. Оценки\nОценки добровольные. Близость долей отвечающих не доказывает одинаковый отбор довольных и недовольных.')
code('''rating_on_time=round(ok.loc[~ok.late,'rating'].mean(),2)
s=ok.loc[ok.delay>10,'rating'].dropna()
rating_late10=round(s.mean(),2);low_share_late10=round((s<=3).mean()*100,1)
t=ok.groupby(pd.cut(ok.delay,[-60,-10,0,10,20,60]),observed=False).rating.agg(rating='mean',n='count')
display(t.round(2));display(ok.groupby('late').rating.apply(lambda x:x.notna().mean()))
fig,ax=plt.subplots(figsize=(8,3.5));bars=ax.bar(t.index.astype(str),t.rating)
ax.bar_label(bars,labels=[f'n={n}' for n in t.n]);ax.set(title='У ответивших при долгом опоздании оценки ниже',xlabel='опоздание, мин (правая граница включена)',ylabel='средняя оценка, балл',ylim=(0,5.5))
save(fig,'ratings')
say(f'Вовремя средняя {rating_on_time}; задержка >10 мин — {rating_late10}, оценок {len(s)}, доля 3 и ниже {low_share_late10}%. Это связь среди ответивших, не доказательство причинности.')''')
md('**Вывод по оценкам.** Предлагаю дополнительную метрику delay>10, сохраняя долю любых нарушений как контроль соблюдения обещания.')
md('### 4.7. Собственные закономерности\nВыбрал размер заказа и короткое расстояние; второе не трактую как эффект расстояния без состава.')
code('''findings=[]
for condition in ['items >= 5','distance_km <= 2']:
    g=ok.query(condition);other=ok.drop(g.index)
    a=round(g.late.mean()*100,1);b=round(other.late.mean()*100,1)
    conclusion=f'{condition}: {g.late.sum()}/{len(g)} ({a}%) против {other.late.sum()}/{len(other)} ({b}%). Возможны различия обещаний, курьеров и маршрутов.'
    findings.append({'группа':condition,'n':len(g),'late_pct':a,'остальные_pct':b,'вывод':conclusion})
    say(conclusion)
    display(ok.assign(inside=ok.index.isin(g.index)).groupby(['courier','inside']).late.agg(['sum','size','mean']))
fig,ax=plt.subplots(figsize=(8,3.5))
x=np.arange(2)
ax.bar(x-.18,[f['late_pct'] for f in findings],width=.36,label='в группе')
ax.bar(x+.18,[f['остальные_pct'] for f in findings],width=.36,label='остальные')
ax.set_xticks(x);ax.set_xticklabels([f['группа'] for f in findings]);ax.legend()
ax.set(title='Крупные заказы и короткие маршруты чаще опаздывают в целом',xlabel='условие группы',ylabel='опозданий, %',ylim=(0,100))
save(fig,'own')''')
md('**Вывод по собственным находкам.** У items>=5 рост доли виден внутри всех типов курьера, но причинную роль размера это не доказывает. Для distance<=2 направление у пеших обратное общему: смесь курьеров и обещаний мешает назначить одно действие по общему сравнению.')
md('### 4.8. Пересчитываемый отчёт\nФункция принимает сырые данные; отсутствие пеших с обещанием 30 минут возвращает None, пустой пригодный период — пустые показатели.')
code(Path('own_report_code.py').read_text().replace('raw=pd.read_csv("deliveries.csv",parse_dates=["created"])','raw=pd.read_csv(DATA/"deliveries.csv",parse_dates=["created"])')+'\nprint(delivery_report(raw))\nprint(delivery_report(raw[raw.created.dt.month==11]))\nprint(delivery_report(raw.iloc[0:0]))\n')
md('**Вывод по функции.** Отчёт воспроизводим для другого периода; fair_promise в этой функции следует публичному контракту про пеших, а выбор целевой группы пилота в анализе сделан вычислением.')
md('## 5. Выводы и рекомендации\n1. Нарушения обещания — 441/1841 (24.0%); неизвестные статусы дают диапазон всей выгрузки 23.5–25.4%.\n2. Для пеших с обещанием 30 минут проверить 40 минут в пилоте с контролем: целевой порог своевременности 80%, дополнительно конверсия и маржа. Это мера честности обещания, а не ускорения.\n3. Крупные заказы и короткие маршруты различаются с остальными; первая связь держится внутри типов курьера, вторая неоднородна. Проверить сборку крупных заказов отдельным пилотом.\n4. Снег связан с опозданиями, но совпадает с ноябрём. Оценки добровольные; выводы о причинах ограничены.\n5. Для решений нужны этапы сборки/ожидания/поездки, нагрузка, маршруты, конверсия и экономика. При отсутствии эффекта в контролируемом пилоте или падении маржи предложение пересмотреть.')
nb=dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},nbformat=4,nbformat_minor=5)
(out/'delivery_delays.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
