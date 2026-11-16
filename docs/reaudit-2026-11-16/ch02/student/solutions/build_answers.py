import json, pathlib, re
ROOT=pathlib.Path('/private/tmp/kuch02round/student')
def save(lesson,solutions,questions):
    s=(ROOT/(lesson+'.md')).read_text()
    out=[]
    for task,code in solutions.items():
        if 'Доступные строки для сборки с отступами:' in s.split('## task: '+task+' |',1)[1].split('## task:',1)[0]:
            section=s.split('## task: '+task+' |',1)[1].split('## task:',1)[0]
            available=section.split('Доступные строки для сборки с отступами:',1)[1].strip().splitlines()
            normal=lambda x: re.sub(r'\s+','',x)
            code='\n'.join(next((a for a in available if normal(a)==normal(line)),line) for line in code.splitlines())
        out.append(dict(lesson=lesson,task=task,code=code,expect='Код применяет изученную операцию к данным и сохраняет требуемые переменные; сверяю значения и тип результата.'))
    for question,choice,reason in questions:
        out.append(dict(question=f'{lesson}/{question}',choice=choice,expect=reason))
    p=ROOT/'work'/(lesson+'.jsonl');p.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out))
    for task,code in solutions.items():
        (ROOT/'work'/(lesson+'-'+task+'.py')).write_text(code+'\n')
    return p
