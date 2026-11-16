"""Expected verdicts are written before execution; every case keeps its full program."""
import json
from pathlib import Path
D=Path(__file__).parent
T={(x['lesson'].split('/')[-1],x['id']):x for x in json.loads((D/'tasks-before.json').read_text()) if x['kind']=='task'}
P=[]
def p(l,t,name,expected,code=None,suffix='',prepare=''):
 x=T[l,t];P.append(dict(lesson=l,task=t,case=name,expected=expected,code=x['solution']+'\n'+suffix if code is None else code,check=x['check'],setup=x.get('setup'),files=x.get('files',[]),prepare=prepare))

# One independently meaningful correct/error pair in each of fourteen lessons.
p('01-plots','labeled','alternative-aggregate',True,code=T['01-plots','labeled']['solution'].replace('.sum().sort_values(','.agg("sum").sort_values('))
p('01-plots','labeled','wrong-halved-channel-revenue',False,suffix='for patch in ax.patches: patch.set_height(patch.get_height()/2)')
p('02-histograms','five-min','alternative-explicit-edges',True,code=T['02-histograms','five-min']['solution'].replace('bins=24, range=(0, 120)','bins=range(0,121,5)'))
p('02-histograms','five-min','wrong-reversed-bin-counts',False,suffix='heights=[p.get_height() for p in ax.patches]\nfor patch,height in zip(ax.patches,heights[::-1]): patch.set_height(height)')
p('02b-shape','ufa-empty','alternative-reordered-keyed-days',True,suffix='per_day=per_day.iloc[::-1]')
p('02b-shape','ufa-empty','wrong-date-labels-only',False,suffix='per_day.index=per_day.index[::-1]')
p('03-boxplots','slow','alternative-whole-deliveries-reordered',True,suffix='ok=ok.iloc[::-1]')
p('03-boxplots','slow','wrong-flags-only-reordered',False,suffix='ok["slow"]=ok.slow.iloc[::-1].to_numpy()')
p('03b-sigma','sigma-courier','alternative-reordered-rows-columns',True,suffix='spread=spread.iloc[::-1][["iqr","std","mean"]]')
p('03b-sigma','sigma-courier','wrong-courier-labels',False,suffix='spread.index=spread.index[::-1]')
p('04-slices','share-snow','alternative-reordered-whole-groups',True,suffix='ct=ct.iloc[::-1,::-1]')
p('04-slices','share-snow','wrong-crosstab-labels-only',False,suffix='ct.index=ct.index[::-1]')
p('05-time','rolling','alternative-window-aggregation',True,code=T['05-time','rolling']['solution'].replace('.rolling(7).mean()','.rolling(window=7).agg("mean")'))
p('05-time','rolling','wrong-middle-rolling-values',False,suffix='smooth.iloc[6:-1]=0')
p('05b-cohorts','age','alternative-whole-rows-columns-reordered',True,suffix='active=active.iloc[::-1,::-1]')
p('05b-cohorts','age','wrong-cohort-labels-only',False,suffix='active.index=active.index[::-1]')
p('05c-dau-mau','sticky-city','alternative-complete-calendar',True,code=T['05c-dau-mau','sticky-city']['solution'].replace('dau.mean()', 'dau.reindex(pd.date_range("2026-06-01","2026-06-30")).fillna(0).mean()'))
p('05c-dau-mau','sticky-city','equal-value-city-labels-reversed',True,suffix='city_sticky.index=city_sticky.index[::-1]')
p('05c-dau-mau','sticky-city','wrong-unequal-city-labels-only',False,suffix='city_sticky.index=list(city_sticky.index[1:])+list(city_sticky.index[:1])')
zero_city="""import pandas as pd
o=pd.read_csv('preorders.csv');g=pd.read_csv('preorder_guests.csv');ids=set(g.loc[g.city=='Пермь','guest_id']);o=o[~((o.date=='2026-06-07') & o.guest_id.isin(ids))];o.to_csv('preorders.csv',index=False)"""
p('05c-dau-mau','sticky-city','calendar-zero-city-day-correct',True,code=T['05c-dau-mau','sticky-city']['solution'].replace('dau.mean()', 'dau.reindex(pd.date_range("2026-06-01","2026-06-30")).fillna(0).mean()'),prepare=zero_city)
p('05c-dau-mau','sticky-city','calendar-zero-city-day-wrong-ignore',False,prepare=zero_city)
sp=T['06-correlation','spearman']['solution']
p('06-correlation','spearman','alternative-pandas-spearman',True,code=sp.replace('d["distance_km"].rank().corr(d["actual_min"].rank())','d["distance_km"].corr(d["actual_min"],method="spearman")'))
p('06-correlation','spearman','wrong-pearson-as-spearman',False,suffix='r_spearman=r_pearson;diff=0')
missing_pairs="""import pandas as pd
d=pd.read_csv('deliveries.csv').iloc[:8].copy();d['distance_km']=[1,None,2,4,None,3,6,5];d['actual_min']=[10,11,12,15,16,17,80,90];d.to_csv('deliveries.csv',index=False)"""
p('06-correlation','spearman','missing-pairs-pandas-spearman',True,code=sp.replace('d["distance_km"].rank().corr(d["actual_min"].rank())','d["distance_km"].corr(d["actual_min"],method="spearman")'),prepare=missing_pairs)
p('06-correlation','spearman','missing-pairs-complete-before-ranking',True,code=sp.replace('subset=["actual_min"]','subset=["distance_km","actual_min"]'),prepare=missing_pairs)
p('06-correlation','spearman','missing-pairs-wrong-rank-before-dropping',False,prepare=missing_pairs)
p('07-readable','no-pie','alternative-inverted-correct-bars',True,code=T['07-readable','no-pie']['solution'].replace('ax.barh(share.index, share.values)','ax.barh(share.index[::-1], share.values[::-1])\nax.invert_yaxis()'))
p('07-readable','no-pie','wrong-drink-labels-only',False,suffix='ax.set_yticks(ax.get_yticks(),share.index[::-1])')
title=T['07-readable','title']['solution']
p('07-readable','title','alternative-format-string',True,code=title.replace('f"{m.index[0]} — самые медленные: медиана {int(m.iloc[0])} мин"','"{} — самые медленные: медиана {} мин".format(m.index[0],int(m.iloc[0]))'))
p('07-readable','title','wrong-reversed-visual-order',False,code=title.replace('ax.bar(m.index, m.values)','ax.bar(m.index[::-1],m.values[::-1])'))
p('07-readable','title','alternative-reversed-with-inversion',True,code=title.replace('ax.bar(m.index, m.values)','ax.bar(m.index[::-1],m.values[::-1])\nax.invert_xaxis()'))
p('07-readable','title','wrong-label-only',False,suffix='ax.set_xticks(ax.get_xticks(),m.index[::-1])')
p('07-readable','title','wrong-minute-axis',False,suffix='ax.set_ylabel("км")')
p('07c-metrics','funnel-platform','alternative-groupby-unstack',True,code=T['07c-metrics','funnel-platform']['solution'].replace('f.pivot_table(index=["platform", "period"], columns="step", values="session_id", aggfunc="nunique")[steps]','f.groupby(["platform","period","step"])["session_id"].nunique().unstack("step")[steps]'))
p('07c-metrics','funnel-platform','whole-groups-reordered',True,suffix='pay_conv=pay_conv.iloc[::-1]')
p('07c-metrics','funnel-platform','labels-only-reordered',False,suffix='pay_conv.index=pay_conv.index[::-1]')
p('07c-metrics','funnel-platform','wrong-fractional-lost',False,suffix='lost+=0.8')
swap_funnel="""import pandas as pd
f=pd.read_csv('app_funnel.csv');f['platform']=f.platform.replace({'android':'ios','ios':'android'});f.to_csv('app_funnel.csv',index=False)"""
p('07c-metrics','funnel-platform','other-platform-loss-dynamic',True,prepare=swap_funnel)
p('07c-metrics','funnel-platform','other-platform-loss-fixed-104',False,suffix='lost=104',prepare=swap_funnel)
p('08-eda','slice-fn','alternative-aggregate-columns',True,code=T['08-eda','slice-fn']['solution'].replace('df.groupby(by)[col].agg(n="size", mean="mean")','df.groupby(by).agg(n=(col,"size"),mean=(col,"mean"))'))
p('08-eda','slice-fn','wrong-unchecked-counts-and-mean',False,code=T['08-eda','slice-fn']['solution'].replace('return t.sort_values("mean", ascending=False)','t.loc[t.index != "a", "n"] = 7\n    t.loc[t.index == "a", "mean"] *= 1.5\n    return t.sort_values("mean", ascending=False)'))
p('09-project','walkers','alternative-largest-sorted-group',True,code=T['09-project','walkers']['solution'].replace('ok.groupby("courier", sort=True)["late"].mean().idxmax()','ok.groupby("courier")["late"].mean().sort_index().sort_values(ascending=False,kind="stable").index[0]'))
p('09-project','walkers','whole-groups-reordered',True,suffix='pv=pv.iloc[::-1,::-1]')
p('09-project','walkers','labels-only-reordered',False,suffix='pv.columns=pv.columns[::-1]')
cars="""import pandas as pd
d=pd.read_csv('deliveries.csv');d['courier']=d.courier.replace({'пеший':'авто','авто':'пеший'});d.to_csv('deliveries.csv',index=False)"""
p('07-readable','title','new-input-other-leader',True,prepare=cars)
p('07-readable','title','new-input-wrong-fixed-title',False,suffix='ax.set_title("пеший — самые медленные: медиана 37 мин")',prepare=cars)
for name,prep in [('other-leader-cars',cars),('input-row-order',"import pandas as pd\nd=pd.read_csv('deliveries.csv');d.iloc[::-1].to_csv('deliveries.csv',index=False)")]:
 p('09-project','walkers',name,True,prepare=prep)
