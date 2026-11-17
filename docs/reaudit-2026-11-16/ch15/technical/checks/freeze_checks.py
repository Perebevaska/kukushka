import json,hashlib,re,pathlib,shutil,ast
ROOT=pathlib.Path('/Users/dmitriikormin/Documents/Projects/ds-course');B=ROOT/'docs/reaudit-2026-11-16/ch15/technical/checks';B.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
allrows=json.load(open('/private/tmp/kuch15round/course.json'));ts=[t for t in allrows if t['lesson'].startswith('ch15/') and t['kind']=='task'];T={(t['lesson'].split('/')[-1],t['id']):t for t in ts}
(B/'tasks.json').write_text(json.dumps(ts,ensure_ascii=False,indent=2));contracts=[]
for t in ts:
 p=ROOT/'content'/str(t['lesson']+'.md');text=p.read_text();m=re.search(r'^## task: '+re.escape(t['id'])+r'\s*\|.*?(?=^## task:|\Z)',text,re.M|re.S);s=m.group()
 contracts.append(dict(lesson=t['lesson'],id=t['id'],public_condition=s.split('###')[0],hints=re.findall(r'### hint\n(.*?)(?=###|\Z)',s,re.S),source_sha256=sha(p),starter=t['starter'],setup=t['setup'],check=t['check'],solution=t['solution']))
