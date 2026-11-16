import json
from pathlib import Path
n=json.loads(Path('ch04-project-template.ipynb').read_text());cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=[s]))
def code(s):cells.append(dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=[s]))
md('# Опоздания доставок: решение для руководителя')
first=''.join(n['cells'][1]['source'])
first=first.replace('import sys','import sys\nimport math\nimport numpy as np\nimport matplotlib')
first+='''
RANDOM_STATE=42
FIGURES=Path('figures-'+Path(DELIVERIES_FILE).stem)
FIGURES.mkdir(exist_ok=True)
def say(text):
    display(Markdown('**Вывод.** '+text))
def save(fig,name):
    fig.tight_layout()
    fig.savefig(FIGURES/(name+'.png'),dpi=130,bbox_inches='tight')
    plt.show()
def prepare(raw):
    t=raw[raw.actual_min.between(1,299)].copy()
    t['late']=t.actual_min>t.promised_min
    t['delay']=t.actual_min-t.promised_min
    t['hour']=t.created.dt.hour
    return t
def delivery_report(raw):
    t=prepare(raw)
    if t.empty:
        return dict(late_pct=None,worst_courier=None,worst_shop=None,peak_hours=[],fair_promise=None)
    chosen=t.groupby('courier').late.mean().sort_index().idxmax()
    s=t[(t.courier==chosen)&(t.promised_min==30)].actual_min
    h=t.groupby('hour').late.agg(['mean','size'])
    return dict(late_pct=round(t.late.mean()*100,1),worst_courier=chosen,worst_shop=t.groupby('shop_id').late.mean().sort_index().idxmax(),peak_hours=h[(h['size']>=50)&(h['mean']>.25)].index.tolist(),fair_promise=None if s.empty else math.ceil(s.quantile(.8)/5)*5)
ok=prepare(raw)
report=delivery_report(raw)
chosen=report['worst_courier']
period=f'{raw.created.min():%d.%m.%Y}–{raw.created.max():%d.%m.%Y}'
context=f'{DELIVERIES_FILE}; {period}'
'''
code(first)
md('## Цель и главное\nВыбрать подгруппу для пилота честного обещания и проверить, можно ли уменьшить опоздания. Доля рассчитывается по пригодному фактическому времени. Обещание не меняет время поездки; экономика решения требует отдельного наблюдения.')
code('''g=ok[ok.courier==chosen]
s30=g[g.promised_min==30]
excluded=len(raw)-len(ok)
lower=ok.late.sum()/len(raw)*100
upper=(ok.late.sum()+excluded)/len(raw)*100
say(f'{context}. Опоздали {ok.late.sum()}/{len(ok)} пригодных доставок ({ok.late.mean():.1%}); неизвестны статусы {excluded}/{len(raw)}. Для всех {len(raw)} доставок крайние сценарии {lower:.1f}–{upper:.1f}%. Наибольшая доля у {chosen}: {g.late.sum()}/{len(g)} ({g.late.mean():.1%}). При одинаковом обещании 30 мин в этой группе {s30.late.sum()}/{len(s30)} ({s30.late.mean():.1%}); кандидат срока по п80 этой подгруппы {report["fair_promise"]} мин. Это результат текущей выгрузки, не причинная оценка работы курьеров.')
display(ok.groupby(['promised_min','courier']).late.agg(опоздали='sum',доставок='size',доля='mean').round(3))''')
md('**Вывод по главному.** Выбранная группа и числа вычислены из текущего файла. Пилот ниже задаёт подгруппу явно; разные исходные обещания нельзя смешать в одно обещание.')
md('## Данные и предобработка\nОдна строка — доставка. Время вне 1–299 и пропуски исключены из расчёта основной доли; их статус остаётся неизвестным. При смене выгрузки применимость этого диапазона надо подтвердить заново.')
code('''log={'всего':len(raw),'без времени':int(raw.actual_min.isna().sum()),'невозможное время':int((raw.actual_min.notna()&~raw.actual_min.between(1,299)).sum()),'осталось':len(ok)}
display(pd.Series(log,name='доставок').to_frame())
print('Полные дубли:',raw.duplicated().sum())
loss=raw[~raw.index.isin(ok.index)].groupby('courier').size()
quality=pd.DataFrame({'опоздали':ok.groupby('courier').late.sum(),'все':raw.groupby('courier').size(),'неизвестно':loss}).fillna(0)
quality['нижняя_%']=quality['опоздали']/quality['все']*100
quality['верхняя_%']=(quality['опоздали']+quality['неизвестно'])/quality['все']*100
display(quality.round(1))
say(f'{context}. Пригодны {len(ok)}/{len(raw)}. Границы {lower:.1f}–{upper:.1f}% — сценарии неизвестных статусов, не доверительный интервал. Оценок {ok.rating.notna().sum()}/{len(ok)}; отсутствие отзыва не заменяю оценкой.')''')
md('**Вывод о качестве.** Доля среди пригодных и пределы всей выгрузки отвечают на разные вопросы. Таблица показывает возможную концентрацию исключений по типам.')
md('## Масштаб и сравнение групп\n### 1. Масштаб задержек')
code('''late_pct=round(ok.late.mean()*100,1)
late_median=ok.loc[ok.late,'delay'].median();p90_late=ok.loc[ok.late,'delay'].quantile(.9)
fig,ax=plt.subplots(figsize=(9,3.5))
ax.hist(ok.delay,bins=16,range=(-40,40),color='lightgray');ax.axvline(0,color='tab:red')
ax.set(title=f'{context}: опоздали {ok.late.sum()}/{len(ok)} ({late_pct}%)',xlabel='опоздание, мин; отрицательное — раньше',ylabel='доставок')
save(fig,'scale')
say(f'Среди {ok.late.sum()} опоздавших медиана задержки {late_median:.1f} мин, п90 {p90_late:.1f} мин. Вне окна −40…40: {((ok.delay < -40)|(ok.delay>40)).sum()}/{len(ok)} доставок. Ни квантиль, ни крайний сценарий не обещают будущее качество.')''')
md('**Вывод по масштабу.** Сравнивать сроки надо с обещанием конкретной доставки, а не со средним фактом всей сети.')
md('### 2. Факторы и одинаковое обещание')
code('''r={}
for col in ['courier','weather','shop_id','items','hour']:
    a=ok.groupby(col).late.agg(['mean','size'])
    s=a[a['size']>=50]['mean']
    r[col]=round((s.max()-s.min())*100,1)
ranking=pd.Series(r).sort_values(ascending=False);top_factor=ranking.index[0]
display(ranking)
pv=ok.pivot_table(index='promised_min',columns='courier',values='late',aggfunc='mean')*100
counts=ok.pivot_table(index='promised_min',columns='courier',values='late',aggfunc='size')
fig,ax=plt.subplots(figsize=(9,4));pv.plot(kind='bar',ax=ax)
ax.set(title=f'{context}: доли при одинаковом обещании',xlabel='обещано, мин',ylabel='опозданий, %',ylim=(0,105))
for container,col in zip(ax.containers,pv.columns):
    ax.bar_label(container,labels=[f'n={v:.0f}' if pd.notna(v) else '' for v in counts[col]],fontsize=8)
ax.legend(title='тип курьера');save(fig,'promise')
say(f'Размах максимален у {top_factor}: {ranking.iloc[0]:.1f} п.п. Самая высокая общая доля у {chosen}; разница при одинаковом обещании видна в таблице первого раздела. Маршруты, часы и состав ещё не уравнены. Размер групп и число категорий меняют размах.')''')
md('**Вывод по факторам.** Общая доля помогает выбрать, с чего начать; сравнение при одном обещании убирает только одно различие.')
md('### 3. Два вопроса о новом сроке\nОбщий отчёт всегда считает худшую группу с обещанием 30 минут. Отдельное исследование берёт наиболее частое обещание выбранной группы; это может оказаться 45 минут. Эти пороги нельзя взаимозаменять.')
code('''walk_p80=s30.actual_min.quantile(.8)
fair_promise=report['fair_promise']
if fair_promise is None:
    say(f'{context}: у {chosen} нет подгруппы с обещанием 30 минут — fair_promise=None.')
else:
    say(f'{context}: отчёт, {chosen}, исходное обещание 30 мин, п80 {walk_p80:.1f}, кандидат {fair_promise} мин; уложились бы {(s30.actual_min<=fair_promise).sum()}/{len(s30)} ({(s30.actual_min<=fair_promise).mean():.1%}).')
pilot_original=int(g.promised_min.mode().iloc[0])
pilot=g[g.promised_min==pilot_original]
pilot_p80=pilot.actual_min.quantile(.8)
pilot_promise=math.ceil(pilot_p80/5)*5
other=ok[(ok.courier!=chosen)&(ok.promised_min==pilot_original)]
s45=g[g.promised_min==45]
walk45_km=s45.distance_km.median();walk45_min=s45.actual_min.median()
say(f'Собственная подгруппа пилота: {chosen}, обещали {pilot_original} мин; опоздали {pilot.late.sum()}/{len(pilot)} ({pilot.late.mean():.1%}), остальные курьеры с тем же обещанием {other.late.sum()}/{len(other)} ({other.late.mean():.1%}). П80 факта {pilot_p80:.1f} мин, кандидат {pilot_promise} мин: уложились бы {(pilot.actual_min<=pilot_promise).sum()}/{len(pilot)} ({(pilot.actual_min<=pilot_promise).mean():.1%}). При обещании 45 мин у {chosen} медианы расстояния {walk45_km:.1f} км и факта {walk45_min:.1f} мин (n={len(s45)}).')''')
md('**Вывод по сроку.** Это пересчёт на исходных маршрутах. Смена обещания может поменять спрос и состав маршрутов; для нового спроса п80 не гарантирован.')
md('### 4. KZN-2 внутри курьеров')
code('''ok['kzn2']=ok.shop_id=='KZN-2'
a=ok.groupby(['courier','kzn2']).actual_min.median().unstack()
b=ok.groupby(['courier','kzn2']).distance_km.median().unstack()
kzn2_gap=(a[True]-a[False]).to_dict();same_distance=(b[True]-b[False]).round(1).to_dict()
display(pd.DataFrame({'разница времени, мин':kzn2_gap,'разница расстояния, км':same_distance}))
display(ok.groupby(['courier','kzn2']).size())
say(f'{context}. Разница медиан KZN-2 минус остальные: {kzn2_gap}; расстояния {same_distance}. Состав курьеров учтён, условия внутри них ещё различаются.')''')
md('**Вывод по KZN-2.** Разницы не доказывают причину задержки в кофейне. Запросить этапы сборки, ожидания и поездки.')
md('### 5. Недели и снег')
code('''ok['snow']=ok.weather=='снег'
weeks=ok.set_index('created').resample('W')[['late','snow']].mean().iloc[1:-1]*100
weeks.columns=['late_pct','snow_pct'];r_weeks=round(weeks.late_pct.corr(weeks.snow_pct),2)
weekly_n=ok.set_index('created').resample('W').size().iloc[1:-1]
fig,ax=plt.subplots(figsize=(10,4));weeks.rename(columns={'late_pct':'опоздания','snow_pct':'снег'}).plot(ax=ax)
ax.set(title=f'{context}: доли по полным неделям, n={weekly_n.min()}…{weekly_n.max()} за неделю',xlabel='воскресенье окончания недели',ylabel='доставок, %')
save(fig,'weeks')
display(pd.concat([weeks,weekly_n.rename('доставок')],axis=1).round(1))
say(f'Корреляция недельных долей {r_weeks}; недель {len(weeks)}. Первая и последняя неполные исключены; снег совпадает с ноябрём, поэтому календарные изменения остаются альтернативой.')''')
md('**Вывод по неделям.** График описывает совместную динамику, а не причинный эффект погоды.')
md('### 6. Отзывы')
code('''rating_on_time=round(ok.loc[~ok.late,'rating'].mean(),2)
s=ok.loc[ok.delay>10,'rating'].dropna();rating_late10=round(s.mean(),2);low_share_late10=round((s<=3).mean()*100,1)
t=ok.groupby(pd.cut(ok.delay,[-60,-10,0,10,20,60]),observed=False).rating.agg(rating='mean',n='count')
fig,ax=plt.subplots(figsize=(9,4));bars=ax.bar(t.index.astype(str),t.rating)
ax.bar_label(bars,labels=[f'n={v}' for v in t.n]);ax.set(title=f'{context}: балл среди {ok.rating.notna().sum()} ответивших',xlabel='опоздание, мин; правая граница включена',ylabel='средняя оценка, балл',ylim=(0,5.5))
save(fig,'ratings')
say(f'Вовремя средняя оценка {rating_on_time}; при задержке >10 мин {rating_late10}, n={len(s)} полученных оценок, доля ≤3: {(s<=3).sum()}/{len(s)} ({low_share_late10}%). Среди всех пригодных задержка >10 мин: {(ok.delay>10).sum()}/{len(ok)} ({(ok.delay>10).mean():.1%}). Одинаковая частота отклика не гарантирует одинаковый состав ответивших; на всех гостей средние не переношу.')''')
md('**Вывод по отзывам.** Отзывы и задержки могут иметь общие причины; дополнительная метрика delay>10 относится ко всем пригодным доставкам независимо от отзыва.')
md('## Две собственные находки\nСохраняю исходные условия items>=5 и distance<=2. Проверяю пороги n>=50 в обеих группах и разницу не менее 5 п.п. Заранее выбранное условие может не пройти на новом составе — не подменяю его другим.')
code('''findings=[]
for condition in ['items >= 5','distance_km <= 2']:
    a=ok.query(condition);b=ok.drop(a.index)
    x=a.late.mean()*100;y=b.late.mean()*100
    valid=len(a)>=50 and len(b)>=50 and abs(x-y)>=5
    findings.append({'группа':condition,'n':len(a),'late_pct':round(x,1),'остальные_pct':round(y,1),'valid':valid,'вывод':f'{condition}: {a.late.sum()}/{len(a)} против {b.late.sum()}/{len(b)}; условия зачёта {valid}'})
    say(f'{context}; {condition}: {a.late.sum()}/{len(a)} ({x:.1f}%) против {b.late.sum()}/{len(b)} ({y:.1f}%). Разница {x-y:.1f} п.п.; условия находки выполнены: {valid}.')
    display(ok.assign(inside=ok.index.isin(a.index)).groupby(['courier','inside']).late.agg(опоздали='sum',доставок='size',доля='mean').round(3))
fig,ax=plt.subplots(figsize=(10,4));x=np.arange(2)
a=ax.bar(x-.18,[f['late_pct'] for f in findings],width=.36,label='в группе')
b=ax.bar(x+.18,[f['остальные_pct'] for f in findings],width=.36,label='вне группы')
ax.bar_label(a,labels=[f'n={f["n"]}' for f in findings]);ax.bar_label(b,labels=[f'n={len(ok)-f["n"]}' for f in findings])
ax.set_xticks(x);ax.set_xticklabels([f['группа'] for f in findings]);ax.legend()
ax.set(title=f'{context}: повторная проверка двух условий',xlabel='условие',ylabel='опозданий, %',ylim=(0,105));save(fig,'own')
say('Доля по коротким маршрутам неоднородна внутри типов курьера. Сравнение общей доли не изолирует расстояние: различаются обещания и распределение курьеров. Для размера заказа также остаются время, погода и состав. Если условия зачёта не выполнены, исходная находка на новом составе не подтверждается.')''')
md('**Вывод по находкам.** Направление и пригодность результата определяются текущими вычислениями выше. Два разных признака ещё не означают два независимых причинных механизма.')
md('## Выводы и рекомендации\nДействие, пределы переносимости и условие отказа.')
code('''say(f'{context}. Предлагаю контролируемый пилот для {chosen} с исходным обещанием {pilot_original} мин: кандидат {pilot_promise} мин; исходная опора {(pilot.actual_min<=pilot_promise).sum()}/{len(pilot)} ({(pilot.actual_min<=pilot_promise).mean():.1%}). Требовать не менее 80% своевременных доставок на сопоставимых маршрутах и контролировать конверсию, отказы и маржу. Если своевременность ниже 80%, либо маржа падает из-за отказов, отказаться от масштабирования срока. Для реального ускорения отдельно проверить перераспределение нагрузки в случайно выбранных сопоставимых сменах и сравнить факт времени/задержек с контролем; если факт не улучшается либо ухудшаются другие группы, отказаться от перераспределения. Изменение названия обещания само по себе не ускоряет доставку.')
failed=[f['группа'] for f in findings if not f['valid']]
say(f'Не прошли прежние пороги собственных находок на этой выгрузке: {failed or "нет"}. Границы неизвестных статусов и добровольный отбор отзывов остаются. Порог времени 1–299 и п80 требуют проверки для нового процесса. fair_promise общего отчёта = {report["fair_promise"]} мин для {chosen}/30; собственный кандидат {pilot_promise} мин для {chosen}/{pilot_original}. Период и подгруппа обязательны рядом с числом.')
print('Пустой период:',delivery_report(raw.iloc[:0]))''')
for i,c in enumerate(cells):c['id']=f'retest-{i:03d}'
n['cells']=cells
Path('delivery_delays.ipynb').write_text(json.dumps(n,ensure_ascii=False,indent=1))
n['cells'][1]['source']=[first.replace('DELIVERIES_FILE = "deliveries.csv"','DELIVERIES_FILE = "deliveries_branch.csv"')]
Path('delivery_branch.ipynb').write_text(json.dumps(n,ensure_ascii=False,indent=1))
