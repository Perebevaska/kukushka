from pathlib import Path
import json,hashlib,ast,shutil,importlib.util
w=Path('/private/tmp/kuch13round');d=w/'checks';root=Path('/Users/dmitriikormin/Documents/Projects/ds-course')
tasks=[t for t in json.loads((w/'course.json').read_text()) if t['kind']=='task' and t['lesson'].startswith('ch13/')]
# Replacements and appended calculations are explicit per task. No execution here.
alt={
 'tokenize': [('return re.findall(r"[а-яё]+", text.lower())','return re.sub(r"[^а-яё]+", " ", text.lower()).split()')],
 'clean':[('return re.sub(r" +", " ", text).strip()','return " ".join(text.split())')],
 'vocab':[('total = sum(words.values())','total = sum(len(re.findall(r"[а-яё]+", s.lower())) for s in r.text)')],
 'p-stop':[('import re\nstop','stop'),('keep = {"не", "но"}','import re\nkeep = {"не", "но"}')],
 'neg-words':[('ne_share_neg = round(float(neg["text"].map(lambda t: "не" in tokenize(t)).mean()), 3)','ne_share_neg = round(sum("не" in tokenize(t) for t in neg.text)/len(neg), 3)')],
 'bag':[('bow.append([tokens.count(w) for w in vocab])','from collections import Counter\n    c = Counter(tokens)\n    bow.append([c[w] for w in vocab])')],
 'hapax':[('share_once_tokens = round(len(once) / sum(words.values()), 4)','share_once_tokens = round(sum(words[t] for t in once) / sum(words.values()), 4)')],
 'bigrams':[('top_bad = sorted(diff, key=lambda k: (-diff[k], k))[:5]','top_bad = [k for k,v in sorted(diff.items(), key=lambda kv: (-kv[1],kv[0]))[:5]]')],
 'rule':[('rule = tokens.map(lambda s: int("не" in s or "но" in s))','rule = tokens.map(lambda s: int(bool(s & {"не", "но"})))')],
 'stem-pairs':[('return word[:n] if len(word) > n else word','return word[:n]')],
 'stem':[('return word[:n] if len(word) > n else word','return word[:n]')],
 'lemma-text':[('return " ".join(to_lemma[w] for w in tokenize(text))','return " ".join(map(to_lemma.__getitem__, tokenize(text)))')],
 'lemmas':[('n_changed = sum(1 for w in set(tokens) if to_lemma[w] != w)','n_changed = len({w for w in tokens if to_lemma[w] != w})')],
 'lemma-top':[('forms_byt = sorted({w for w in tokens if to_lemma[w] == "быть"})','forms_byt = sorted(set(tokens) & {w for w,l in to_lemma.items() if l == "быть"})')],
 'lemma-fix':[('top_drink = max(["кофе", "капучино", "латте", "раф"], key=lambda d: c[d])','top_drink = max({d:c[d] for d in ["кофе", "капучино", "латте", "раф"]}, key=c.get)')],
 'count':[('n_kofe = int(X[:, cv.vocabulary_["кофе"]].sum())','n_kofe = int(X.sum(axis=0)[0,cv.vocabulary_["кофе"]])')],
 'p-tfidf':[('import numpy as np\nfrom sklearn.feature_extraction.text import TfidfVectorizer','from sklearn.feature_extraction.text import TfidfVectorizer\nimport numpy as np')],
 'idf':[('idf = pd.Series(tf.idf_, index=tf.get_feature_names_out())','idf = pd.Series(dict(zip(tf.get_feature_names_out(), tf.idf_))).iloc[::-1]')],
 'idf-by-hand':[('idf_manual = round(np.log((1 + n) / (1 + df_word)) + 1, 4)','idf_manual = round(np.log1p(n)-np.log1p(df_word)+1,4)')],
 'ngrams':[('has_ne_pridu = "не приду" in cv3.vocabulary_','has_ne_pridu = "не приду" in set(cv3.get_feature_names_out())')],
 'min-df':[('dropped_examples = sorted(set(full.vocabulary_) - set(cut.vocabulary_))[:5]','dropped_examples = sorted(w for w in full.vocabulary_ if w not in cut.vocabulary_)[:5]')],
 'keywords':[('idx = [j for j in np.argsort(-row, kind="stable") if row[j] > 0][:k]','idx = sorted(np.flatnonzero(row), key=lambda j: (-row[j],j))[:k]')],
 'train-only':[('n_unseen = len([w for w in test_words if w not in tf.vocabulary_])','n_unseen = len(test_words - set(tf.get_feature_names_out()))')],
 'char-ngrams':[('vocab_chars = len(chars.vocabulary_)','vocab_chars = len(chars.get_feature_names_out())')],
 'pipe':[('preds = [int(v) for v in model.predict(new)]','preds = model.predict(new).tolist()')],
 'p-nb':[('print(round(float((model.predict(X_test) == y_test).mean()), 3))','print(round(float((model.predict(X_test) == y_test).sum()/len(y_test)), 3))')],
 'baseline':[('share_bad = round(y.mean(), 3)','share_bad = round(y.sum()/len(y), 3)')],
 'top-words':[('top_bad = list(weights.sort_values(ascending=False).index[:5])','top_bad = sorted(weights.index, key=weights.get, reverse=True)[:5]')],
 'errors':[('confident = errors & (proba.max(axis=1) > 0.8)','confident = errors & ((proba[:,1] > .8) | (proba[:,1] < .2))')],
 'unsure':[('unsure = (p >= 0.2) & (p <= 0.8)','unsure = ~((p < .2) | (p > .8))')],
 'recall95':[('t = max(good)','t = sorted(good)[-1]')],
 'topics':[('cm = pd.crosstab(y_test, pred)','cm = pd.crosstab(y_test, pred).iloc[::-1,::-1]')],
 'compare':[('best = max(cv_f1, key=cv_f1.get)','best = pd.Series(cv_f1).idxmax()')],
 'p-vote':[('same = wide.nunique(axis=1) == 1','same = wide.nunique(axis=1).eq(1)')],
 'vote':[('n_no_majority = int(vote.isna().sum())','vote = vote.iloc[::-1]\nn_no_majority = int(vote.isna().sum())')],
 'kappa':[('p_o = sum(a == b for a, b in zip(x, y)) / n','p_o = 1-sum(a != b for a,b in zip(x,y))/n')],
 'golden':[('worst = min(gold_acc, key=gold_acc.get)','worst = pd.Series(gold_acc).idxmin()')],
 'topic-check':[('agree = wide["аня"] == wide["борис"]','agree = wide["аня"].eq(wide["борис"])')],
 'train-labels':[('rest = r.drop(wide.index)','rest = r.loc[~r.index.isin(wide.index)]')],
 'cos':[('return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))','return (a/np.linalg.norm(a)) @ (b/np.linalg.norm(b))')],
 'p-pool':[('import numpy as np\nvec','import numpy as np\nvec'),('v = np.mean([vec[w] for w in words], axis=0)','v = np.sum([vec[w] for w in words], axis=0)/len(words)')],
 'nearest':[('top3 = list(sims.index[:3])','top3 = list(sims.nlargest(3).index)')],
 'lsa':[('Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)','from sklearn.preprocessing import normalize\nZn = normalize(Z)')],
 'char-search':[('return list(r["text"].values[idx])','return r.iloc[idx]["text"].tolist()')],
 'lsa-clf':[('best_k = max(sorted(acc_by_k), key=acc_by_k.get)','best_k = min(acc_by_k, key=lambda k: (-acc_by_k[k], k))')],
 'skipgram':[('if j != i:','if abs(j-i)>0:')],
 'zero-shot':[('zs_pred = np.array(list(desc))[np.argmax(Zn @ Dn.T, axis=1)]','zs_pred = pd.Series(np.array(list(desc))[np.argmax(Zn @ Dn.T, axis=1)])')],
 'pad-mask':[('attention_mask = (input_ids != 0).astype(int)','attention_mask = np.not_equal(input_ids,0).astype(int)')],
 'wordpiece':[('if piece in ID:','if piece in set(VOCAB):')],
 'attention':[('W = np.exp(masked) / np.exp(masked).sum(axis=1, keepdims=True)','from scipy.special import softmax\nW = softmax(masked,axis=1)')],
 'masked-pool':[('return (H * mask[:, :, None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)','return np.stack([a[m.astype(bool)].mean(axis=0) for a,m in zip(H,mask)])')],
 'truncate':[('return ids if len(ids) <= max_len else ids[:max_len - 1] + [SEP]','return list(ids) if len(ids) <= max_len else [*ids[:max_len-1],3]')],
 'pad-waste':[('total += max(chunk) * len(chunk) - sum(chunk)','total += sum(max(chunk)-n for n in chunk)')],
 'parse-one':[('answer[answer.index("{"): answer.rindex("}") + 1]','"{" + answer.split("{",1)[1].rsplit("}",1)[0] + "}"')],
 'parse-llm':[('pd.DataFrame([parse(a) for a in raw])','pd.DataFrame.from_records(map(parse,raw),index=range(100,100+len(raw)))')],
 'llm-cost':[('total_in = sum((len(PROMPT) + len(t)) / 3 for t in new["text"])','total_in = (len(PROMPT)*len(new)+new["text"].str.len().sum())/3')],
 'llm-check':[('recall_by_topic = ok.groupby(true).mean().round(3)','recall_by_topic = (ok.groupby(true).sum()/true.value_counts()).round(3).iloc[::-1]')],
 'llm-same':[('lower = paired.mean() - 1.96 * paired.sem()','lower = paired.mean() - 1.96 * (paired.var(ddof=1)/len(paired))**.5')],
 'models':[('group_test_ids = r.iloc[group_test]["review_id"].tolist()','group_test_ids = list(reversed(r.iloc[group_test]["review_id"].tolist()))')],
 'rare':[('macro_f1 = round(float(f1_score(t_test, pred, average="macro")), 3)','macro_f1 = round(sum(float(v) for v in f1_score(t_test,pred,average=None,labels=labels))/len(labels),3)')],
 'score':[('n["p_neg"] = sent.predict_proba(n["text"])[:, 1]\nn["neg"] = (n["p_neg"] >= 0.5).astype(int)\nn["topic"] = topic_model.predict(n["text"])','predicted = pd.DataFrame({"review_id":n.review_id,"p_neg":sent.predict_proba(n.text)[:,1],"topic":topic_model.predict(n.text)}).sample(frac=1,random_state=7)\nn=n.merge(predicted,on="review_id",validate="one_to_one")\nn["neg"]=(n.p_neg>=.5).astype(int)')],
 'shops':[('by_shop = by_shop.round(3).sort_values("рост", ascending=False)','by_shop = by_shop.round(3).sort_values("рост", ascending=False,kind="stable")')],
 'weekly':[('weekly = n.pivot_table(index="week", columns="shop_id", values="neg", aggfunc="mean")','weekly = n.groupby(["week","shop_id"])["neg"].mean().unstack()')],
 'why':[('kzn = pd.crosstab(kb["topic"], kb["period"], normalize="columns")','kzn = kb.groupby(["topic","period"]).size().unstack(fill_value=0)\nkzn = kzn/kzn.sum(axis=0)')],
 'adjust':[('labeled = n.merge(gold[[\'review_id\',\'complaint\']],on=\'review_id\',validate=\'one_to_one\')','labeled = n.join(gold.sample(frac=1,random_state=4).set_index("review_id")[["complaint"]],on="review_id",validate="one_to_one")')],
}
bad={
 'tokenize':'def tokenize(text):\n    return re.findall(r"[а-я]+",text.lower())',
 'clean':'clean = normalize(raw)\ndef normalize(text):\n    return re.sub(r"[а-яё]*не[а-яё]*", "", re.sub(r"[^а-я ]", " ",text.lower().replace("ё","е"))).strip()',
 'vocab':'total = n_words',
 'p-stop':None,
 'neg-words':'ne_share_neg = round(sum("не" in tokenize(t) for t in r.loc[r.rating<=3,"text"])/int((r.rating<=3).sum()),3)',
 'bag':'bow = [[int(v>0) for v in row] for row in bow]',
 'hapax':'share_once_tokens = share_once_vocab',
 'bigrams':'top_bad = list(reversed(top_bad))',
 'rule':'acc_rule = acc_ne; f1_rule = f1_ne',
 'stem-pairs':'def stem(word,n):\n    return word[:5]',
 'stem':'def stem(word,n=5):\n    return word[:5]',
 'lemma-text':'def lemmatize(text):\n    return " ".join(tokenize(text))',
 'lemmas':'n_changed = sum(1 for w in tokens if to_lemma[w]!=w)',
 'lemma-top':'n_byt = len(forms_byt)',
 'lemma-fix':'n_barista = sum(fixes.get(w,w)=="бариста" for t in r.text for w in tokenize(t))',
 'count':'density = round(X.nnz/(X.shape[0]*X.shape[1])*100,4)',
 'p-tfidf':None,
 'idf':'idf.index = list(reversed(idf.index))',
 'idf-by-hand':'idf_manual = round(np.log(n/df_word)+1,4)',
 'ngrams':'sizes["1-2 min5"] = sizes["1-2"]',
 'min-df':'kept_share = round(len(cut.vocabulary_)/len(full.vocabulary_),4)',
 'keywords':'kw = {i:list(reversed(v)) for i,v in kw.items()}',
 'train-only':'tf = TfidfVectorizer().fit(r.text)\nX_train=tf.transform(text_train);X_test=tf.transform(text_test)',
 'char-ngrams':'sim_chars = sim_words',
 'pipe':'preds = [1-int(v) for v in preds]',
 'p-nb':None,
 'baseline':'f1_dummy = acc_dummy',
 'top-words':'weights = weights.sort_values().reset_index(drop=True).set_axis(weights.index)',
 'errors':'confident_share = round(n_confident/len(y_test),3)',
 'unsure':'unsure_examples=list(X_test.values[np.argsort(-np.abs(p-.5),kind="stable")[:3]])',
 'recall95':'thr=.5',
 'topics':'cm.index = list(reversed(cm.index))',
 'compare':'cv_f1["words"],cv_f1["chars"] = cv_f1["chars"],cv_f1["words"]',
 'p-vote':None,
 'vote':'vote = vote.reset_index(drop=True)',
 'kappa':'def kappa(x,y):\n    return sum(a==b for a,b in zip(x,y))/len(x)',
 'golden':'n_recheck = int((wide.loc[gold.index,rest[0]]!=wide.loc[gold.index,rest[1]]).sum())',
 'topic-check':'match_ab = round(float((wide["аня"]==topic).mean()),3)',
 'train-labels':'acc["аня"],acc["вика"] = acc["вика"],acc["аня"]',
 'cos':'def cosine(a,b):\n    return float(a@b)',
 'p-pool':None,
 'nearest':'sims.index = list(reversed(sims.index))',
 'lsa':'Zn = np.roll(Zn,1,axis=0)',
 'char-search':'def search(vec,T,q,k=5):\n    sim=(T@vec.transform(["курьер опоздал"]).T).toarray().ravel()\n    return list(r.text.values[np.argsort(-sim,kind="stable")[:k]])',
 'lsa-clf':'acc_by_k[10],acc_by_k[100]=acc_by_k[100],acc_by_k[10]',
 'skipgram':'_pairs_original=skipgram_pairs\ndef skipgram_pairs(tokens,window=2):\n    return [p for p in _pairs_original(tokens,window) if p[0]!=p[1]]',
 'zero-shot':'zs_pred=np.roll(zs_pred,1)',
 'pad-mask':None,
 'wordpiece':'_original_wp=wordpiece\ndef wordpiece(word):\n    p=_original_wp(word)\n    return p if p!=["[UNK]"] else [word[:3],"[UNK]"]',
 'attention':'W = W_raw; out=W@X',
 'masked-pool':'def mean_pool(H,mask):\n    return H.mean(axis=1)',
 'truncate':'def truncate(ids,max_len):\n    return ids[:max_len]',
 'pad-waste':'def pad_count(lens,size=8):\n    return sum(max(lens[i:i+size])*size-sum(lens[i:i+size]) for i in range(0,len(lens),size))',
 'parse-one':'topic = d["sentiment"]',
 'parse-llm':'parsed.iloc[[0,1]]=parsed.iloc[[1,0]].to_numpy()',
 'llm-cost':'cost = round(tokens_in*.3+tokens_out*1.5,1)',
 'llm-check':'acc_llm = round(float(ok[valid].mean()),3)',
 'llm-same':'paired_lower = round(float(paired.mean()-1.96*((ok_llm.var()+ok_model.var())/len(paired))**.5),3)',
 'models':'text_quality.loc["новые","macro_f1_topic"]=text_quality.loc["повторы","macro_f1_topic"]',
 'rare':'count_ratio = round(float((t_test==rarest).sum()/(pred==rarest).sum()),3)',
 'score':'n["p_neg"] = n.p_neg.to_numpy()[::-1]\nn["neg"]=(n.p_neg>=.5).astype(int)',
 'shops':'by_shop.index = list(reversed(by_shop.index))',
 'weekly':'weekly.index = weekly.index+pd.Timedelta(days=7)',
 'why':'quote_ids = quote_ids[::-1]',
 'adjust':'audit[["tpr","fpr"]] = tpr,fpr',
}
rows=[]
def emit(t,label,code,expected,description,origin='new targeted program',reachability='editor'):
 ast.parse(code)
 name=f'{t["lesson"].split("/")[-1]}--{t["id"]}--{label}.py';(d/'programs'/name).write_text(code)
 rows.append(dict(lesson=t['lesson'],task=t['id'],label=label,code=code,expected=expected,description=description,origin=origin,reachability=reachability,code_sha256=hashlib.sha256(code.encode()).hexdigest(),program_file='programs/'+name))