(B/'source57x4-before.json').write_text(json.dumps(contracts,ensure_ascii=False,indent=2))
(B/'data').mkdir(exist_ok=True)
for f in sorted({f for t in ts for f in t['files']}):shutil.copy2(ROOT/'site/data'/f,B/'data'/f)
shutil.copy2(ROOT/'site/assets/harness.py',B/'frozen_harness.py')
# Each alternative changes a calculation or data-access path. No answer-key substitutions.
A={
('01-artifact','md5-text'):('hashlib.md5(', 'hashlib.new("md5", '),
('01-artifact','p-save'):('m2.predict(X) == m.predict(X)', 'm.predict(X) == m2.predict(X)'),
('01-artifact','size'):('os.path.getsize(', '__import__("pathlib").Path.stat(__import__("pathlib").Path('),
('01-artifact','data-md5'):('return hashlib.md5(f.read()).hexdigest()', 'h = hashlib.md5()\n        for block in iter(lambda: f.read(8192), b""):\n            h.update(block)\n        return h.hexdigest()'),
('01-artifact','card'):('[str(f) for f in model.feature_names_in_]','list(map(str,model.feature_names_in_))'),
('01-artifact','golden'):('np.abs(got - gold["expected"]).max()', 'np.max(np.abs(np.subtract(got, gold["expected"])))'),
('01-artifact','contract'):('new = sorted(set(df[c].dropna()) - set(values))','new = sorted(df.loc[df[c].notna() & ~df[c].isin(values), c].unique())'),
('01-artifact','decide'):('p >= card["threshold"]','np.greater_equal(p, card["threshold"])'),
('01-artifact','versions'):('np.sort(p11)[::-1][n10 - 1]','np.partition(p11, len(p11)-n10)[len(p11)-n10]'),
('01-artifact','release'):('np.abs(model.predict_proba(gold.drop(columns=["expected"]))[:, 1] - gold["expected"]).max()', 'max(abs(a-b) for a,b in zip(model.predict_proba(gold.drop(columns=["expected"]))[:, 1],gold["expected"]))'),
('02-service','json-rt'):('json.loads(request_text)','json.JSONDecoder().decode(request_text)'),
('02-service','p-json'):('json.loads(text)','json.JSONDecoder().decode(text)'),
('02-service','is-int'):('isinstance(x, int) and not isinstance(x, bool)','type(x) is int'),
('02-service','validate'):('v < lo or (hi is not None and v > hi)','not (lo <= v and (hi is None or v <= hi))'),
('02-service','handler'):('p >= CARD["threshold"]','not p < CARD["threshold"]'),
('02-service','http'):('json.loads(text)','json.JSONDecoder().decode(text)'),
('02-service','reasons'):('contrib = contrib[contrib > 0].sort_values(ascending=False)','contrib = contrib.loc[contrib.gt(0)].nlargest(k)'),
('02b-service-run','batch'):('pd.DataFrame([predict_one(p) for p in payloads])','pd.DataFrame.from_records(map(predict_one, payloads))'),
('02b-service-run','tail'):('np.mean(times)','sum(times) / len(times)'),
('02b-service-run','latency'):('np.mean(times)','sum(times) / len(times)'),
('02b-service-run','tests'):('return 422 if validate(payload) else 200','return {True:422,False:200}[bool(validate(payload))]'),
('02b-service-run','tests-write'):('dict(GOOD, delivery_share=40)','dict(GOOD, delivery_share=1.01)'),
('03-experiments','run-dict'):('journal.loc[journal["cv_auc"].idxmax(), "run_id"]','max(runs, key=lambda r:r["cv_auc"])["run_id"]'),
('03-experiments','p-cv'):('scores.mean()','sum(scores) / len(scores)'),
('03-experiments','seed'):('np.abs(p1 - p3).max()','max(abs(a-b) for a,b in zip(p1,p3))'),
('03-experiments','log-csv'):('pd.DataFrame([run]).to_csv(path, mode="a", header=not os.path.exists(path), index=False)','pd.DataFrame([run]).reindex(columns=pd.read_csv(path,nrows=0).columns if os.path.exists(path) else list(run)).to_csv(path, mode="a", header=not os.path.exists(path), index=False)'),
('03-experiments','grid'):('journal.loc[journal["cv_auc_mean"].idxmax()]','journal.sort_values("cv_auc_mean", ascending=False).iloc[0]'),
('03-experiments','paired'):('diff = rf - lr','diff = np.subtract(rf, lr)'),
('03-experiments','seed-noise'):('max(by_seed) - min(by_seed)','np.ptp(by_seed)'),
('03-experiments','lucky'):('max(roc_auc_score(y_all[:n], np.random.default_rng(s).random(n)) for s in range(40))','sorted(roc_auc_score(y_all[:n], np.random.default_rng(s).random(n)) for s in range(40))[-1]'),
('03-experiments','reproduce'):('json.loads(row["params"])','json.JSONDecoder().decode(row["params"])'),
('03-experiments','honest'):('chosen = cv_table.idxmax()','chosen = max(cv_table.index,key=cv_table.get)'),
('04-deploy','versions'):('"\\n".join(f"{p}=={version(p)}" for p in ["numpy", "pandas", "scikit-learn"])','"\\n".join(map(lambda p:p+"=="+version(p),["numpy","pandas","scikit-learn"]))'),
('04-deploy','p-jsonl'):('[json.loads(line) for line in f]','list(map(json.loads, f))'),
('04-deploy','cron'):('"30 6 * * 1"','"30  6 * * 1"'),
('04-deploy','batch-job'):('df.apply(bad_reason, axis=1)','pd.Series([bad_reason(r) for _,r in df.iterrows()],index=df.index)'),
('04-deploy','idempotent'):('int((allf["guest_id"].value_counts() > 1).sum())','len(allf.loc[allf["guest_id"].duplicated(),"guest_id"].unique())'),
('04-deploy','parse-log'):('pd.json_normalize(log["payload"].tolist())','pd.DataFrame(log["payload"].tolist())'),
('04-deploy','latency-hours'):('log.groupby(log["ts"].dt.hour).size()','log["ts"].dt.hour.value_counts().sort_index()'),
('04-deploy','write-log'):('pd.DataFrame([json.loads(line) for line in f])','pd.DataFrame.from_records(map(json.loads,f))'),
('04-deploy','daily'):('(s != 200).mean()','1-s.eq(200).mean()'),
('04-deploy','cron-match'):('value % int(part[2:]) == 0','value in range(0, 10000, int(part[2:]))'),
('05-project','timeline'):('(s == 500).mean()','s.eq(500).mean()'),
('05-project','slow'):('g.quantile(0.5)','g.median()'),
('05-project','web500'):('e500["client"].value_counts()','e500.groupby("client").size().sort_values(ascending=False)'),
('05-project','kopecks'):('pd.json_normalize(ok["payload"].tolist())','pd.DataFrame.from_records(ok["payload"])'),
('05-project','rollback'):('>= 1 / 3','>= (1.0 / 3.0)'),
('05-project','guard'):('row["visits_90d"] < 0','not row["visits_90d"] >= 0'),
('05-project','faster'):('np.median(times)','np.quantile(times,.5)'),
('05-project','advice'):('advice = 2','advice = [2][0]'),
('06-final-project','audit'):('pd.read_sql(sql, con).iloc[0, 0]','con.execute(sql).fetchone()[0]'),
('06-final-project','target'):('active["end_date"].notna() & (active["end_date"] <= c + pd.offsets.MonthEnd(months))','active["end_date"].between(c, c + pd.offsets.MonthEnd(months), inclusive="right")'),
('06-final-project','features'):('o90.groupby("client_id").size()','o90.groupby("client_id")["order_date"].count()'),
('06-final-project','leak'):('ok.groupby("client_id")["order_date"].max()','ok.groupby("client_id")["order_date"].agg("max")'),
('06-final-project','models'):('cross_val_score(m, X, y, groups=groups, cv=cv, scoring="roc_auc").mean()','np.mean(cross_val_score(m, X, y, groups=groups, cv=cv, scoring="roc_auc"))'),
('06-final-project','profit'):('index[:150]','index[:10]'),
('06-final-project','package'):('.head(150)','.head(3)')}
# Explicit wrong outcomes; some mutations deliberately test an unguarded semantic obligation.
W={
'md5-text':'h2 = h1','p-save':'print(False)','size':'ratio = 0','data-md5':'changed = False','card':'card["name"]="wrong"\ncard["version"]="0.0"\njson.dump(card,open("card.json","w"))','golden':'golden["city"] = "Москва"\ngolden.to_csv("golden.csv",index=False)','contract':'_old=check_input\ncheck_input=lambda frame: _old(frame) if frame is not ok else ["city: ошибка"]','decide':'n_in=0','versions':'flip=0','release':'res_bad["golden"]=True','json-rt':'has_null=False','p-json':'print(False)','is-int':'is_int=lambda x:isinstance(x,int)','validate':'_old=validate\nvalidate=lambda p:[e for e in _old(p) if not e.startswith("visits_90d")]','handler':'r_bad={"status":500,"errors":["city"]}','http':'a3="{}"','reasons':'top_guest=[]','batch':'res["status"]=200','tail':'slow=0','latency':'batch_per_row=0','tests':'validate_v1=validate_v0','tests-write':'cases=cases[:1]','run-dict':'journal["cv_auc"]=0','p-cv':'print(0)','seed':'max_gap=0','log-csv':'back.loc[1,"cv_auc_mean"]=0\nback.to_csv("journal.csv",index=False)','grid':'journal["cv_auc_std"]=0','paired':'diff=-diff','seed-noise':'seed_range=0','lucky':'shrinks=False','reproduce':'check_df["reproduced"]=0','honest':'optimism=1','p-jsonl':'print(0)','cron':'crons["weekly"]="30 6 * * 2"','batch-job':'sc=pd.read_csv("out/scores_2026-12-07.csv")\nsc.loc[0,"guest_id"]=sc.loc[1,"guest_id"]\nsc.to_csv("out/scores_2026-12-07.csv",index=False)','idempotent':'rows_after_2=400','parse-log':'payload_df["visits_90d"]=0','latency-hours':'peak_hour=-1','write-log':'mine.loc[0,"client"]="wrong"','daily':'daily.index=list(reversed(daily.index))','cron-match':'n_runs=29','timeline':'daily.index=list(reversed(daily.index))','slow':'lat["n"]=0','web500':'web_fail_after=0','kopecks':'ratio_32=1','rollback':'rollback_harm=0','guard':'_old=range_problems\nrange_problems=lambda row:[p for p in _old(row) if not p.startswith("visits_90d")]','faster':'speed["ms"]=1\nspeedup=1','advice':'advice=1','audit':'n_returns=0','target':'_old=build_target\ndef build_target(cutoff,months=3):\n    r=_old(cutoff,months)\n    return r.fillna(0)','features':'means["orders_90"]=0','leak':'n_future=0','models':'oof_calibration=pd.DataFrame()\nhistorical_budget=pd.Series(dtype=float)','profit':'profit_model=0','package':'out.loc[0,"city"]="Москва"\nout.to_csv("call_list.csv",index=False)'}
rows=[]
def add(k,label,code,expected,description='',**kw):
 t=T[k];ast.parse(code);rows.append(dict(lesson=t['lesson'],task=t['id'],label=label,expected=expected,description=description,code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),**kw))