if __name__=='__main__':
    p='import pandas as pd\ndf=pd.read_csv("orders_3m.csv")\n'
    save('01-dataframe',{
    'menu':'import pandas as pd\nmenu=pd.DataFrame({"drink":["Латте","Капучино","Раф"],"price":[210,190,260]})\nmenu',
    'load':p+'n_rows=len(df)', 'p-sum':p+'revenue=df["amount"].sum()\nprint(revenue)', 'columns':p+'cols=list(df.columns)',
    'kpi':p+'revenue=df["amount"].sum()\navg_check=round(df["amount"].mean(),2)',
    'clients':p+'n_clients=df["client_id"].nunique()',
    'hit':p+'vc=df["drink"].value_counts()\ntop_drink=vc.index[0]\ntop_count=vc.iloc[0]',
    'describe':p+'median_check=df["amount"].median()\nshare_big=round((df["amount"]>600).mean()*100,1)',
    'supplier':'import pandas as pd\nprices=pd.read_csv("supplier_prices.csv",sep=";",encoding="cp1251",decimal=",",thousands=" ")\ntotal=round((prices["Цена, руб."]*prices["Количество"]).sum(),2)',
    'records':'import pandas as pd\norders=[{"city":"Пермь","drink":"Латте","amount":450},{"city":"Казань","drink":"Раф"},{"city":"Пермь","drink":"Раф","amount":610},{"city":"Уфа","drink":"Мокко","amount":480},{"city":"Казань","drink":"Латте","amount":320}]\nt=pd.DataFrame(orders)\nn_no_amount=t["amount"].isna().sum()\ntotal=t["amount"].sum()\navg_check=t["amount"].mean()',
    'loyalty':p+'loyalty_share=round(df["client_id"].notna().mean()*100,1)\norders_per_client=round(df["client_id"].count()/df["client_id"].nunique(),1)'},[
    ('quiz/1',4,'Цена пока текст; указываю дробную запятую и пробел тысяч.'),('quiz/2',3,'Один ключ даёт Series, список ключей сохраняет таблицу.'),('predict/1',3,'В каждом столбце три строки, столбцов два.'),('predict/2',2,'Подпись первого элемента Латте, частота три.'),('predict/3',1,'Латте, Раф и Мокко — три разных значения.')])
    save('02-select', {k:p+v for k,v in {
    'cols':'sub=df[["drink","amount"]]', 'big':'big=df[df["amount"]>800]\nn_big=len(big)',
    'p-loc':'mask=(df["size"]=="L") & (df["channel"]=="доставка")\nresult=df.loc[mask,["drink","amount"]]\nprint(len(result))',
    'delivery':'n_delivery=(df["channel"]=="доставка").sum()',
    'and':'revenue_big_delivery=df.loc[(df["channel"]=="доставка") & (df["amount"]>500),"amount"].sum()',
    'fix-and':'n=len(df[(df["size"]=="S") & (df["channel"]=="зал")])\nprint(n)',
    'isin':'kazan_revenue=df.loc[df["shop_id"].isin(["KZN-1","KZN-2"]),"amount"].sum()',
    'loc':'large=df.loc[df["size"]=="L",["order_id","drink","amount"]]',
    'october':'october=df.loc[df["datetime"].str.startswith("2026-10"),"amount"].sum()',
    'query-at':'threshold=450\ndrinks=["Раф","Мокко","Какао"]\nsweet=df.query("amount >= @threshold and drink in @drinks")\nn_sweet=len(sweet)\nrev_sweet=sweet["amount"].sum()',
    'query':'q=df.query("amount > 400 and channel != \'зал\'")\nn_q=len(q[q["client_id"].notna()])',
    'share':'k=df[df["shop_id"].isin(["KZN-1","KZN-2"])]\nshare=round(k.loc[k["channel"]=="доставка","amount"].sum()/k["amount"].sum()*100,1)'
    }.items()}, [('predict/1',2,'10 и 15 больше 5, строк две.'),('quiz/1',1,'Для столбцов нужен поэлементный &, каждое сравнение в скобках.'),('predict/2',3,'Два True в маске, сумма равна двум.')])
    save('03-columns', {k:p+v for k,v in {
    'top5':'top5=df.sort_values("amount",ascending=False).head(5)',
    'price':'df["price"]=df["amount"]/df["qty"]',
    'p-sort':'df["price"]=df["amount"]/df["qty"]\ntop=df.sort_values("price",ascending=False)\nprint(top["drink"].iloc[0])',
    'nlargest':'ids=df.nlargest(3,"amount")["order_id"].tolist()',
    'map':'df["channel_en"]=df["channel"].map({"зал":"dine-in","с собой":"takeaway","доставка":"delivery"})\nn_takeaway=(df["channel_en"]=="takeaway").sum()',
    'cut':'df["segment"]=pd.cut(df["amount"],bins=[0,250,500,float("inf")],labels=["малый","средний","крупный"])\ncounts=df["segment"].value_counts()',
    'loc-update':'df["amount_net"]=df["amount"]\nm=df["channel"]=="доставка"\ndf.loc[m,"amount_net"]=(df.loc[m,"amount"]*.9).round()',
    'rename':'export=df.drop(columns=["client_id","channel"]).rename(columns={"amount":"sum_rub"}).sort_values("sum_rub",ascending=False)',
    'hour':'df["hour"]=df["datetime"].str[11:13].astype(int)\npeak_hour=df["hour"].value_counts().index[0]'
    }.items()}, [('predict/1',1,'DESC располагает 9,4,2.'),('predict/2',3,'Неизвестное L превращается в NaN, числа становятся float.'),('quiz/1',3,'loc одной операцией меняет исходную таблицу, Series справа совмещается по индексу.')])
    save('04-groupby',{k:p+v for k,v in {
    'by-shop':'by_shop=df.groupby("shop_id")["amount"].sum()',
    'by-channel':'channels=df.groupby("channel").size().to_dict()',
    'p-agg':'t=df.groupby("shop_id").agg(avg_check=("amount","mean"))\nbest=t["avg_check"].idxmax()\nprint(best)',
    'shop-stats':'stats=df.groupby("shop_id").agg(revenue=("amount","sum"),orders=("order_id","count"),avg_check=("amount","mean"))\nstats["avg_check"]=stats["avg_check"].round(1)',
    'having':'n=df.groupby("drink").size()\npopular=sorted(n[n>200].index.tolist())',
    'two-keys':'by_pair=df.groupby(["shop_id","channel"])["amount"].sum()\nkzn1_delivery=by_pair[("KZN-1","доставка")]',
    'shares':'r=df.groupby("drink")["amount"].sum()\nshare=(r/r.sum()*100).round(1).sort_values(ascending=False)\ntop3=share.index[:3].tolist()',
    'avg-of-avg':'loyal=df[df["client_id"].notna()]\nclient_avg=round(loyal.groupby("client_id")["amount"].mean().mean(),1)\norder_avg=round(loyal["amount"].mean(),1)',
    'pareto':'r=df.groupby("drink")["amount"].sum().sort_values(ascending=False)\nn80=int((r.cumsum()/r.sum()<.8).sum()+1)'
    }.items()}, [('predict/1',2,'a даёт 1+3=4, b даёт 2, ключи сортируются.'),('predict/2',3,'count пропускает None.'),('quiz/1',3,'Нужны уникальные гости, а не визиты.'),('quiz/2',2,'Делю всю выручку 36000 на все 110 заказов.')])
    save('04a-guest-metrics',{
    'toy-guest':'import pandas as pd\nt=pd.DataFrame({"client_id":["X","X","Y","Z","Z","Z","Z"],"amount":[200,300,500,100,150,150,200]})\ng=t.groupby("client_id").agg(orders=("amount","size"),revenue=("amount","sum"))\ncheck=t["amount"].mean()\narpu=g["revenue"].mean()\nrepeat=(g["orders"]>=2).mean()',
    'per-guest':p+'g=df.groupby("client_id").agg(orders=("order_id","size"),revenue=("amount","sum"))\narpu=round(g["revenue"].mean(),2)\norders_per_guest=round(g["orders"].mean(),2)',
    'repeat':p+'g=df[df["datetime"].str.startswith("2026-10")].groupby("client_id").size()\nrepeat_oct=round((g>=2).mean()*100,1)',
    'arpu-month':p+'loyal=df[df["client_id"].notna()].copy()\nloyal["month"]=loyal["datetime"].str[:7]\ng=loyal.groupby("month").agg(revenue=("amount","sum"),guests=("client_id","nunique"))\narpu_m=(g["revenue"]/g["guests"]).round(2).to_dict()',
    'conversion':'import pandas as pd\nguests=pd.read_csv("zdb_guests.csv")\norders=pd.read_csv("zdb_orders.csv")\nguests["ordered"]=guests["guest_id"].isin(orders["guest_id"])\nconv_all=round(guests["ordered"].mean(),3)\nconv=guests.groupby("source")["ordered"].mean().round(3).to_dict()\nlost_app=((guests["source"]=="приложение") & ~guests["ordered"]).sum()'
    }, [('quiz/1',1,'Строка пока заказ; на гостя нужна агрегация по client_id.')])
    pm=p+'df["month"]=df["datetime"].str[:7]\n'
    multi='t=pd.pivot_table(df,index="shop_id",columns="month",values=["amount","order_id"],aggfunc={"amount":"sum","order_id":"count"})\n'
    save('04b-pivot',{
    'p-pivot':p+'pv=pd.pivot_table(df,index="shop_id",columns="channel",values="amount",aggfunc="sum")\ncell=pv.loc["UFA-1","с собой"]\nprint(cell)',
    'pivot':p+'pv=pd.pivot_table(df,index="shop_id",columns="size",values="order_id",aggfunc="count")\nufa_l=pv.loc["UFA-1","L"]',
    'g-unstack':p+'wide=df.groupby(["shop_id","channel"])["amount"].sum().unstack()\nwide_shape=wide.shape',
    'wide':pm+'report=pd.pivot_table(df,index="shop_id",columns="month",values="amount",aggfunc="sum",margins=True,margins_name="Итого")\noct_total=report.loc["Итого","2026-10"]',
    'melt':'import pandas as pd\nplan=pd.DataFrame({"shop_id":["KZN-1","KZN-2","PRM-1","PRM-2","TMN-1","UFA-1"],"2026-09":[60000,30000,60000,25000,30000,20000],"2026-10":[62000,32000,62000,26000,31000,24000],"2026-11":[65000,34000,65000,27000,33000,26000]})\nplan_long=plan.melt(id_vars="shop_id",var_name="month",value_name="plan")\nplan_by_month=plan_long.groupby("month")["plan"].sum().to_dict()',
    'flat-cols':pm+multi+'t.columns=[f"{a}_{b}" for a,b in t.columns]\ncols=t.columns.tolist()\nprm2_oct_orders=t.loc["PRM-2","order_id_2026-10"]',
    'multi':pm+multi+'avg_check=(t["amount"]/t["order_id"]).round(1)\nkzn_nov=avg_check.loc["KZN-1","2026-11"]',
    'ch-share':p+'pv=pd.pivot_table(df,index="shop_id",columns="channel",values="amount",aggfunc="sum")\nshare=pv.div(pv.sum(axis=1),axis=0)\nlow_delivery=share["доставка"].idxmin()\nlow_share=round(share.loc[low_delivery,"доставка"],3)'
    }, [('predict/1',1,'Две кофейни и два размера.'),('predict/2',1,'A,L содержит 300; пустая пара делает столбец float.'),('quiz/1',2,'По умолчанию mean, для выручки нужно sum.'),('predict/3',1,'3 магазина на 2 месяца дают 6 строк и 3 столбца.'),('quiz/2',2,'Длинный формат даёт одинаковые ключи с фактом и позволяет соединить.')])
    ps=p+'shops=pd.read_csv("shops.csv")\n'
    pn=p+'menu=pd.read_csv("menu.csv")\n'
    save('05-merge',{
    'city':ps+'full=df.merge(shops,on="shop_id",how="left",validate="many_to_one")',
    'by-city':ps+'full=df.merge(shops,on="shop_id",how="left",validate="many_to_one")\nby_city=full.groupby("city")["amount"].sum().sort_values(ascending=False)\nbest_city=by_city.index[0]',
    'p-merge':pn+'full = df.merge(menu, on="drink", how="left")\nby_cat = full.groupby("category")["amount"].sum()\nprint(by_cat["кофе"])',
    'category':pn+'full=df.merge(menu,on="drink",how="left",validate="many_to_one")\nnon_coffee_share=round(full.loc[full["category"]=="не кофе","amount"].sum()/full["amount"].sum()*100,1)',
    'all-shops':ps+'rev=df.groupby("shop_id",as_index=False).agg(revenue=("amount","sum"))\nreport=shops[["shop_id","city"]].merge(rev,on="shop_id",how="left",validate="one_to_one")\nreport["revenue"]=report["revenue"].fillna(0)',
    'per-seat':ps+'rev=df.groupby("shop_id")["amount"].sum()\ns=shops.set_index("shop_id")\nbest_per_seat=(rev/s["seats"]).idxmax()',
    'margin':pn+'SIZE_K={"S":1.,"M":1.25,"L":1.5}\nfull=df.merge(menu,on="drink",how="left",validate="many_to_one")\nfull["cost"]=full["cost_s"]*full["size"].map(SIZE_K)*full["qty"]\ndf["cost"]=full["cost"]\ng=full.groupby("drink").agg(revenue=("amount","sum"),cost=("cost","sum"))\nbest_margin=((g["revenue"]-g["cost"])/g["revenue"]*100).idxmax()',
    'validate':ps+'shops_bad=pd.concat([shops,shops[shops["shop_id"]=="KZN-1"]],ignore_index=True)\ncaught=False\ntry:\n    df.merge(shops_bad,on="shop_id",how="left",validate="many_to_one")\nexcept pd.errors.MergeError:\n    caught=True\nextra=len(df.merge(shops_bad,on="shop_id",how="left"))-len(df)'
    },[('predict/1',3,'По умолчанию inner, ключ 1 даёт две пары.'),('quiz/1',2,'Справочник слева при LEFT сохраняет все кофейни.'),('quiz/2',2,'Одна строка заказа сопоставляется каждой строке дубля.')])
    save('05b-join-index',{
    'map-toy':'import pandas as pd\nt=pd.DataFrame({"drink":["Раф","Латте","Чай","Раф"]})\nprice=pd.Series({"Латте":220,"Раф":260,"Какао":200})\nt["price"]=t["drink"].map(price)\nno_price=t["price"].isna().sum()',
    'align':ps+'rev=df.groupby("shop_id")["amount"].sum()\nshops["revenue"]=shops["shop_id"].map(rev).fillna(0)',
    'join':ps+'stats=df.groupby("shop_id").agg(revenue=("amount","sum"),guests=("client_id","nunique"))\nreport=shops.join(stats,on="shop_id")\nn_empty=report["revenue"].isna().sum()',
    'key-type':'import pandas as pd\nvisits=pd.DataFrame({"guest":["0101","0102","0103","0104","0105"],"visits":[5,2,7,1,3]})\nbonus=pd.DataFrame({"guest":[101,102,104,106],"bonus":[150,0,300,50]})\nbonus["guest"]=bonus["guest"].astype(str).str.zfill(4)\nfull=visits.merge(bonus,on="guest",how="left",validate="one_to_one")\nmatched=full["bonus"].notna().sum()',
    'anti':ps+'no_orders=shops.loc[~shops["shop_id"].isin(df["shop_id"]),"shop_id"].tolist()',
    'p-concat':p+'oct_df = df[df["datetime"].str.startswith("2026-10")]\nnov_df = df[df["datetime"].str.startswith("2026-11")]\nboth = pd.concat([oct_df, nov_df], ignore_index=True)\nprint(len(both))',
    'concat':p+'sep_df=df[df["datetime"].str.startswith("2026-09")]\noct_df=df[df["datetime"].str.startswith("2026-10")]\nnov_df=df[df["datetime"].str.startswith("2026-11")]\nall3=pd.concat([sep_df,oct_df,nov_df],ignore_index=True)\nsame=len(all3)==len(df)'
    },[('predict/1',3,'Индекс 1 не имеет пары; 300 находится у индекса 2.'),('quiz/1',1,'Типы совпали, остаётся проверить сами записи ключей.'),('predict/2',1,'Ключ 1 сопоставился, 2 присутствует только слева.')])
    pdtime='import pandas as pd\ndf=pd.read_csv("orders_3m.csv",parse_dates=["datetime"])\n'
    save('06-dates',{
    'to-dt':p+'df["datetime"]=pd.to_datetime(df["datetime"])',
    'months':pdtime+'by_month=df.groupby(df["datetime"].dt.month)["amount"].sum().to_dict()',
    'p-month':p+'df["datetime"] = pd.to_datetime(df["datetime"])\ndf["month"] = df["datetime"].dt.month\nprint(df.groupby("month")["amount"].sum()[11])',
    'weekend':pdtime+'weekend_share=round(df.loc[df["datetime"].dt.weekday>=5,"amount"].sum()/df["amount"].sum()*100,1)',
    'period':pdtime+'rev_1_15=df.loc[(df["datetime"]>="2026-10-01") & (df["datetime"]<"2026-10-16"),"amount"].sum()',
    'hours':pdtime+'orders_by_hour=df.groupby(df["datetime"].dt.hour).size().sort_index()\npeak=orders_by_hour.idxmax()',
    'best-day':pdtime+'daily=df.resample("D",on="datetime")["amount"].sum()\nbest_date=daily.idxmax().date()\nbest_revenue=daily.max()',
    'mom-net':pdtime+'monthly=df.resample("ME",on="datetime")["amount"].sum()\ngrowth=(monthly.pct_change()*100).round(1)\nnov_growth=growth.iloc[-1]',
    'floor':pdtime+'n=df["datetime"].dt.floor("30min").dt.strftime("%H:%M").value_counts()\npeak_slot=n.index[0]\npeak_n=n.iloc[0]',
    'weekly':pdtime+'weekly=df.resample("W",on="datetime")["amount"].sum()\nn_weeks=len(weekly)\nbest_week_end=weekly.idxmax().date()',
    'lifetime':pdtime+'g=df.groupby("client_id")["datetime"].agg(["min","max"])\ndays=(g["max"]-g["min"]).dt.days\navg_days=round(days.mean(),1)\nloyal=(days>=60).sum()',
    'mom':pdtime+'df["month"]=df["datetime"].dt.month\nt=df.groupby(["shop_id","month"])["amount"].sum().unstack()\ngrowth=((t[11]/t[10]-1)*100).round(1)\nfastest=growth.idxmax()'
    },[('predict/1',1,'Понедельник имеет номер 0.'),('quiz/1',2,'Граница без времени означает начало дня.'),('quiz/2',1,'resample задаёт регулярный календарь и заполняет пустые дни суммой 0.'),('predict/2',2,'От 1 до 10 прошло девять суток.')])
    pe='import pandas as pd\nev=pd.read_csv("app_events.csv")\n'
    save('06b-timezones',{
    'unix-range':pe+'utc=pd.to_datetime(ev["ts"],unit="ms")\nfirst_utc=utc.min()\nlast_utc=utc.max()',
    'p-tz':pe+'kzn = ev[ev["shop_id"].str.startswith("KZN")].copy()\nkzn["utc"] = pd.to_datetime(kzn["ts"], unit="ms")\nkzn["local"] = kzn["utc"].dt.tz_localize("UTC").dt.tz_convert("+03:00")\nprint(kzn["local"].dt.hour.value_counts().idxmax())',
    'unix':pe+'perm=ev[ev["shop_id"].str.startswith("PRM")].copy()\nperm["utc"]=pd.to_datetime(perm["ts"],unit="ms")\nperm["local"]=perm["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")\nperm_peak=perm["local"].dt.hour.value_counts().idxmax()',
    'tmn-fix':pe+'tmn=ev[ev["shop_id"].str.startswith("TMN")].copy()\ntmn["utc"]=pd.to_datetime(tmn["ts"],unit="ms")\ntmn["local"]=tmn["utc"].dt.tz_localize("UTC").dt.tz_convert("+05:00")\ntmn_morning=round((tmn["local"].dt.hour<10).mean()*100,1)\nprint(tmn_morning)',
    'local-time':pe+'offset={"PRM":5,"TMN":5,"UFA":5,"KZN":3}\nev["local"]=pd.to_datetime(ev["ts"],unit="ms")+pd.to_timedelta(ev["shop_id"].str[:3].map(offset),unit="h")\no=ev[ev["event"]=="заказ"]\nmorning_share=round((o["local"].dt.hour<10).mean()*100,1)'
    },[('quiz/1',4,'Unix обозначает UTC; местный пик сдвинут на пять часов.')])
    pdb='import duckdb\n'+p
    save('07-duckdb',{
    'total':pdb+'revenue=duckdb.sql("SELECT SUM(amount) FROM df").fetchone()[0]',
    'group':pdb+'by_channel=duckdb.sql("SELECT channel, COUNT(*) AS orders FROM df GROUP BY channel ORDER BY orders DESC").df()',
    'p-sql':'import duckdb\nquery = "SELECT COUNT(*) FROM \'orders_3m.csv\' WHERE size = \'L\'"\nn = duckdb.sql(query).fetchone()[0]\nprint(n)',
    'join':pdb+'shops=pd.read_csv("shops.csv")\nby_city=duckdb.sql("SELECT city,SUM(amount) AS revenue FROM df JOIN shops USING(shop_id) GROUP BY city ORDER BY revenue DESC").df()',
    'having':pdb+'rare=[row[0] for row in duckdb.sql("SELECT drink FROM df GROUP BY drink HAVING COUNT(*)<100 ORDER BY drink").fetchall()]',
    'from-file':'import duckdb\navg_check_delivery=duckdb.sql("SELECT ROUND(AVG(amount),2) FROM \'orders_3m.csv\' WHERE channel=\'доставка\'").fetchone()[0]',
    'reconcile':pdb+'pd_avg=df.groupby("channel")["amount"].mean().round(2).to_dict()\nsql_avg=dict(duckdb.sql("SELECT channel,ROUND(AVG(amount),2) FROM df GROUP BY channel").fetchall())\nmatch=all(abs(pd_avg[k]-sql_avg[k])<1e-8 for k in pd_avg)'
    },[('predict/1',1,'Обычное деление в DuckDB возвращает 3.5.'),('predict/2',1,'Две строки и [0] извлекает скаляр из кортежа.'),('quiz/1',3,'DuckDB умеет окна прямо на DataFrame, можно оставить знакомый SQL.')])
    sq='import sqlite3\nimport pandas as pd\n'
    save('07a-sql-python',{
    'items-peek':sq+'con=sqlite3.connect("zerno.db")\norders_cols=pd.read_sql_query("SELECT * FROM orders LIMIT 0",con).columns.tolist()\nn_items=pd.read_sql_query("SELECT COUNT(*) AS n FROM order_items",con)["n"].iloc[0]\ncon.close()',
    'p-sqlite':sq+'con = sqlite3.connect("zerno.db")\nquery = "SELECT COUNT(*) AS n FROM orders WHERE substr(ordered_at, 1, 7) = ?"\nt = pd.read_sql_query(query, con, params=("2026-04",))\ncon.close()\nprint(t["n"].iloc[0])',
    'sqlite-read':sq+'cat="еда"\ncon=sqlite3.connect("zerno.db")\nfood=pd.read_sql_query("SELECT name,price FROM menu WHERE category=? ORDER BY price DESC",con,params=(cat,))\ncon.close()',
    'delivery-month':sq+'month="2026-08"\ncon=sqlite3.connect("zerno.db")\nt=pd.read_sql_query("SELECT channel FROM orders WHERE substr(ordered_at,1,7)=?",con,params=(month,))\nshare=round((t["channel"]=="доставка").mean()*100,1)\ncon.close()',
    'sqlite-func':sq+'def city_revenue(con, city, month):\n    q="SELECT COALESCE(SUM(i.qty*i.price),0) AS revenue FROM orders o JOIN order_items i USING(order_id) JOIN shops s USING(shop_id) WHERE s.city=? AND substr(o.ordered_at,1,7)=?"\n    return int(pd.read_sql_query(q,con,params=(city,month))["revenue"].iloc[0])\ncon=sqlite3.connect("zerno.db")\nprint(city_revenue(con,"Казань","2026-06"))\ncon.close()'
    },[('predict/1',2,'Без запятой params это строка из шести символов, а заполнитель один.'),('quiz/1',4,'Значения передаю параметром без кавычек вокруг ?. Это надёжно и для апострофа.')])
    save('08-jupyter',{
    'env':'import sys\nimport pandas as pd\ndef env_report():\n    return {"python":f"{sys.version_info.major}.{sys.version_info.minor}","pandas":pd.__version__}\nenv_report()',
    'path':'from pathlib import Path\nDATA=Path("data")\npath=DATA/"orders_3m.csv"\nstem=path.stem',
    'sheets-url':'def sheet_csv_url(link):\n    sid=link.split("/d/")[1].split("/")[0]\n    gid=link.rsplit("gid=",1)[1].split("&")[0].split("#")[0] if "gid=" in link else "0"\n    return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"',
    'run-order':'x=10\nx=x*2\nx=x+5\ntop_down=x\nx=10\nx=x+5\nx=x*2\nshuffled=x',
    'ipynb-json':'import json\nwith open("zerno_draft.ipynb",encoding="utf-8") as f:\n    nb=json.load(f)\nn_md=sum(c["cell_type"]=="markdown" for c in nb["cells"])\nn_code=sum(c["cell_type"]=="code" for c in nb["cells"])\ncounts=[c["execution_count"] for c in nb["cells"] if c["cell_type"]=="code"]\nran=[n for n in counts if n is not None]\nin_order=all(a<b for a,b in zip(ran,ran[1:]))',
    'p-order':p+'by_shop = df.groupby("shop_id")["amount"].sum()\nbest = by_shop.idxmax()\nprint(best, by_shop[best])',
    'fix-order':'import pandas as pd\ndf = pd.read_csv("orders_3m.csv")\nrevenue = df["amount"].sum()\nn = len(df)\navg_check = round(revenue / n, 2)\nprint(avg_check)',
    'safe-filter':p+'delivery=df[df["channel"]=="доставка"]\nrevenue_all=df["amount"].sum()\nrevenue_delivery=delivery["amount"].sum()\ndelivery=df[df["channel"]=="доставка"]\nn_rows=len(df)',
    'nb-audit':'''import json
import re
def audit(nb):
    problems=[]
    maximum=0
    for i,c in enumerate(nb["cells"]):
        if c["cell_type"]!="code":
            continue
        n=c.get("execution_count")
        if n is not None:
            if n<maximum:
                problems.append((i,"order"))
            maximum=max(maximum,n)
        source="".join(c["source"])
        for j,ch in enumerate(source):
            if ch in ['"',"'"]:
                after=source[j+1:]
                if after.startswith("/") or (len(after)>=2 and after[0].isalpha() and after[1]==":"):
                    problems.append((i,"abs_path"))
                    break
        if any(o.get("output_type")=="error" for o in c.get("outputs",[])):
            problems.append((i,"error"))
        lines=[x.strip() for x in source.splitlines() if x.strip()]
        if lines and all(x.startswith("#") for x in lines):
            problems.append((i,"commented"))
    return problems
nb=json.load(open("zerno_draft.ipynb",encoding="utf-8"))
audit(nb)'''
    },[('predict/1',1,'Восемь ячеек, две Markdown, шесть кодовых.'),('predict/2',2,'Дважды увеличили единицу на один — три.'),('predict/3',1,'После перезапуска x в памяти отсутствует.'),('quiz/1',3,'Скрытая память ядра маскировала отсутствие определения выше вызова.')])
    shopfn='def shop_kpi(df,shop_id):\n    t=df.loc[df["shop_id"]==shop_id,"amount"]\n    return {"orders":len(t),"revenue":t.sum(),"avg_check":round(t.mean(),1)}\n'
    outline='''outline=[("markdown","# Итоги осени"),("code","import pandas as pd"),("markdown","## Данные"),("code","df = pd.read_csv('data/orders_3m.csv')"),("markdown","Вывод: 2089 заказов, пропусков в сумме нет."),("markdown","## Выручка по месяцам"),("code","monthly = ..."),("markdown","## Кофейни"),("code","by_shop = ..."),("markdown","Вывод: лидер — PRM-1."),("markdown","## Часы пик"),("code","load = ...")]
'''
    nb_order='''cells = []
cells.append(("markdown", "# Итоги осени: цель и данные"))
cells.append(("code", "import pandas as pd"))
cells.append(("code", "df = pd.read_csv('data/orders_3m.csv')"))
cells.append(("markdown", "## Выручка по месяцам"))
cells.append(("code", "monthly = df.groupby('month')['amount'].sum()"))
cells.append(("markdown", "Вывод: в ноябре +9.6 % к октябрю."))
cells.append(("markdown", "## Общий вывод"))
print(len(cells))'''
    save('08a-nb-report',{
    'nb-order':nb_order,
    'md-report':p+'''report=f"**Выручка:** {df['amount'].sum()} ₽\\n**Заказов:** {len(df)}\\n**Средний чек:** {df['amount'].mean():.2f} ₽"''',
    'conclusion':pdtime+'''m=df.groupby(df["datetime"].dt.month)["amount"].sum()
growth=(m.loc[11]/m.loc[10]-1)*100
best=df.groupby("shop_id")["amount"].sum().idxmax()
conclusion=(f"**Что сделали:** разобрали {len(df)} заказов {df['shop_id'].nunique()} кофеен.\\n"
    f"**Что нашли:** рост выручки ноября к октябрю — {growth:+.1f} %, лидер по выручке — {best}.\\n"
    "**Что предлагаем:** проверить рост по отдельным дням и сохраняется ли эффект в декабре.")''',
    'md-after':outline+'''def missing_conclusions(cells):
    missing=[]
    section=None
    last=None
    for typ,text in cells:
        if typ=="markdown" and text.startswith("## "):
            if section is not None and (last is None or last[0]!="markdown" or last[1].startswith("#")):
                missing.append(section)
            section=text[3:]
            last=(typ,text)
        elif section is not None:
            last=(typ,text)
    if section is not None and (last is None or last[0]!="markdown" or last[1].startswith("#")):
        missing.append(section)
    return missing
bad=missing_conclusions(outline)''',
    'function-cell':p+shopfn+'kpi_ufa=shop_kpi(df,"UFA-1")\nkpi_ufa',
    'kpi-all':p+shopfn+'kpi=pd.DataFrame({sid:shop_kpi(df,sid) for sid in df["shop_id"].unique()}).T\nkpi.index.name="shop_id"\nbest_check=kpi["avg_check"].idxmax()'
    },[('predict/1',3,'+ задаёт явный знак, .1f округляет до одного десятичного.'),('quiz/1',1,'Здесь конкретный месяц, величина изменения и его компоненты.'),('predict/2',3,'Доли переводятся в проценты и округляются до одного знака.')])
    save('08b-jupyter-keys',{
    'p-keys':'keys = []\nkeys.append("Esc")\nkeys.append("B")\nkeys.append("M")\nkeys.append("Enter")\nkeys.append("напечатать: Вывод: в ноябре +9.6 %")\nkeys.append("Shift+Enter")\nprint(keys)',
    'signature':'import inspect\nimport pandas as pd\nasc_default=inspect.signature(pd.DataFrame.sort_values).parameters["ascending"].default\nnorm_default=inspect.signature(pd.Series.value_counts).parameters["normalize"].default\ndropna_default=inspect.signature(pd.Series.value_counts).parameters["dropna"].default',
    'float-fmt':p+'avg=df.groupby("shop_id")["amount"].mean()\nwith pd.option_context("display.float_format","{:.1f}".format):\n    print(avg)',
    'rows-ctx':p+'with pd.option_context("display.max_rows",6,"display.max_columns",None):\n    print(df)',
    'timeit-read':'slow="13.2 ms ± 828 μs per loop (mean ± std. dev. of 7 runs, 100 loops each)"\nfast="87.5 μs ± 8.78 μs per loop (mean ± std. dev. of 7 runs, 10,000 loops each)"\ndef to_us(text):\n    number,unit=text.split()[:2]\n    return float(number)*{"s":1000000,"ms":1000,"μs":1,"µs":1,"ns":.001}[unit]\nspeedup=round(to_us(slow)/to_us(fast))',
    'time-it':'import timeit\n'+p+'t_apply=timeit.timeit(lambda:df.apply(lambda r:r["amount"]/r["qty"],axis=1),number=3)/3\nt_vec=timeit.timeit(lambda:df["amount"]/df["qty"],number=3)/3\nfaster=t_apply/t_vec',
    'tb-fix':p+'by_shop=df.groupby("shop_id").agg(revenue=("amount","sum"),orders=("order_id","count"))\nbad_names=["shop","amout"]\nby_shop'
    },[('predict/1',1,'Вставка выше идёт на текущий индекс 1, размер списка становится 3.'),('quiz/1',1,'Курсор мигает — режим правки.'),('predict/2',1,'Меняется только формат представления.'),('quiz/2',1,'2100 микросекунд / 850 = 2.47.'),('predict/3',3,'Регистр имени столбца значим, Amount отсутствует.')])
    full=pdtime+'shops=pd.read_csv("shops.csv")\nmenu=pd.read_csv("menu.csv")\nfull=df.merge(shops,on="shop_id",how="left",validate="many_to_one").merge(menu,on="drink",how="left",validate="many_to_one")\n'
    mcode='monthly=full.groupby(full["datetime"].dt.to_period("M")).agg(revenue=("amount","sum"),orders=("order_id","size"),avg_check=("amount","mean"),clients=("client_id","nunique"))\nmonthly["avg_check"]=monthly["avg_check"].round(1)\nnov_vs_oct=round((monthly["revenue"].iloc[-1]/monthly["revenue"].iloc[-2]-1)*100,1)\n'
    bcode='by_shop=full.groupby("shop_id").agg(city=("city","first"),revenue=("amount","sum"),seats=("seats","first"))\nby_shop["per_seat"]=(by_shop["revenue"]/by_shop["seats"]).round()\nby_shop=by_shop.sort_values("per_seat",ascending=False)\nleader=by_shop["per_seat"].idxmax()\nleader_by_revenue=by_shop["revenue"].idxmax()\n'
    scode='nov=full[full["datetime"].dt.month==11]\noctober=full[full["datetime"].dt.month==10]\nnew_drinks=set(nov["drink"])-set(full.loc[full["datetime"].dt.month<11,"drink"])\nseasonal_share=round(nov.loc[nov["drink"].isin(new_drinks),"amount"].sum()/nov["amount"].sum()*100,1)\ncheck_change=round((nov["amount"].mean()/october["amount"].mean()-1)*100,1)\n'
    lcode='card=full.loc[full["client_id"].notna(),"amount"].mean()\nno_card=full.loc[full["client_id"].isna(),"amount"].mean()\navg_card=round(card,1)\navg_no_card=round(no_card,1)\ndiff_pct=round((card/no_card-1)*100,1)\n'
    hcode='load=pd.pivot_table(full,index=full["datetime"].dt.weekday,columns=full["datetime"].dt.hour,values="order_id",aggfunc="count",fill_value=0)\npeak=load.stack().idxmax()\n'
    cost='SIZE_K={"S":1.,"M":1.25,"L":1.5}\nfull["cost"]=full["cost_s"]*full["size"].map(SIZE_K)*full["qty"]\ng=full.groupby("category").agg(revenue=("amount","sum"),cost=("cost","sum"))\nmargin_raw=(g["revenue"]-g["cost"])/g["revenue"]*100\nmargin=margin_raw.round(1)\n'
    vcode='def verdict(ok):\n    return "подтвердилась" if ok else "не подтвердилась"\nmost_seats=set(by_shop.index[by_shop["seats"]==by_shop["seats"].max()])\nmost_revenue=set(by_shop.index[by_shop["revenue"]==by_shop["revenue"].max()])\nverdicts={"H1":verdict((monthly["revenue"].pct_change().dropna()>0).all()),"H2":verdict(bool(most_seats & most_revenue)),"H4":verdict((card/no_card-1)*100>=5),"H5":verdict(peak[0] in [5,6] and peak[1]<12),"H6":verdict(margin_raw["не кофе"]-margin_raw["кофе"]>=3)}\n'
    sumfn='def summary(full):\n    monthly=full.groupby(full["datetime"].dt.to_period("M"))["amount"].sum()\n    return {"revenue":full["amount"].sum(),"orders":len(full),"avg_check":round(full["amount"].mean(),1),"best_city":full.groupby("city")["amount"].sum().idxmax(),"top_drink":full["drink"].value_counts().idxmax(),"growth_pct":round((monthly.iloc[-1]/monthly.iloc[-2]-1)*100,1)}\n'
    save('09-project',{'load':full+'same_rows=len(full)==len(df)', 'monthly':full+mcode,'shops':full+bcode,'seasonal':full+scode,'loyalty':full+lcode,'heatmap':full+hcode,'margin':full+cost,'verdicts':full+mcode+bcode+lcode+hcode+cost+vcode,'summary':full+sumfn+'summary(full)'},[('quiz/1',3,'Заданы метрика, две группы и порог 5%.'),('quiz/2',3,'Сначала разложу выручку на заказы и средний чек, проверю изменение состава.')])
    def starter(lesson,task):
        text=(ROOT/(lesson+'.md')).read_text().split('## task: '+task+' |',1)[1].split('## task:',1)[0]
        return re.search(r'```python\n(.*?)```',text,re.S).group(1)
    save('10-git',{
    'log-count':starter('10-git','log-count')+'rows=log.splitlines()\nn_commits=len(rows)\nlast_hash=rows[0].split()[0]\nfirst_message=rows[-1].split(" ",1)[1]',
    'my-log':'my_log='+repr((ROOT/'work/my_git_log.txt').read_text())+'\nrows=my_log.strip().splitlines()\nn_mine=len(rows)\nmessages=[row.split(" ",1)[1] for row in rows]',
    'log-pandas':starter('10-git','log-pandas')+'commits=pd.read_csv(io.StringIO(log),sep="|",names=["hash","date","author","message"],parse_dates=["date"])\nper_day=commits.groupby("date").size().sort_index()\nbusiest=per_day.idxmax()',
    'diff-stat':starter('10-git','diff-stat')+'files=[line.split(" b/",1)[1] for line in diff.splitlines() if line.startswith("diff --git ")]\nadded=sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())\nremoved=sum(line.startswith("-") and not line.startswith("---") for line in diff.splitlines())',
    'ignore':starter('10-git','ignore').split('def is_ignored')[0]+'''def is_ignored(path,patterns):
    parts=path.split("/")
    return any((pat[:-1] in parts[:-1]) if pat.endswith("/") else fnmatch(parts[-1],pat) for pat in patterns)
tracked=[path for path in files if not is_ignored(path,patterns)]''',
    'status-sim':starter('10-git','status-sim').split('def status')[0]+'''def status(committed,working,ignore):
    return {"new":sorted(p for p in working if p not in committed and not any(fnmatch(p.split("/")[-1],pat) for pat in ignore)),"modified":sorted(p for p in working if p in committed and working[p]!=committed[p]),"deleted":sorted(p for p in committed if p not in working)}
status(committed,working,ignore)'''
    },[('quiz/1',1,'Изменения рабочей папки нужно отобрать в индекс.'),('predict/1',2,'Плюс есть у заголовка +++ и у строки кода.'),('quiz/2',3,'Без аргументов diff сравнивает папку с индексом; нужен --staged.'),('predict/2',1,'fnmatch допускает / под *, поэтому окончание .csv подходит.'),('quiz/3',1,'Удаление новым коммитом оставляет секрет в истории, пароль надо сменить.')])
    stripfn='''def strip(nb):
    clean=copy.deepcopy(nb)
    for c in clean["cells"]:
        if c["cell_type"]=="code":
            c["outputs"]=[]
            c["execution_count"]=None
    return clean
'''
    save('10b-git-github',{
    'strip':'import json\nimport copy\nnb=json.load(open("zerno_draft.ipynb",encoding="utf-8"))\n'+stripfn+'n_removed=sum(len(c.get("outputs",[])) for c in nb["cells"] if c["cell_type"]=="code")\nclean=strip(nb)',
    'diff-noise':'import copy\nimport difflib\nimport json\n'+stripfn+'''def changed_lines(a,b):
    return sum(l[:1] in ["+","-"] and not l.startswith(("+++","---")) for l in difflib.unified_diff(a.splitlines(),b.splitlines()))
old=open("zerno_draft.ipynb",encoding="utf-8").read()
new=open("zerno_rerun.ipynb",encoding="utf-8").read()
raw_changed=changed_lines(old,new)
clean_changed=changed_lines(json.dumps(strip(json.loads(old)),ensure_ascii=False,indent=1),json.dumps(strip(json.loads(new)),ensure_ascii=False,indent=1))''',
    'p-first-commit':'''cmds = []
cmds.append("git init")
cmds.append("git status")
cmds.append("git add README.md .gitignore report.ipynb")
cmds.append('git commit -m "Первая версия отчёта"')
cmds.append("git remote add origin https://github.com/anya/zerno-analytics.git")
cmds.append("git push -u origin main")
print(len(cmds))''',
    'readme':starter('10b-git-github','readme').split('def make_readme')[0]+'''def make_readme(info):
    lines=["# "+info["title"],"","## Вопрос",info["question"],"","## Данные",info["data"],"","## Главное"]
    lines += ["- "+s for s in info["findings"]]
    lines += ["","## Как запустить"]+["    "+s for s in info["run"]]
    return "\\n".join(lines)
readme=make_readme(autumn)''',
    'portfolio':starter('10b-git-github','portfolio').split('def review')[0]+'''def review(repos):
    result={}
    for name,files in repos.items():
        p=[]
        if "README.md" not in files:p.append("no_readme")
        if ".gitignore" not in files:p.append("no_gitignore")
        if not any(f.endswith(".ipynb") for f in files):p.append("no_notebook")
        if any(f.split("/")[-1]==".env" for f in files):p.append("secrets")
        if any(f.startswith("data/") for f in files):p.append("data")
        if p:result[name]=p
    return result
problems=review(repos)'''
    },[('quiz/1',1,'Нужно включить удалённый коммит в локальную историю и повторить push.')])
    save('07s-subqueries-cte',{
    'cheap':pdb+'cheap=duckdb.sql("SELECT COUNT(*) FROM df WHERE amount<(SELECT AVG(amount) FROM df)").fetchone()[0]',
    'subquery':pdb+'shops=pd.read_csv("shops.csv")\nbig_kzn=duckdb.sql("SELECT COUNT(*) FROM df WHERE shop_id IN (SELECT shop_id FROM shops WHERE city=\'Казань\') AND amount>(SELECT AVG(amount) FROM df)").fetchone()[0]',
    'not-l':pdb+'no_l=duckdb.sql("SELECT COUNT(DISTINCT client_id) FROM df WHERE client_id IS NOT NULL AND client_id NOT IN (SELECT client_id FROM df WHERE size=\'L\' AND client_id IS NOT NULL)").fetchone()[0]',
    'cte':pdb+'shops=pd.read_csv("shops.csv")\ncity_daily=duckdb.sql("WITH d AS (SELECT city,CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df JOIN shops USING(shop_id) GROUP BY city,day) SELECT city,ROUND(AVG(revenue)) AS avg_daily FROM d GROUP BY city ORDER BY avg_daily DESC").df()',
    'window':'import duckdb\n'+pdtime+'best_days=duckdb.sql("WITH d AS (SELECT shop_id,CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df GROUP BY shop_id,day),r AS (SELECT *,ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY revenue DESC,day) AS rn FROM d) SELECT shop_id,day,revenue FROM r WHERE rn=1 ORDER BY shop_id").df()',
    'order-fix':'import duckdb\n'+pdtime+'first_orders=duckdb.sql("WITH r AS (SELECT client_id,datetime,amount,ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime,order_id) AS rn FROM df WHERE client_id IS NOT NULL) SELECT client_id,datetime,amount FROM r WHERE rn=1 ORDER BY client_id").df()'
    },[('predict/1',2,'Среднее 25; остаются 30 и 40.'),('predict/2',3,'Фильтр до окна исключает 1, номера считаются заново.'),('quiz/1',3,'Агрегат ещё не существует на шаге WHERE.')])
    dbtime='import duckdb\n'+pdtime
    save('07b-sql-windows',{
    'w-share':pdb+'by_shop = duckdb.sql("SELECT shop_id, SUM(amount) AS revenue FROM df GROUP BY shop_id").df()\nshares = duckdb.sql("SELECT shop_id, revenue, ROUND(100 * revenue / SUM(revenue) OVER (), 1) AS pct FROM by_shop ORDER BY pct DESC").df()\nprint(shares)',
    'w-number':dbtime+'numbered=duckdb.sql("SELECT client_id,datetime,ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY datetime,order_id) AS n FROM df WHERE client_id IS NOT NULL").df()\nsecond_orders=(numbered["n"]==2).sum()',
    'w-ties':pdb+'top2=duckdb.sql("SELECT shop_id,drink,COUNT(*) AS n,DENSE_RANK() OVER (PARTITION BY shop_id ORDER BY COUNT(*) DESC) AS place FROM df GROUP BY shop_id,drink QUALIFY place<=2 ORDER BY shop_id,place,drink").df()',
    'w-ntile':pdb+'quart=duckdb.sql("WITH g AS (SELECT client_id,SUM(amount) AS spent FROM df WHERE client_id IS NOT NULL GROUP BY client_id),q AS (SELECT *,NTILE(4) OVER (ORDER BY spent DESC,client_id) AS quartile FROM g) SELECT quartile,COUNT(*) AS guests,SUM(spent) AS revenue,ROUND(100*SUM(spent)/SUM(SUM(spent)) OVER (),1) AS pct FROM q GROUP BY quartile ORDER BY quartile").df()\ntop_pct=quart.loc[quart["quartile"]==1,"pct"].iloc[0]',
    'w-lag':dbtime+'mom_shop=duckdb.sql("WITH m AS (SELECT shop_id,date_trunc(\'month\',datetime) AS month,SUM(amount) AS revenue FROM df GROUP BY shop_id,month) SELECT shop_id,month,revenue,ROUND(100*(revenue/LAG(revenue) OVER (PARTITION BY shop_id ORDER BY month)-1),1) AS growth_pct FROM m ORDER BY shop_id,month").df()\nfalls=mom_shop[mom_shop["growth_pct"]<0]',
    'w-lead':dbtime+'gaps=duckdb.sql("WITH x AS (SELECT client_id,CAST(datetime AS DATE) AS day,LEAD(CAST(datetime AS DATE)) OVER (PARTITION BY client_id ORDER BY datetime,order_id) AS next_day FROM df WHERE client_id IS NOT NULL) SELECT client_id,day,next_day,next_day-day AS days FROM x WHERE next_day IS NOT NULL").df()\navg_gap=round(gaps["days"].mean(),1)\nmedian_gap=gaps["days"].median()',
    'w-streak':dbtime+'streaks=duckdb.sql("WITH d AS (SELECT DISTINCT shop_id,CAST(datetime AS DATE) AS day FROM df),r AS (SELECT *,day-CAST(ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY day) AS INTEGER) AS grp FROM d),s AS (SELECT shop_id,MIN(day) AS start,MAX(day) AS finish,COUNT(*) AS days FROM r GROUP BY shop_id,grp) SELECT shop_id,start,finish,days FROM s QUALIFY ROW_NUMBER() OVER (PARTITION BY shop_id ORDER BY days DESC,start)=1 ORDER BY shop_id").df()'
    },[('quiz/1',4,'Окно видит сгруппированные строки — разные напитки.'),('predict/1',3,'RANK пропускает третье место, DENSE_RANK не пропускает.'),('quiz/2',4,'Нужны уровни, поэтому плотный ранг, не первые три строки.'),('predict/2',3,'В первой строке предыдущего значения нет; дальше +20 и -30.')])
    save('07c-sql-frames',{
    'w-running':dbtime+'cum=duckdb.sql("WITH d AS (SELECT CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df GROUP BY day) SELECT day,revenue,SUM(revenue) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running FROM d ORDER BY day").df()\nhalf_day=cum.loc[cum["running"]>=cum["revenue"].sum()/2,"day"].iloc[0]',
    'w-half':dbtime+'half=duckdb.sql("WITH d AS (SELECT shop_id,CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df GROUP BY shop_id,day),w AS (SELECT *,SUM(revenue) OVER (PARTITION BY shop_id ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,SUM(revenue) OVER (PARTITION BY shop_id) AS total FROM d) SELECT shop_id,MIN(day) AS half_day FROM w WHERE running>=total/2 GROUP BY shop_id ORDER BY shop_id").df()',
    'w-ma7':'import duckdb\nimport pandas as pd\nds=pd.read_csv("daily_sales.csv",parse_dates=["date"])\ndec=duckdb.sql("WITH w AS (SELECT date,revenue_k,ROUND(AVG(revenue_k) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),1) AS ma7 FROM ds WHERE shop_id=\'TMN-1\') SELECT * FROM w WHERE date>=DATE \'2025-12-01\' AND date<DATE \'2026-01-01\' ORDER BY date").df()\npeak_date=dec.loc[dec["ma7"].idxmax(),"date"]',
    'w-range':dbtime+'ufa=duckdb.sql("WITH d AS (SELECT CAST(datetime AS DATE) AS day,SUM(amount) AS revenue FROM df WHERE shop_id=\'UFA-1\' GROUP BY day) SELECT day,revenue,AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_rows,AVG(revenue) OVER (ORDER BY day RANGE BETWEEN INTERVAL 6 DAYS PRECEDING AND CURRENT ROW) AS ma_range FROM d ORDER BY day").df()\ndiffer=((ufa["ma_rows"]-ufa["ma_range"]).abs()>1).sum()',
    'w-firstlast':dbtime+'fl=duckdb.sql("SELECT DISTINCT client_id,FIRST_VALUE(drink) OVER w AS first_drink,LAST_VALUE(drink) OVER w AS last_drink,COUNT(*) OVER w AS orders FROM df WHERE client_id IS NOT NULL WINDOW w AS (PARTITION BY client_id ORDER BY datetime,order_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) ORDER BY client_id").df()\nrepeat=fl[fl["orders"]>=2]\nswitch_pct=round((repeat["first_drink"]!=repeat["last_drink"]).mean()*100,1)'
    },[('predict/1',2,'RANGE включает обе строки первого дня и затем весь второй день.'),('quiz/1',2,'Строки после пропуска могут уходить за календарную неделю.')])
    save('08c-terminal-memory',{
    'w-lines':'files=["orders_3m.csv","shops.csv","menu.csv"]\nlines={}\nfor name in files:\n    with open(name,encoding="utf-8") as f:\n        lines[name]=sum(1 for line in f)\nn_orders=lines["orders_3m.csv"]-1\nn_shops=lines["shops.csv"]-1',
    'grep-count':'with open("orders_3m.csv",encoding="utf-8") as f:\n    lines=f.read().splitlines()\nhead3=lines[:3]\nn_delivery=sum("доставка" in line for line in lines)\nn_seasonal_delivery=sum("доставка" in line and "Сезонный" in line for line in lines)',
    'ls-parse':starter('08c-terminal-memory','ls-parse')+'rows=[l.split() for l in listing.splitlines() if not l.startswith("total")]\nsizes={r[-1]:int(r[4]) for r in rows}\nbiggest=max(sizes,key=sizes.get)\ntotal_kb=round(sum(sizes.values())/1024)',
    'cat-codes':'import pandas as pd\nsizes=pd.Series(["M","S","M","L","M","S"])\ncat=sizes.astype("category")\ncats=cat.cat.categories.tolist()\ncodes=cat.cat.codes.tolist()',
    'mem-category':p+'''def shrink(df):
    small=df.copy()
    for c in small:
        if (pd.api.types.is_string_dtype(small[c]) or small[c].dtype==object) and small[c].nunique()/len(small)<.05:
            small[c]=small[c].astype("category")
    return small
small=shrink(df)
converted=[c for c in df if str(small[c].dtype)=="category" and str(df[c].dtype)!="category"]
saved_pct=round((1-small.memory_usage(deep=True).sum()/df.memory_usage(deep=True).sum())*100,1)'''
    },[('predict/1',2,'Чтение построчно учитывает и заголовок: 2089+1.'),('quiz/1',3,'Все номера уникальны, справочник не уменьшится и добавит коды.')])
    sql_load='''import duckdb
import pandas as pd
names=["shops","menu","guests","promos","orders","items"]
dates={"orders":["ordered_at"],"guests":["reg_date"],"promos":["start_date","end_date"]}
for name in names:
    t=pd.read_csv(f"zdb_{name}.csv",parse_dates=dates.get(name,[]))
    duckdb.sql(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM t")
'''
    city_q="SELECT s.city,date_trunc('month',o.ordered_at) AS month,COUNT(DISTINCT o.order_id) AS orders,SUM(i.qty*i.price) AS revenue FROM orders o JOIN items i USING(order_id) JOIN shops s USING(shop_id) GROUP BY city,month ORDER BY city,month"
    checks_q="WITH totals AS (SELECT order_id,SUM(qty*price) AS total FROM items GROUP BY order_id) SELECT o.channel,CASE WHEN o.guest_id IS NULL THEN 'без карты' ELSE 'с картой' END AS card,COUNT(*) AS orders,ROUND(AVG(total),1) AS avg_check FROM orders o JOIN totals USING(order_id) GROUP BY channel,card ORDER BY channel,card"
    second_q="WITH r AS (SELECT guest_id,ordered_at,ROW_NUMBER() OVER (PARTITION BY guest_id ORDER BY ordered_at,order_id) AS rn,LEAD(ordered_at) OVER (PARTITION BY guest_id ORDER BY ordered_at,order_id) AS next_at FROM orders WHERE guest_id IS NOT NULL),f AS (SELECT guest_id,date_diff('day',CAST(ordered_at AS DATE),CAST(next_at AS DATE)) AS days FROM r WHERE rn=1 AND ordered_at<TIMESTAMP '2026-08-01') SELECT source,COUNT(*) AS guests,ROUND(100*AVG(CASE WHEN days<=30 THEN 1 ELSE 0 END),1) AS back30_pct,MEDIAN(days) AS median_days FROM f JOIN guests USING(guest_id) GROUP BY source ORDER BY source"
    ret_q="WITH f AS (SELECT guest_id,date_trunc('month',MIN(ordered_at)) AS cohort FROM orders WHERE guest_id IS NOT NULL GROUP BY guest_id),a AS (SELECT DISTINCT o.guest_id,cohort,date_diff('month',cohort,date_trunc('month',ordered_at)) AS k FROM orders o JOIN f USING(guest_id)),c AS (SELECT cohort,k,COUNT(*) AS guests FROM a GROUP BY cohort,k) SELECT cohort,k,guests,ROUND(100*guests/FIRST_VALUE(guests) OVER (PARTITION BY cohort ORDER BY k),1) AS pct FROM c ORDER BY cohort,k"
    src_q="WITH f AS (SELECT guest_id,date_trunc('month',MIN(ordered_at)) AS cohort FROM orders WHERE guest_id IS NOT NULL GROUP BY guest_id),a AS (SELECT DISTINCT o.guest_id,date_diff('month',cohort,date_trunc('month',ordered_at)) AS k FROM orders o JOIN f USING(guest_id) WHERE cohort<DATE '2026-07-01'),g AS (SELECT f.guest_id,source,MAX(CASE WHEN a.k=1 THEN 1 ELSE 0 END) AS m1,MAX(CASE WHEN a.k=2 THEN 1 ELSE 0 END) AS m2 FROM f JOIN guests USING(guest_id) LEFT JOIN a USING(guest_id) WHERE cohort<DATE '2026-07-01' GROUP BY f.guest_id,source) SELECT source,COUNT(*) AS cohort_size,ROUND(100*AVG(m1),1) AS m1,ROUND(100*AVG(m2),1) AS m2 FROM g GROUP BY source ORDER BY source"
    margin_q="SELECT category,SUM(i.qty*i.price) AS revenue,SUM(i.qty*(i.price-m.cost)) AS margin,ROUND(100*SUM(i.qty*(i.price-m.cost))/SUM(i.qty*i.price),1) AS margin_pct FROM items i JOIN menu m USING(item_id) GROUP BY category ORDER BY margin_pct DESC"
    promo_q="WITH m AS (SELECT name,date_trunc('month',ordered_at) AS month,SUM(qty) AS cups FROM items JOIN orders USING(order_id) JOIN menu USING(item_id) WHERE name IN ('Раф','Лимонад') GROUP BY name,month) SELECT name,month,cups,ROUND(100*(cups/LAG(cups) OVER (PARTITION BY name ORDER BY month)-1),1) AS growth_pct FROM m ORDER BY name,month"
    save('11-sql-project',{
    'p-tables':sql_load+'sizes={name:duckdb.sql(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in names}\nempty_orders=duckdb.sql("SELECT COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM items i WHERE i.order_id=o.order_id)").fetchone()[0]',
    'p-city-month':sql_load+'city_month=duckdb.sql('+repr(city_q)+').df()\naug=city_month[city_month["month"].dt.month==8]\nbest_city=aug.loc[aug["revenue"].idxmax(),"city"]',
    'p-unsold':sql_load+'unsold=[r[0] for r in duckdb.sql("SELECT name FROM menu m WHERE NOT EXISTS (SELECT 1 FROM items i WHERE i.item_id=m.item_id) ORDER BY name").fetchall()]\nlemonade_first=duckdb.sql("SELECT CAST(MIN(ordered_at) AS DATE) FROM orders JOIN items USING(order_id) JOIN menu USING(item_id) WHERE name=\'Лимонад\'").fetchone()[0]',
    'p-ghosts':sql_load+'ghosts=duckdb.sql("WITH g AS (SELECT guest_id,source,NOT EXISTS (SELECT 1 FROM orders o WHERE o.guest_id=g.guest_id) AS no_order FROM guests g) SELECT source,COUNT(*) AS guests,SUM(CAST(no_order AS INT)) AS no_orders,ROUND(100*AVG(CAST(no_order AS INT)),1) AS pct FROM g GROUP BY source ORDER BY source").df()',
    'p-checks':sql_load+'checks=duckdb.sql('+repr(checks_q)+').df()\na=duckdb.sql("WITH t AS (SELECT order_id,SUM(qty*price) AS total FROM items GROUP BY order_id) SELECT guest_id IS NOT NULL AS card,AVG(total) AS avg_check FROM orders JOIN t USING(order_id) GROUP BY card").df().set_index("card")["avg_check"]\ndiff_pct=round((a.loc[True]/a.loc[False]-1)*100,1)',
    'p-margin':sql_load+'margin=duckdb.sql('+repr(margin_q)+').df()',
    'p-promo':sql_load+'promo_items=duckdb.sql('+repr(promo_q)+').df()',
    'p-second':sql_load+'second=duckdb.sql('+repr(second_q)+').df()',
    'p-cohorts':sql_load+'ret=duckdb.sql('+repr(ret_q)+').df()\nmarch_m1=ret.loc[(ret["cohort"].dt.month==3) & (ret["k"]==1),"pct"].iloc[0]',
    'p-cohort-source':sql_load+'ret_src=duckdb.sql('+repr(src_q)+').df()\ns=ret_src.set_index("source")["m2"]\nm2_gap=round(s.loc["приложение"]-s.loc["касса"],1)'
    },[('quiz/1',2,'Правый край наблюдения: будущий месяц нельзя считать нулём.'),('quiz/2',1,'Сравнение групп не предсказывает изменение от выдачи карты.')])