for t in tasks:
 s=t['solution']; id=t['id'];emit(t,'author',s,True,'Авторская программа текущего frozen export','current author')
 a=s
 for old,new in alt[id]:
  assert old in a,(id,old);a=a.replace(old,new,1)
 assert a!=s,id
 emit(t,'alternative',a,True,'Другой корректный расчёт: '+repr(alt[id]),reachability='Parsons reordered or harness-only alternate' if id.startswith('p-') or id=='pad-mask' else 'editor')
 if bad[id] is None:
  if id=='p-stop':b=s.replace('stop - keep','stop')
  elif id=='p-tfidf':b=s.replace('(T ** 2).sum(axis=1)','T.sum(axis=1)')
  elif id=='p-nb':b=s.replace('(model.predict(X_test) == y_test).mean()','(model.predict(X_test) != y_test).mean()')
  elif id=='p-vote':b=s.replace('== 1','== 2')
  elif id=='p-pool':b=s.replace('v = v / np.linalg.norm(v)','v = v')
  elif id=='pad-mask':b=s.replace('input_ids != 0','input_ids == 0')
 else:b=s+'\n'+bad[id]+'\n'
 emit(t,'plausible-wrong',b,False,'Правдоподобная ошибка расчёта / порядка / функции: '+str(bad[id]),reachability='harness-only; Parsons constants/operators are fixed in UI' if id.startswith('p-') or id=='pad-mask' else 'editor')