for k,t in T.items():
 s=t['solution'];add(k,'author',s,True,'Полный авторский код baseline740b115')
 a,b=A[k]
 if k==('01-artifact','size'):
  alt='from pathlib import Path\n'+s.replace('os.path.getsize("small.joblib")','Path("small.joblib").stat().st_size').replace('os.path.getsize("big.joblib")','Path("big.joblib").stat().st_size')
 else:
  assert a in s,(k,a);alt=s.replace(a,b)
 if k==('01-artifact','decide'):alt='import numpy as np\n'+alt
 if k==('01-artifact','card') and alt==s:raise ValueError(k)
 if k==('06-final-project','package'):alt=alt.replace('"n_calls": int(len(out)),','"call_limit": 3,\n    "n_calls": int(len(out)),')
 add(k,'alternative',alt,True,'Другой доступ к данным/расчёт; для package лимит3; для profit очередь10')
 wrong=s+'\n'+W[t['id']]+'\n'
 if t['id']=='versions' and k[0]=='04-deploy':wrong=s+'\nsk_version="0.0"\n'
 add(k,'wrong',wrong,False,'Нарушение заявленного результата; Parsons произвольные изменения harness-only',harness_only=t['id'].startswith('p-'))
# Historical69 literal extraction, never reconstruct from current solution.
fp=ROOT/'tools/checks/fixtures/reaudit_20261115.jsonl';historical=[]
for ln,line in enumerate(fp.read_text().splitlines(),1):
 r=json.loads(line)
 if r['lesson'].startswith('ch15/'):
  add((r['lesson'].split('/')[-1],r['task']),'historical69-'+str(ln),r['code'],r['expected'],r['description'],origin=dict(path=str(fp.relative_to(ROOT)),file_sha256=sha(fp),line=ln,method='Literal JSON field code, no source expression evaluation'))
  historical.append(rows[-1])
