import json
from pathlib import Path
D=Path(__file__).parent
T={(x['lesson'].split('/')[-1],x['id']):x for x in json.loads((D/'tasks-before.json').read_text()) if x['kind']=='task'}
P=[]
def p(lesson,task,case,expected,code=None,suffix='',prepare=''):
 t=T[lesson,task]; P.append(dict(lesson=lesson,task=task,case=case,expected=expected,code=code if code is not None else t['solution']+'\n'+suffix,check=t['check'],setup=t.get('setup'),files=t.get('files',[]),prepare=prepare))
p('09-project','shops','alternative-map-and-key-sort',True,code='''import pandas as pd
rev = full.groupby('shop_id')['amount'].sum()
meta = full.drop_duplicates('shop_id').set_index('shop_id')
by_shop = pd.DataFrame({'city': rev.index.map(meta.city), 'revenue': rev, 'seats': rev.index.map(meta.seats)}, index=rev.index)
by_shop['per_seat'] = (by_shop.revenue/by_shop.seats).round()
by_shop = by_shop.sort_values(['per_seat','revenue'],ascending=False)
leader = by_shop.index[0]
leader_by_revenue = rev.nlargest(1).index[0]''')
p('09-project','shops','wrong-per-seat-plus-1000',False,suffix="by_shop['per_seat'] += 1000")
p('09-project','shops','wrong-shop-labels',False,suffix="by_shop.index = list(reversed(by_shop.index))")
p('09-project','shops','wrong-unsorted',False,suffix="by_shop = by_shop.sort_values('per_seat')")
p('09-project','shops','reordered-shops',True,prepare="import pandas as pd\ns=pd.read_csv('shops.csv');s.iloc[::-1].to_csv('shops.csv',index=False)")
# Minimal authorized fixture: two equal revenue leaders, one per-seat leader, qty>1.
fixture="""import pandas as pd
s=pd.read_csv('shops.csv'); s.loc[s.shop_id=='PRM-1','seats']=10; s.loc[s.shop_id=='KZN-1','seats']=30;s.iloc[::-1].to_csv('shops.csv',index=False)
d=pd.read_csv('orders_3m.csv').iloc[:3].copy(); d['shop_id']=['PRM-1','KZN-1','KZN-1'];d['amount']=[900,600,300];d['qty']=[3,2,1];d['order_id']=[1,2,3];d.to_csv('orders_3m.csv',index=False)"""
p('09-project','shops','tie-revenue-any-leader',True,suffix="leader_by_revenue='KZN-1'",prepare=fixture)
p('09-project','shops','tie-wrong-revenue-leader',False,suffix="leader_by_revenue='UFA-1'",prepare=fixture)
p('09-project','shops','tie-wrong-denominator',False,suffix="by_shop['per_seat']=(by_shop['revenue']/by_shop['revenue'].sum()).round()",prepare=fixture)
p('09-project','margin','alternative-weighted-formula',True,code="""import pandas as pd
x=full.assign(total_cost=full.cost_s*full['size'].map({'S':1,'M':1.25,'L':1.5})*full.qty)
g=x.groupby('category').agg(revenue=('amount','sum'),cost=('total_cost','sum'))
margin=(100-100*g.cost/g.revenue).round(1).sort_index(ascending=False)""")
p('09-project','margin','wrong-ignore-qty',False,code="""full['cost']=full.cost_s*full['size'].map({'S':1,'M':1.25,'L':1.5})
g=full.groupby('category')[['amount','cost']].sum()
margin=(100*(g.amount-g.cost)/g.amount).round(1)""")
p('09-project','margin','wrong-denominator-cost',False,code="""full['cost']=full.cost_s*full['size'].map({'S':1,'M':1.25,'L':1.5})*full.qty
g=full.groupby('category')[['amount','cost']].sum()
margin=(100*(g.amount-g.cost)/g.cost).round(1)""")
p('09-project','margin','wrong-category-labels',False,suffix="margin.index=list(reversed(margin.index))")
p('05-merge','margin','alternative-map',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv'); m=pd.read_csv('menu.csv').set_index('drink')
df['cost']=df.drink.map(m.cost_s)*df['size'].map({'S':1,'M':1.25,'L':1.5})*df.qty
g=df.groupby('drink')[['amount','cost']].sum();best_margin=(1-g.cost/g.amount).idxmax()""")
p('05-merge','margin','wrong-ignore-qty',False,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');menu=pd.read_csv('menu.csv')
full=df.merge(menu,on='drink')
full['cost']=full.cost_s*full['size'].map({'S':1,'M':1.25,'L':1.5})
g=full.groupby('drink')[['amount','cost']].sum()
best_margin=(100*(g.amount-g.cost)/g.amount).idxmax()""")
p('05-merge','margin','wrong-profit-rubles',False,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');menu=pd.read_csv('menu.csv')
full=df.merge(menu,on='drink');full['cost']=full.cost_s*full['size'].map({'S':1,'M':1.25,'L':1.5})*full.qty
g=full.groupby('drink')[['amount','cost']].sum();best_margin=(g.amount-g.cost).idxmax()""")
p('05-merge','per-seat','wrong-revenue-only',False,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv'); best_per_seat=df.groupby('shop_id').amount.sum().idxmax()""")
p('05-merge','city','wrong-merge-assign-first-city',False,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');shops=pd.read_csv('shops.csv')
full=df.assign(city=shops.city.iloc[0],seats=shops.seats.iloc[0])""")
p('05-merge','all-shops','wrong-other-shop-revenue',False,suffix="report.loc[report.shop_id=='KZN-1','revenue']=0")
p('04-groupby','shares','alternative-crosstab',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');r=df.pivot_table(index='drink',values='amount',aggfunc='sum')['amount']
share=(100*r/r.sum()).round(1).sort_values(ascending=False);top3=share.index[:3].tolist()""")
p('04-groupby','shares','wrong-nonleader-all-zero',False,suffix="share.iloc[1:]=0")
p('04-groupby','two-keys','wrong-only-delivery-groups',False,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');by_pair=df[df.channel=='доставка'].groupby(['shop_id','channel']).amount.sum();kzn1_delivery=by_pair[('KZN-1','доставка')]""")
p('07a-sql-python','sqlite-read','correct-single-quote-cat',True,code="""import pandas as pd, sqlite3
con=sqlite3.connect('zerno.db');cat='еда'
food=pd.read_sql_query('SELECT name, price FROM menu WHERE category = ? ORDER BY price DESC',con,params=(cat,));con.close()""")
p('07a-sql-python','sqlite-read','wrong-zero-price',False,suffix="food['price']=0")
p('06-dates','mom-net','wrong-calendar-index',False,suffix="monthly.index=monthly.index+pd.DateOffset(months=1)")
p('06-dates','mom-net','wrong-last-growth',False,suffix="growth.iloc[-1]=0")
p('05-merge','city','alternative-join-reversed-result',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');shops=pd.read_csv('shops.csv')
full=df.join(shops.set_index('shop_id'),on='shop_id').iloc[::-1]""")
p('05-merge','all-shops','alternative-map-reversed-shops',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');shops=pd.read_csv('shops.csv')
rev=df.groupby('shop_id').amount.sum()
report=shops[['shop_id','city']].iloc[::-1].copy();report['revenue']=report.shop_id.map(rev).fillna(0)""")
p('05-merge','per-seat','alternative-map-reversed-shops',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');shops=pd.read_csv('shops.csv').iloc[::-1]
rev=df.groupby('shop_id').amount.sum();rates=rev/rev.index.map(shops.set_index('shop_id').seats)
best_per_seat=rates.idxmax()""")
p('04-groupby','two-keys','alternative-dataframe-groupby',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');by_pair=df.groupby(['shop_id','channel'],as_index=False).agg(revenue=('amount','sum'))
kzn1_delivery=by_pair.loc[(by_pair.shop_id=='KZN-1')&(by_pair.channel=='доставка'),'revenue'].iloc[0]""")
p('04-groupby','shares','wrong-share-labels',False,suffix="share.index=list(reversed(share.index))")
p('04-groupby','two-keys','wrong-pair-labels',False,suffix="by_pair.index=by_pair.index[::-1]")
p('07a-sql-python','sqlite-read','alternative-named-param',True,code="""import sqlite3 as sql, pandas as pd
cat='еда'
con=sql.connect('zerno.db')
food=pd.read_sql_query('SELECT name, price FROM menu WHERE category = :kind ORDER BY price DESC',con,params={'kind':cat});con.close()""")
p('07a-sql-python','sqlite-read','correct-another-category',True,code="""import sqlite3, pandas as pd
cat='не кофе'
con=sqlite3.connect('zerno.db')
food=pd.read_sql_query('SELECT name, price FROM menu WHERE category = ? ORDER BY price DESC',con,params=(cat,));con.close()""")
p('06-dates','mom-net','alternative-indexed-resample',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv',parse_dates=['datetime'])
monthly=df.set_index('datetime').amount.resample('ME').sum();growth=monthly.pct_change().mul(100).round(1);nov_growth=growth.loc['2026-11-30']""")
fixture_diverge=fixture+"\nd=pd.read_csv('orders_3m.csv');d['amount']=[900,400,200];d.to_csv('orders_3m.csv',index=False)\ns=pd.read_csv('shops.csv');s.loc[s.shop_id=='PRM-1','seats']=30;s.loc[s.shop_id=='KZN-1','seats']=10;s.to_csv('shops.csv',index=False)"
p('09-project','shops','different-revenue-and-seat-leaders',True,prepare=fixture_diverge)
p('09-project','shops','wrong-same-leader-for-different-metrics',False,suffix="leader_by_revenue=leader",prepare=fixture_diverge)
p('03-columns','map','alternative-replace-channels',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv')
df['channel_en']=df.channel.replace({'зал':'dine-in','с собой':'takeaway','доставка':'delivery'})
n_takeaway=df.channel_en.eq('takeaway').sum()""")
p('03-columns','map','wrong-swapped-dine-and-delivery',False,suffix="df['channel_en']=df.channel_en.replace({'dine-in':'delivery','delivery':'dine-in'})")
p('04b-pivot','wide','alternative-unstack-manual-totals',True,code="""import pandas as pd
df=pd.read_csv('orders_3m.csv');df['month']=df.datetime.str[:7]
report=df.groupby(['shop_id','month']).amount.sum().unstack()
report['Итого']=report.sum(axis=1);report.loc['Итого']=report.sum(axis=0)
report=report.iloc[::-1,::-1];oct_total=report.loc['Итого','2026-10']""")
p('04b-pivot','wide','wrong-nonchecked-million',False,suffix="report.loc['PRM-2','2026-11']+=1000000")
p('07b-sql-windows','w-lag','alternative-window-file-sql',True,code="""import duckdb
mom_shop=duckdb.sql(\"\"\"SELECT shop_id,month,revenue,round(100*(revenue/lag(revenue) OVER w-1),1) AS growth_pct FROM (SELECT shop_id,date_trunc('month',datetime) AS month,sum(amount) AS revenue FROM read_csv('orders_3m.csv') GROUP BY 1,2) WINDOW w AS (PARTITION BY shop_id ORDER BY month) ORDER BY shop_id,month\"\"\").df()
falls=mom_shop.query('growth_pct<0').copy()""")
p('07b-sql-windows','w-lag','wrong-shifted-months',False,suffix="mom_shop['month']+=pd.DateOffset(months=1);falls['month']+=pd.DateOffset(months=1)")
p('07b-sql-windows','w-lag','wrong-zero-revenues',False,suffix="mom_shop['revenue']=0;falls['revenue']=0")
p('07c-sql-frames','w-running','alternative-explicit-frame-file-sql',True,code="""import duckdb
cum=duckdb.sql(\"\"\"SELECT day,revenue,sum(revenue) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running FROM (SELECT CAST(datetime AS DATE) AS day,sum(amount) AS revenue FROM read_csv('orders_3m.csv') GROUP BY 1) ORDER BY day\"\"\").df()
half_day=cum.loc[cum.running.ge(cum.revenue.sum()/2),'day'].min()""")
p('07c-sql-frames','w-running','wrong-shifted-days',False,suffix="cum['day']+=pd.Timedelta(days=1)")
p('07c-sql-frames','w-running','wrong-zero-daily-revenue',False,suffix="cum['revenue']=0")
p('07a-sql-python','sqlite-read','alternative-read-sql-keyword-api',True,code='import sqlite3, pandas as pd\ncat="еда"\ncon=sqlite3.connect(\'zerno.db\')\nfood=pd.read_sql(sql=\'SELECT name, price FROM menu WHERE category = ? ORDER BY price DESC\',con=con,params=[cat]);con.close()')
p('05-merge','city','review-missing_city_nullable',False,code='import pandas as pd\ndf = pd.read_csv("orders_3m.csv")\nshops = pd.read_csv("shops.csv")\nfull = pd.merge(df, shops, on="shop_id", how="left")\nfull[\'city\']=full[\'city\'].astype(\'string\'); full.loc[full.index[0], \'city\'] = pd.NA')
p('05-merge','all-shops','review-missing_city_nullable',False,code='import pandas as pd\ndf = pd.read_csv("orders_3m.csv")\nshops = pd.read_csv("shops.csv")\nrev = df.groupby("shop_id", as_index=False).agg(revenue=("amount", "sum"))\nreport = pd.merge(shops, rev, on="shop_id", how="left")[["shop_id", "city", "revenue"]]\nreport["revenue"] = report["revenue"].fillna(0)\nreport[\'city\']=report[\'city\'].astype(\'string\'); report.loc[report.index[0], \'city\'] = pd.NA')
p('05-merge','margin','review-ignores_size',False,code="import pandas as pd\nf=pd.read_csv('orders_3m.csv').merge(pd.read_csv('menu.csv'),on='drink')\nf['cost']=f.cost_s*f.qty\ng=f.groupby('drink')[['amount','cost']].sum()\nbest_margin=(1-g.cost/g.amount).idxmax()\n")
p('04-groupby','two-keys','review-named_aggregation',True,code="import pandas as pd\ndf=pd.read_csv('orders_3m.csv')\nby_pair=df.groupby(['shop_id','channel']).agg(total_amount=('amount', 'sum'))\nkzn1_delivery=by_pair.at[('KZN-1','доставка'), 'total_amount']\n")
p('04-groupby','two-keys','review-reversed_key_fields',True,code="import pandas as pd\ndf=pd.read_csv('orders_3m.csv')\nby_pair=df.groupby(['channel','shop_id']).amount.sum()\nkzn1_delivery=by_pair.loc[('доставка','KZN-1')]\n")
p('06-dates','mom-net','review-unrounded_growth',False,code='import pandas as pd\ndf = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])\nmonthly = df.resample("ME", on="datetime")["amount"].sum()\ngrowth = (monthly.pct_change() * 100).round(1)\nnov_growth = growth.iloc[-1]\ngrowth=monthly.pct_change()*100; nov_growth=growth.iloc[-1]')
p('07b-sql-windows','w-lag','review-unrounded_growth',False,code='import duckdb\nimport pandas as pd\ndf = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])\n\nmom_shop = duckdb.sql("""\n    WITH m AS (\n        SELECT shop_id, date_trunc(\'month\', datetime) AS month, SUM(amount) AS revenue\n        FROM df\n        GROUP BY shop_id, month\n    )\n    SELECT shop_id, month, revenue,\n           ROUND(100 * (revenue / LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month) - 1), 1) AS growth_pct\n    FROM m\n    ORDER BY shop_id, month\n""").df()\nfalls = mom_shop[mom_shop["growth_pct"] < 0]\nfalls\nmom_shop[\'growth_pct\']=mom_shop.groupby(\'shop_id\')[\'revenue\'].pct_change()*100\nfalls=mom_shop[mom_shop.growth_pct<0]')
p('07a-sql-python','sqlite-read','review-contextlib_closing',True,code='from contextlib import closing\nimport pandas as pd, sqlite3\ncat="еда"\nwith closing(sqlite3.connect(\'zerno.db\')) as con:\n    food=pd.read_sql_query(\'SELECT name, price FROM menu WHERE category = ? ORDER BY price DESC\',con,params=(cat,))\n')
p('03-columns','map','review-only_uppercase_translation',False,code='import pandas as pd\ndf = pd.read_csv("orders_3m.csv")\ndf["channel_en"] = df["channel"].map({"зал": "dine-in", "с собой": "takeaway", "доставка": "delivery"})\nn_takeaway = (df["channel_en"] == "takeaway").sum()\ndf.loc[df.index[-1], \'channel_en\']=df[\'channel_en\'].iloc[-1].upper()')
p('04b-pivot','wide','review-wrong_grand_total',False,code='import pandas as pd\ndf = pd.read_csv("orders_3m.csv")\ndf["month"] = df["datetime"].str[:7]\nreport = pd.pivot_table(df, index="shop_id", columns="month", values="amount",\n                        aggfunc="sum", margins=True, margins_name="Итого")\noct_total = report.loc["Итого", "2026-10"]\nreport.at[\'Итого\',\'Итого\']+=1')
p('07c-sql-frames','w-running','review-wrong_final_running',False,code='import duckdb\nimport pandas as pd\ndf = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])\n\ncum = duckdb.sql("""\n    WITH d AS (\n        SELECT CAST(datetime AS DATE) AS day, SUM(amount) AS revenue\n        FROM df\n        GROUP BY day\n    )\n    SELECT day, revenue, SUM(revenue) OVER (ORDER BY day) AS running\n    FROM d\n    ORDER BY day\n""").df()\nhalf_day = cum.loc[cum["running"] >= cum["revenue"].sum() / 2, "day"].iloc[0]\nprint(half_day)\ncum.loc[cum.index[-1], \'running\']+=1')
p('04-groupby','shares','review-correct_share_bad_top3',False,code='import pandas as pd\ndf = pd.read_csv("orders_3m.csv")\nby_drink = df.groupby("drink")["amount"].sum()\nshare = (by_drink / by_drink.sum() * 100).round(1).sort_values(ascending=False)\ntop3 = list(share.index[:3])\ntop3[2]=top3[0]')
p('05-merge','per-seat','review-sorted_aggregation',True,code="import pandas as pd\ndf=pd.read_csv('orders_3m.csv'); shops=pd.read_csv('shops.csv')\njoined=df.merge(shops,on='shop_id')\nm=joined.groupby('shop_id').agg(rev=('amount','sum'),n=('seats','first'))\nbest_per_seat=m.eval('rev/n').sort_values(ascending=False).index[0]\n")
p('07a-sql-python','sqlite-read','review-positional-params',True,code="import sqlite3,pandas as pd\ncat='еда'\ncon=sqlite3.connect('zerno.db')\nfood=pd.read_sql_query('SELECT name,price FROM menu WHERE category=? ORDER BY price DESC',con,None,True,(cat,));con.close()")
p('07a-sql-python','sqlite-read','review-unclosed-connection',False,code="import sqlite3,pandas as pd\ncat='еда'\ncon=sqlite3.connect('zerno.db')\nfood=pd.read_sql_query('SELECT name,price FROM menu WHERE category=? ORDER BY price DESC',con,params=(cat,))")
p('11-sql-project','p-promo','promo-extra-period-label',True,suffix="promo_items['Акция']='вне акции';promo_items.loc[(promo_items.name=='Раф') & (promo_items.month.dt.month==4),'Акция']='Весенний раф';promo_items.loc[(promo_items.name=='Лимонад') & (promo_items.month.dt.month==7),'Акция']='Летний лимонад'")
p('11-sql-project','p-promo','promo-reordered-columns-extra-label',True,suffix="promo_items['Акция']='подпись периода';promo_items=promo_items[['Акция','growth_pct','cups','month','name']]")
p('11-sql-project','p-promo','promo-wrong-cups-extra-label',False,suffix="promo_items['Акция']='подпись периода';promo_items.loc[promo_items.index[-1],'cups']+=100")
p('11-sql-project','p-promo','promo-wrong-growth-extra-label',False,suffix="promo_items['Акция']='подпись периода';promo_items.loc[promo_items.index[-1],'growth_pct']+=10")
p('11-sql-project','p-promo','promo-duplicate-required-field',False,suffix="promo_items=promo_items[['name','month','cups','growth_pct','cups']]")
p('11-sql-project','p-promo','promo-fractional-cups',False,suffix="promo_items['cups']+=0.25")
p('11-sql-project','p-promo','promo-unrounded-growth',False,suffix="promo_items['growth_pct']=promo_items.groupby('name')['cups'].pct_change()*100")
(D/'probes-before.json').write_text(json.dumps(P,ensure_ascii=False,indent=2))
print(len(P))