# Historical complete original programs, preserved literally.
hist=d/'historical';hist.mkdir(exist_ok=True)
for source in ['tools/checks/fixtures/reaudit_20261115.jsonl','docs/course-improvements/reaudit/fixes/technical-results.jsonl','docs/course-improvements/reaudit/expert_probes.py','tools/checks/ch13_acceptance.py','tools/checks/reaudit_technical.py']:
 f=root/source;shutil.copy2(f,hist/f.name)
 if f.suffix=='.jsonl':
  rs=[json.loads(l) for l in f.read_text().splitlines()];filtered=[r for r in rs if str(r.get('lesson',r.get('id',''))).startswith('ch13/')]
  (hist/(f.stem+'-ch13.json')).write_text(json.dumps(filtered,ensure_ascii=False,indent=2))
old=[json.loads(l) for l in (hist/'reaudit_20261115.jsonl').read_text().splitlines()]
for i,r in enumerate(old):
 if not r['lesson'].startswith('ch13/'):continue
 t=next(t for t in tasks if t['lesson']==r['lesson'] and t['id']==r['task']);emit(t,'historical35-'+str(i),r['code'],r['expected'],r['description'],'literal old35 fixture')
# Preserve acceptance driver expressions instantiated against CURRENT author, do not call old student code.
tmap={(t['lesson'].split('/')[-1],t['id']):t for t in tasks}
for i,(le,ta,suffix,expected) in enumerate([('05-project','score','n=n.sample(frac=1,random_state=3)',True),('05-project','score',"n.loc[n.shop_id=='KZN-2','shop_id']='TMN-1'",False),('05-project','weekly','weekly.index=weekly.index+pd.Timedelta(days=7)',False),('05-project','why','quotes[0]="Цитата из другого источника"',False),('05-project','adjust','',True),('03-classify','recall95','',True)]):
 t=tmap[le,ta];emit(t,'historical-driver-'+str(i),t['solution']+'\n'+suffix,expected,'Литерал выражения ch13_acceptance.py поверх текущего авторского решения','historical driver expression / current author')
(d/'tasks.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2))
(d/'programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(d/'freeze-manifest.json').write_text(json.dumps({'baseline':'563d774b125387aca7b004c086603e02900a18b1','files':{str(f.relative_to(d)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(d.rglob('*')) if f.is_file() and f.name!='freeze-manifest.json'}},indent=2))
print('PREPARED',len(rows),'programs',len(tasks),'tasks',hashlib.sha256((d/'programs.jsonl').read_bytes()).hexdigest())