(B/'historical-literal.json').write_text(json.dumps(historical,ensure_ascii=False,indent=2))
# Adversarial pairs plus direct semantic oracles. Oracles run the actual frozen setup, not a copied corrected formula.
k=('03-experiments','grid');s=T[k]['solution'];add(k,'wrong-model-param-labels',s+'\njournal.loc[:4,"param"] = -99\n',False,'Перестановка/подмена подписей конфигурации при сохранении чисел AUC')
k=('03-experiments','log-csv');s=T[k]['solution'];add(k,'wrong-second-key-order',s.replace('for r in [r1, r2, r3]:','r2 = {"run_id":r2["run_id"],"note":r2["note"],"model":r2["model"],"cv_auc_mean":r2["cv_auc_mean"]}\nfor r in [r1, r2, r3]:'),False,'Те же записи словаря, иной порядок ключей не меняет смысл CSV')
add(k,'alternative-second-key-order',s.replace('pd.DataFrame([run]).to_csv(path, mode="a", header=not os.path.exists(path), index=False)',A[k][1]).replace('for r in [r1, r2, r3]:','r2 = {"run_id":r2["run_id"],"note":r2["note"],"model":r2["model"],"cv_auc_mean":r2["cv_auc_mean"]}\nfor r in [r1, r2, r3]:'),True,'Независимое выравнивание столбцов по заголовку')
k=('05-project','guard');s=T[k]['solution']
for name,old,new,expect in [('zero-reject','row["visits_90d"] < 0','row["visits_90d"] <= 0',False),('first-only','return problems','return problems[:1]',False),('reverse-order','return problems','return list(reversed(problems))',True),('duplicate-error','return problems','return problems + problems',False)]:add(k,name,s.replace(old,new),expect,'Границы и полнота списка нарушений')
# Public guard promises ranges only: bool is not separately prohibited there. Keep diagnostic separate.
add(k,'guard-nan-visits-oracle',s+'\nassert range_problems(dict(avg_check=800,delivery_share=.5,visits_90d=float("nan"))), "NaN is not >=0"',True,'Смысл visits>=0: нечисловое NaN не удовлетворяет диапазону',check_override='')
for task in ['leak','models','profit','package']:
 k=('06-final-project',task)
 add(k,'working-target-unknown-oracle','assert build_target("2026-09-30").isna().all(), "Рабочие уходы ещё неизвестны"\n',True,'Незрелый квартал не подменяется нулями',check_override='')
 add(k,'negative-return-zero-denominator-oracle','''c=pd.Timestamp("2026-06-30")
client=active_at(c).sort_values("start_date").client_id.iloc[0]
orders=orders.iloc[:2].copy()
orders["client_id"]=client
orders["status"]="доставлен"
orders["late_min"]=0
orders["order_date"]=[c-pd.Timedelta(days=30),c-pd.Timedelta(days=120)]
orders["amount"]=[-1,0]
v=build_features(c).loc[client,"revenue_trend"]
assert v==0, ("Нулевой знаменатель должен давать0",v)
''',True,'Сохранены возвраты; нулевой знаменатель по публичной формуле кодируется0',check_override='')
k=('06-final-project','target');s=T[k]['solution'];add(k,'closure-correct',s+'''
def make_bound(frame):
    def target(cutoff, months=3):
        c=pd.Timestamp(cutoff)
        a=frame[(frame.start_date<=c)&(frame.end_date.isna()|(frame.end_date>c))]
        if c+pd.offsets.MonthEnd(months)>pd.Timestamp("2026-09-30"):
            return pd.Series(pd.NA,index=a.client_id.values,dtype="Int64")
        return pd.Series((a.end_date.notna()&(a.end_date<=c+pd.offsets.MonthEnd(months))).astype(int).values,index=a.client_id.values)
    return target
build_target=make_bound(base)
''',True,'Реальное замыкание с отдельным captured frame')
k=('06-final-project','package');s=T[k]['solution'];small=s.replace('.head(150)','.head(3)').replace('"n_calls": int(len(out)),','"call_limit": 3,\n    "n_calls": int(len(out)),')
for label,extra in [
 ('wrong-three-id','out.loc[0,"client_id"]=out.loc[1,"client_id"]\nout.to_csv("call_list.csv",index=False)'),
 ('wrong-three-order','out=out.iloc[::-1]\nout.to_csv("call_list.csv",index=False)'),
 ('wrong-three-city','out.loc[0,"city"]="Москва"\nout.to_csv("call_list.csv",index=False)'),
 ('wrong-three-proba','out.loc[0,"p_churn"]=0\nout.to_csv("call_list.csv",index=False)'),
 ('wrong-three-rounded-total','passport["expected_profit"]=int(out.exp_profit.sum())\njson.dump(passport,open("passport.json","w"))'),
 ('wrong-golden-permuted-features','golden[NUM[0]]=golden[NUM[0]].iloc[::-1].values\ngolden.to_csv("golden.csv",index=False)'),
 ('wrong-golden-proba','golden["expected"]=.123\ngolden.to_csv("golden.csv",index=False)'),
 ('wrong-passport-feature-order','passport["features"]=list(reversed(CAT+NUM))\njson.dump(passport,open("passport.json","w"))'),
 ('wrong-passport-limit','passport["call_limit"]=True\njson.dump(passport,open("passport.json","w"))')]:add(k,label,small+'\n'+extra+'\n',False,'Пакет при лимите3: связность файла модели,20контрольных строк,паспорта и очереди')
