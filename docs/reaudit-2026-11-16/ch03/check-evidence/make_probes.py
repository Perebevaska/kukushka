"""Explicit educational contracts; expected verdicts declared before execution."""
import json
from pathlib import Path
D=Path(__file__).parent
T={(x['lesson'].split('/')[-1],x['id']):x for x in json.loads((D/'tasks-before.json').read_text()) if x['kind']=='task'}
P=[]
def p(l,t,case,expected,code=None,suffix='',prepare=''):
 x=T[l,t];P.append(dict(lesson=l,task=t,case=case,expected=expected,code=x['solution']+'\n'+suffix if code is None else code,check=x['check'],setup=x.get('setup'),files=x.get('files',[]),prepare=prepare))
# One distinct correct method and meaningful error per lesson.
p('01-inspect','worst','alternative-count-missing',True,code="import pandas as pd\ndf=pd.read_csv('clients_raw.csv');missing=len(df)-df.count();worst=missing.sort_values().index[-1]")
p('01-inspect','worst','wrong-no-missing',False,suffix='missing[:]=0')
p('02-missing','flag','alternative-where',True,code="import pandas as pd\ndf=pd.read_csv('clients_raw.csv',na_values=['—'],thousands=' ');df['bonus_missing']=df.bonus.isna();df['bonus']=df.bonus.where(df.bonus.notna(),0)")
p('02-missing','flag','wrong-moved-missing-flags',False,suffix="df['bonus_missing']=df.bonus_missing.iloc[::-1].to_numpy();df.loc[df.bonus_missing,'bonus']=0")
p('02-missing','flag','wrong-erase-known-bonuses',False,suffix="df['bonus']=0")
p('02-missing','reconcile','wrong-relabel-clients',False,suffix="by_client.index=list(by_client.index[:-1][::-1])+[by_client.index[-1]]")
p('03-types','bonus-num','alternative-map-parser',True,code="import pandas as pd\ndf=pd.read_csv('clients_raw.csv');bonus=df.bonus.map(lambda x: pd.to_numeric(str(x).replace(' ',''),errors='coerce'));lost=df.loc[bonus.isna() & df.bonus.notna(),'bonus'].unique().tolist()")
p('03-types','bonus-num','wrong-fill-missing-zero',False,suffix='bonus=bonus.fillna(0)')
p('03-types','age','irrelevant-intermediate-after-correct-median',True,suffix='age[:]=0')
p('03-types','age','alternative-other-intermediate-name',True,code=T['03-types','age']['solution'].replace('born','dates'))
p('03-types','age','wrong-median',False,suffix='median_age+=1')
p('04-duplicates','drop-exact','alternative-boolean-mask',True,code="import pandas as pd\ndf=pd.read_csv('clients_raw.csv');clean=df.loc[~df.duplicated()].reset_index(drop=True)")
p('04-duplicates','drop-exact','wrong-keep-first-N-rows',False,code="import pandas as pd\ndf=pd.read_csv('clients_raw.csv');clean=df.iloc[:len(df.drop_duplicates())].reset_index(drop=True)")
p('04-duplicates','norm-id','wrong-one-card-for-all',False,suffix="df['client_id']='C1000'")
p('04-duplicates','keep-last','wrong-discard-name-and-city',False,suffix="clients[['name','city']]=None")
p('04-duplicates','versions','wrong-discard-version-content',False,suffix="versions['name']=None")
p('04-duplicates','shops-ref','wrong-shop-address',False,suffix="shops['shop_address']='неверный адрес'")
p('05-strings','phone10','alternative-regex-extraction',True,code="import pandas as pd\ndf=pd.read_csv('clients_raw.csv');d=df.phone.str.replace(r'\\D','',regex=True);df['phone10']=d.str.extract(r'^(?:[78])?(\\d{10})$',expand=False);n_bad=df.phone10.dropna().str.len().ne(10).sum()")
p('05-strings','phone10','unvalidated-matches-original-fixture',True,code=T['05-strings','phone10']['solution'].replace("digits.where(digits.str.fullmatch(r\"[78]?\\d{10}\"))",'digits'))
phone_fixture="import pandas as pd\nd=pd.read_csv('clients_raw.csv');d.loc[0,'phone']='+7 912 345-67-89 доб.12';d.loc[1,'phone']='29123456789';d.to_csv('clients_raw.csv',index=False)"
p('05-strings','phone10','wrong-unvalidated-truncation-changed-input',False,code=T['05-strings','phone10']['solution'].replace("digits.where(digits.str.fullmatch(r\"[78]?\\d{10}\"))",'digits'),prepare=phone_fixture)
p('05-strings','phone10','validated-changed-input',True,prepare=phone_fixture)
p('06-categories','check-size','alternative-conditional-expression',True,code="import pandas as pd\ndef check_size(a): return 'малый' if a<300 else 'крупный' if a>=600 else 'средний'\ndf=pd.read_csv('orders_3m.csv');sizes=df.amount.map(check_size).value_counts().to_dict()")
p('06-categories','check-size','wrong-boundary-300',False,code=T['06-categories','check-size']['solution'].replace('amount < 300','amount <= 300'))
p('07-anomalies','mask-bonus','alternative-where',True,code=T['07-anomalies','mask-bonus']['solution'].replace('df["bonus"].mask((df["bonus"] < 0) | (df["bonus"] > 10_000))','df["bonus"].where(df["bonus"].between(0,10_000))'))
p('07-anomalies','mask-bonus','wrong-zero-outliers',False,code=T['07-anomalies','mask-bonus']['solution'].replace('> 10_000))','> 10_000),0)'))
p('08-pipeline','log','alternative-groupby-latest',True,code="""import pandas as pd
def clean_with_log(raw):
 d=raw.loc[~raw.duplicated()].copy(); n1=len(d);d['client_id']=d.client_id.str.strip().str.upper();n2=len(d)
 d=d.sort_values('signup_date').groupby('client_id',sort=False).tail(1)
 return d,[('загрузка',len(raw)),('копии',n1),('номера',n2),('версии',len(d))]
df,log=clean_with_log(pd.read_csv('clients_raw.csv'))""")
p('08-pipeline','log','wrong-log-preserved-but-values-erased',False,code=T['08-pipeline','log']['solution'].replace('return df, log',"df['city']=None\n    return df, log"))
p('08-pipeline','log','wrong-log-preserved-but-old-versions',False,code=T['08-pipeline','log']['solution'].replace('keep="last"','keep="first"'))
p('08-pipeline','save','alternative-date-after-reading',True,code="import pandas as pd\nclients.to_csv('clients_clean.csv',index=False);back=pd.read_csv('clients_clean.csv');back['signup_date']=pd.to_datetime(back.signup_date)")
p('08-pipeline','save','wrong-values-in-file',False,code="import pandas as pd\nclients.assign(city='Москва').to_csv('clients_clean.csv',index=False);back=pd.read_csv('clients_clean.csv',parse_dates=['signup_date'])")
p('08-pipeline','save','wrong-values-only-in-back',False,suffix="back['city']='Москва'")
p('08-pipeline','save','wrong-index-in-file-only',False,code="import pandas as pd\nclients.to_csv('clients_clean.csv');back=pd.read_csv('clients_clean.csv',index_col=0,parse_dates=['signup_date'])")
p('08-pipeline','january','wrong-cut-gor-prefix-from-real-name',False,code=T['08-pipeline','january']['solution'].replace('.str.removeprefix("гор.")','.str.replace(r"^гор.\\s*", "",regex=True)'))
p('09-project','clean','alternative-latest-groupby',True,code=T['09-project','clean']['solution'].replace('.drop_duplicates(subset=["client_id"], keep="last")','.groupby("client_id",sort=False).tail(1)'))
p('09-project','clean','wrong-name-missing',False,suffix="clients['name']=None")
p('09-project','clean','wrong-returned-phone-values',False,code=T['09-project','clean']['solution'].replace('return digits.where(ok).str[-10:]','return digits.where(ok).str[-10:].where(~ok, "0000000000")'))
p('09-project','clean','wrong-log',False,suffix="log['анкет']+=1")
p('09-project','age','alternative-reordered-whole-rows',True,suffix='clients=clients.iloc[::-1]')
p('09-project','age','wrong-reordered-age-only',False,suffix="clients['age']=clients.age.iloc[::-1].to_numpy()")
p('09-project','guests','alternative-reordered-whole-rows',True,suffix='guests=guests.iloc[::-1]')
p('09-project','guests','wrong-reordered-revenue-only',False,suffix="guests['revenue']=guests.revenue.iloc[::-1].to_numpy()")
p('09-project','guests','wrong-count-cups',False,code=T['09-project','guests']['solution'].replace('orders=("order_id", "count")','orders=("qty", "sum")'))
p('09-project','sources','alternative-reordered-columns',True,suffix="by_source=by_source[['avg_revenue','clients','active_pct']]")
p('09-project','sources','wrong-source-labels',False,suffix='by_source.index=by_source.index[::-1]')
p('09-project','sources','wrong-one-group-missing',False,suffix="by_source.iloc[-1,2]=float('nan')")
p('09-project','age-money','alternative-reordered-columns-and-rows',True,suffix="by_age=by_age.iloc[::-1][['avg_revenue','guests_n','avg_orders']]")
p('09-project','age-money','wrong-group-labels',False,suffix='by_age.index=by_age.index[::-1]')
p('09-project','report','alternative-mean-activity',True,code=T['09-project','report']['solution'].replace('(guests["orders"] > 0).mean()','guests["orders"].gt(0).sum()/len(guests)'))
p('09-project','report','wrong-fixed-CRM-file',False,code=T['09-project','report']['solution'].replace('def report(raw, orders):','def report(raw, orders):\n    raw=pd.read_csv("clients_raw.csv")'))
p('09-project','report','alternative-no-rounding-non-promised-median',True,suffix='')
p('09-project','report','empty-orders-period',True,prepare="import pandas as pd\nd=pd.read_csv('orders_3m.csv');d.iloc[:0].to_csv('orders_3m.csv',index=False)")
p('08-pipeline','log','wrong-fixed-source-file',False,code=T['08-pipeline','log']['solution'].replace('def clean_with_log(raw):','def clean_with_log(raw):\n    raw=pd.read_csv(\"clients_raw.csv\")'))
# Priority Excel pair: different shifts and empty values. Full rows retain keyed identity.
shift="""import openpyxl
w=openpyxl.load_workbook('zerno_finance.xlsx')
for name,n in [('План',1),('Факт',4)]: w[name].insert_rows(1,n)
w.save('zerno_finance.xlsx')"""
p('03b-excel','auto-header','different-shifts-and-empty-months',True,prepare=shift)
p('03b-excel','auto-header','alternative-reordered-columns-rows',True,suffix="pf=pf.iloc[::-1][['факт','план']]")
p('03b-excel','auto-header','wrong-fixed-header-positions',False,code=T['03b-excel','auto-header']['solution'].replace('row = sheet[sheet[0] == "Код"].index[0]','row = {"План":3,"Факт":4}[name]'))
p('03b-excel','auto-header','wrong-all-empty-NaN',False,code=T['03b-excel','auto-header']['solution'].replace('sum(axis=1)','sum(axis=1,min_count=1)'))
p('03b-excel','auto-header','wrong-shop-labels',False,suffix='pf.index=pf.index[::-1]')
p('03b-excel','auto-header','wrong-all-zero',False,suffix='pf[:]=0')
# Completely missing answer on every task: no accidental credit, no student side effects.
for l,t in sorted(T): p(l,t,'empty-answer',False,code='pass')
(D/'probes-before.json').write_text(json.dumps(P,ensure_ascii=False,indent=2)); print(len(P))