p('09-project','walkers','wrong-fixed-walkers-on-cars',False,code=T['09-project','walkers']['solution'].replace('group = ok.groupby("courier", sort=True)["late"].mean().idxmax()','group = "пеший"'),prepare=cars)
# Synthetic valid deliveries: tied 50% rates, different quantiles/medians, reverse input order.
tie="""import pandas as pd
d=pd.read_csv('deliveries.csv');rows=[]
for group,values,km in [('пеший',[25,49,40,68],3.0),('вело',[22,43,37,60],2.0),('авто',[20,36,35,52],1.0)]:
 for i,(promise,actual) in enumerate(zip([30,30,45,45],values)):
  r=d.iloc[0].copy();r['courier']=group;r['promised_min']=promise;r['actual_min']=actual;r['distance_km']=km;r['created']=f'2026-10-0{i+1} 12:00:00';rows.append(r)
pd.DataFrame(rows).to_csv('deliveries.csv',index=False)"""
p('09-project','walkers','tie-alphabetical-first-correct',True,prepare=tie)
p('09-project','walkers','tie-wrong-input-first-group',False,code=T['09-project','walkers']['solution'].replace('sort=True','sort=False'),prepare=tie)
p('09-project','clean','alternative-whole-deliveries-reordered',True,suffix='ok=ok.iloc[::-1]')
p('09-project','clean','wrong-content-erased-consistent-derived',False,suffix='ok["courier"]="авто";ok["actual_min"]=ok.promised_min;ok["late"]=False;ok["delay"]=0')
compare=T['02-histograms','compare']['solution']
p('02-histograms','compare','alternative-reverse-group-order',True,code=compare.replace('["вело", "авто"]','["авто", "вело"]'))
p('02-histograms','compare','wrong-zero-density',False,suffix='for patch in ax.patches: patch.set_height(0)')
p('02-histograms','compare','wrong-second-group-counts',False,suffix='for patch in ax.patches[30:]: patch.set_height(1)')
p('02-histograms','compare','wrong-courier-labels',False,suffix='ax.legend(ax.containers,["авто","вело"])')
# Complete empty submission audit counted separately from meaningful examples.
for l,t in sorted(T): p(l,t,'empty-answer',False,code='pass')
(D/'probes-before.json').write_text(json.dumps(P,ensure_ascii=False,indent=2))
print(len(P),'probes',len(P)-len(T),'meaningful',len({x['lesson'] for x in P if x['case']!='empty-answer'}),'lessons')