# A fixed wrong global estimate vs working function preserves baseline aggregates: real functional checks must reject it.
k=('06-final-project','features');s=T[k]['solution'];add(k,'wrong-fixed-cutoff',s+'\n_old=order_features\norder_features=lambda cutoff:_old("2026-06-30")\n',False,'Функция должна уважать дату аргумента')
k=('01-artifact','contract');s=T[k]['solution'];add(k,'wrong-ignore-city',s.replace('for c, values in KNOWN.items():','for c, values in KNOWN.items():\n        if c == "city": continue'),False,'Проверка неизвестной категории в city отдельно от fav_category')
module_path=ROOT/'docs/audit-2026-11-13/ch15/student-project/src/features.py'
module_source=module_path.read_text()
(B/'historical-features-module.py').write_text(module_source)
k=('06-final-project','target')
add(k,'imported-module-correct',T[k]['solution']+'\nimport importlib.util\n'+"open('frozen_features.py','w').write("+repr(module_source)+")\n"+"_spec=importlib.util.spec_from_file_location('frozen_features','frozen_features.py')\n_mod=importlib.util.module_from_spec(_spec)\n_spec.loader.exec_module(_mod)\nbuild_target=_mod.build_target\n",True,'Настоящий импорт самостоятельного файла; версия источника фиксирована',origin=dict(path=str(module_path.relative_to(ROOT)),file_sha256=sha(module_path)))
k=('01-artifact','p-save');add(k,'process-indistinguishable-print', 'print(True)\n',False,'Вывод совпал, сохранения/загрузки нет; ограничения процесса отдельно от видимых перестановок Parsons',harness_only=True,process_indistinguishable=True)
k=('05-project','guard');add(k,'bool-visits-diagnostic',T[k]['solution']+'\nprint("bool_visits",range_problems(dict(avg_check=800,delivery_share=.5,visits_90d=True)))\n',True,'В условии guard только диапазоны, запрета bool здесь нет; не переносить контракт validate молча')
k=('02-service','validate');add(k,'nan-rejected-oracle',T[k]['solution']+'\nassert validate(dict(GOOD,avg_check=float("nan")))\nassert validate(dict(GOOD,delivery_share=float("nan")))\n',True,'NaN не удовлетворяет заданным конечным диапазонам',check_override='')
(B/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
for name in ['run_native_portable.py','run_pyodide_portable.mjs']:
 source=(ROOT/'docs/reaudit-2026-11-16/ch14/technical/checks'/name).read_text().replace("t['check'],t['setup']","row.get('check_override',t['check']),t['setup']").replace('run(row.code,t.check,t.setup','run(row.code,row.check_override ?? t.check,t.setup')
 if name.endswith('.mjs'):
  source=source.replace("const t=tasks.find(t=>t.lesson===row.lesson&&t.id===row.task);for","const t=tasks.find(t=>t.lesson===row.lesson&&t.id===row.task); const folder='/tmp/check_'+index;try{py.FS.mkdir(folder)}catch{};py.FS.chdir(folder);for").replace("'/home/pyodide/'+f","folder+'/'+f")
 (B/name).write_text(source)
manifest={'baseline':'740b115','frozen_before_execution':True,'tasks':len(ts),'programs':len(rows),'expected_true':sum(r['expected'] for r in rows),'expected_false':sum(not r['expected'] for r in rows),'files':{str(p.relative_to(B)):sha(p) for p in B.rglob('*') if p.is_file() and p.name!='freeze-manifest.json'}}
(B/'freeze-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
lines=['# Замороженное покрытие57×4 до исполнения','', 'Поля: публичная цель/метод; полный author; альтернативный расчёт; правдоподобная ошибка. Все исходы пока ожидаемые; ни одной программы не запускали. Parsons произвольные мутации H относятся только к harness.','', '|ID|Публичные условие/заготовка/hints/setup/check/solution|Author N/P|Alternative N/P|Wrong N/P|','|---|---|---|---|---|']
for t in ts:lines.append('|'+t['lesson']+'/'+t['id']+'|Прочитаны и зафиксированы|—/— (T)|—/— (T)|—/— (F)'+(' H' if t['id'].startswith('p-') else '')+'|')
(B/'coverage57-before.md').write_text('\n'.join(lines)+'\n')
print(manifest['tasks'],manifest['programs'],manifest['expected_true'],manifest['expected_false'])
