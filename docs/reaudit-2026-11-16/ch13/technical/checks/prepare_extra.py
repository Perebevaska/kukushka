from pathlib import Path
import json,hashlib,ast
p=Path('/private/tmp/kuch13round/checks');ts=json.loads((p/'tasks.json').read_text());tm={t['id']:t for t in ts};rows=[]
def emit(id,label,code,expected,desc):
 ast.parse(code);t=tm[id];rows.append(dict(lesson=t['lesson'],task=id,label=label,code=code,expected=expected,description=desc,code_sha256=hashlib.sha256(code.encode()).hexdigest(),origin='additive diagnostic after235 before-results, frozen before own execution'))
# Separate diagnostics observe why three old expectations failed; never revise old235.
for id,expr in [('lemma-fix','dict(author=n_barista, word_instead_lemma=sum(fixes.get(w,w)=="бариста" for t in r.text for w in tokenize(t)))'),('compare','dict(scores=cv_f1,words_chars_equal=cv_f1["words"]==cv_f1["chars"])'),('adjust','dict(source_ids_equal=n.review_id.reset_index(drop=True).equals(gold.review_id.reset_index(drop=True)))')]:
 emit(id,'diagnose-nondiscriminating',tm[id]['solution']+'\nprint('+expr+')',True,'Проверить фактическую различимость предыдущей пары, результат True не является пробой защиты')
# Independent original-source n, then shuffle gold only in memory, preserving immutable CSV.
s=tm['adjust']['solution'];s=s.replace("gold = pd.read_csv('reviews_new_gold.csv')","gold = pd.read_csv('reviews_new_gold.csv').sample(frac=1,random_state=29).reset_index(drop=True)")
emit('adjust','gold-shuffled-keyed',s,True,'Те же gold строки в другом порядке: ключевой merge сохраняет ответы')
emit('adjust','gold-shuffled-positional',s.replace("labeled = n.merge(gold[['review_id','complaint']],on='review_id',validate='one_to_one')","labeled=n.copy()\nlabeled['complaint']=gold.complaint.to_numpy()"),False,'Переставлена только gold таблица: позиционное присвоение разрушает пары')
emit('adjust','extra-period-row',tm['adjust']['solution']+'\naudit.loc["неизвестный"] = audit.iloc[0]',False,'Третья строка не соответствует двум периодам public таблицы')
emit('adjust','partial-source-rows','n=n.iloc[::2].copy()\n'+tm['adjust']['solution'],False,'n случайно отфильтрована до расчёта audit: исходные знаменатели должны сохраняться')
# New callable inputs show functional distinction without changing data.
for id,diag in [('tokenize','print("new_tokens",tokenize("Ёж, ёлка и ABC не-кофе 3!"))'),('stem','print("new_stem_n3",stem("капучино",3))'),('skipgram','print("repeated_positions",skipgram_pairs(["кофе","кофе"],1))'),('char-search','print("new_query",search(w_vec,W,"цены адекватные",3))')]:
 s=tm[id]['solution'];emit(id,'new-input-oracle',s+'\n'+diag,True,'Новый вход; ожидаемый смысл следует из публичного определения функции')
 b=next(r for r in map(json.loads,(p/'programs.jsonl').read_text().splitlines()) if r['task']==id and r['label']=='plausible-wrong')['code'];emit(id,'new-input-wrong-evidence',b+'\n'+diag,False,'Сохранённый ошибочный код на новом входе; вывод фиксирует функциональное различие')
# Pair benchmark 200 rows may be permuted as whole aligned pairs, keeping row keys.
s=tm['llm-same']['solution']
prefix='order=check.sample(frac=1,random_state=17).index\ncheck=check.loc[order].reset_index(drop=True)\nok_llm=ok_llm.loc[order].reset_index(drop=True)\n'
emit('llm-same','whole-pairs-permuted',prefix+s,True,'Одни и те же200 review_id: переставлены строки вместе с их LLM correctness')
prefix_bad='ok_llm=ok_llm.sample(frac=1,random_state=17).reset_index(drop=True)\n'
emit('llm-same','only-labels-permuted',prefix_bad+s,False,'Меняется только принадлежность LLM correctness, benchmark должен сверять исходные ответы по review_id')
# Explicit non-default index with unaltered physical order, all comparisons by physical row order.
prefix='check=check.copy();check.index=range(1000,1200)\nok_llm=ok_llm.copy();ok_llm.index=check.index\n'
s=s.replace('pd.Series(model.predict(check["text"])) == check["topic"]','pd.Series(model.predict(check["text"]),index=check.index) == check["topic"]')
emit('llm-same','nondefault-same-order-index',prefix+s,True,'Смена только pandas index; порядок отзывов и соответствие сохранены')
(p/'extra-programs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
for r in rows:
 filename=r['task']+'--'+r['label']+'.py';f=p/'extra-programs'/filename;f.parent.mkdir(exist_ok=True);f.write_text(r['code'])
(p/'extra-freeze.json').write_text(json.dumps({'n':len(rows),'program_sha256':hashlib.sha256((p/'extra-programs.jsonl').read_bytes()).hexdigest(),'baseline_tasks_sha256':hashlib.sha256((p/'tasks.json').read_bytes()).hexdigest()},indent=2));print(len(rows),(p/'extra-freeze.json').read_text())
# New drivers are copies of the frozen235 drivers with only input programs changed.
for src,dst in [('run_native.py','run_native_extra.py'),('run_pyodide.mjs','run_pyodide_extra.mjs')]:
 (p/dst).write_text((p/src).read_text().replace('programs.jsonl','extra-programs.jsonl'))
