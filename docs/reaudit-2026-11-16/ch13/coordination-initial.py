"""Chapter 13 initial reconciliation; standard library only, no course execution.
Raw pairs, immutable student evidence, frozen source, whole graded payloads,
CSV arithmetic and independent adjudication ledger are separate denominators.
"""
import collections
import csv
import datetime
import hashlib
import json
import re
from pathlib import Path

D = Path(__file__).resolve().parent
W = Path('/private/tmp/kuch13round')
S = D / 'student'
def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def code_sha(s): return hashlib.sha256(s.encode()).hexdigest()
def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True)
def require(test, message):
    if not test: raise AssertionError(message)
def counts(events):
    return dict(events=len(events), graded=sum(type(e.get('passed')) is bool for e in events), passed=sum(e.get('passed') is True for e in events), failed=sum(e.get('passed') is False for e in events), transport_errors=sum('browserError' in e for e in events), hint_events=sum('hint' in e for e in events))
def table(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
def keyed(rr):
    result={r['review_id']:r for r in rr}
    require(len(result)==len(rr), 'unique review_id')
    return result

o={'scope':'ch13 initial only','status':'pending sanitized retake and final independent review','execution':'stdlib JSON/CSV/hash/arithmetic; no ML, NumPy, Node or Jupyter execution','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
b=read(D/'technical/baseline.json')
require(b['head']=='563d774b125387aca7b004c086603e02900a18b1','baseline HEAD')
require({s:sha(W/'original'/s) for s in b['source_sha256']}==b['source_sha256'],'frozen source SHA')
require(sha(W/'course.json')==b['full_export_sha256'],'frozen full export SHA')
for name,digest in b['data_sha256'].items():
    require(sha(D/'technical/data-baseline'/name)==digest,'raw data SHA '+name)
    require(sha(S/'data'/name)==digest,'student raw data SHA '+name)
o['reference']=b
o['standard_before']={'log_sha256':sha(D/'technical/baseline-standard.log'),'raw':(D/'technical/baseline-standard.log').read_text().strip(),'scope':'recorded standard 101 checks; coordinator did not rerun'}
full=read(W/'course.json'); chapter=read(D/'technical/baseline-export.json'); inv=read(D/'technical/inventory.json')
require([r for r in full if r['lesson'].startswith('ch13/')]==chapter,'frozen chapter export')
require({r['lesson'][5:]+'/'+r['id'] for r in chapter if r['kind']=='task'}=={k for k,v in inv.items() if v=='task'},'task IDs')
o['inventory']={'student_count':len(inv),'student_kinds':dict(collections.Counter(inv.values())),'technical_count':len(chapter),'technical_kinds':dict(collections.Counter(r['kind'] for r in chapter)),'technical_sha256':sha(D/'technical/baseline-export.json')}
alias={k:k.rsplit('/',1)[0]+'/predict/'+k.rsplit('/',1)[1][1:] for k,v in inv.items() if v=='predict'}
inv={alias.get(k,k):v for k,v in inv.items()}; o['inventory']['predict_aliases']=alias
manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (S/'SHA256SUMS').read_text().splitlines() if line.strip()}
require(all(sha(S/name)==digest for name,digest in manifest.items()),'immutable student SHA256SUMS')
actual_files={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}
o['student_freeze']={'manifest_entries':len(manifest),'all_hashes_match':True,'files_outside_manifest':sorted(actual_files-set(manifest)),'manifest_sha256':sha(S/'SHA256SUMS')}
actual=[]; pairs=[]; trace=[]; feedback_pairs=[]
for p in sorted(S.glob('*.feedback.jsonl')):
    q=p.with_name(p.name.replace('.feedback.','.input.')); aa,bb=rows(q),rows(p)
    require(len(aa)==len(bb),'pair lengths '+p.name)
    pairs.append({'input':q.name,'feedback':p.name,**counts(bb)})
    for line,(a,f) in enumerate(zip(aa,bb),1):
        ident=a.get('question') or a['lesson']+'/'+a.get('task','')
        require(ident==f['id'],'raw ID '+p.name+str(line))
        require(all(a.get(k) for k in ['Q1','Q2','Q3']),'pre-action Q1-Q3')
        actual.append({**a,**f}); feedback_pairs.append((a,f));trace.append({'input':q.name,'feedback':p.name,'line':line})
saved_raw=rows(S/'initial-attempts.jsonl')
require([r['at'] for r in saved_raw]==sorted(r['at'] for r in saved_raw),'aggregate chronological order')
saved=[{k:v for k,v in r.items() if k!='at'} for r in saved_raw]
raw_counter=collections.Counter(map(canonical,actual));saved_counter=collections.Counter(map(canonical,saved))
graded_counter=collections.Counter(canonical(e) for e in actual if type(e.get('passed')) is bool)
require(graded_counter==saved_counter,'FULL graded payload multiset including code, choices, prompts, images and multiplicity, excluding only at')
raw_only=[json.loads(s) for s,n in (raw_counter-saved_counter).items() for _ in range(n)]
require(not saved_counter-raw_counter,'no unexplained aggregate event')
# Walkthrough holds full feedback JSON and the complete Q1-Q3 strings per action.
walktext=(S/'walkthrough.md').read_text(); walk=[]
for section in re.split(r'(?m)^## ',walktext)[1:]:
    heading=section.splitlines()[0]
    if ' — ' not in heading: continue
    ident,filename=heading.split(' — ',1)
    feedback=json.loads(re.search(r'```json\n(.*?)\n```',section,re.S).group(1))
    questions={k:re.search(r'\*\*'+k+r'\.\*\* (.*?)(?=\n\n\*\*Q|\n\n\*\*Следующий)',section,re.S).group(1) for k in ['Q1','Q2','Q3']}
    require(ident==feedback['id'],'walkthrough ID')
    walk.append({'input_file':filename,'id':ident,**questions,'feedback':feedback})
expected_walk=[{'input_file':t['input'],'id':f['id'],**{k:a[k] for k in ['Q1','Q2','Q3']},'feedback':f} for (a,f),t in zip(feedback_pairs,trace)]
require(collections.Counter(map(canonical,walk))==collections.Counter(map(canonical,expected_walk)),'full Q1-Q4 walkthrough equality')
first={};last={};fg={};lg={}
# Primary lesson files preserve first raw events; saved chronological log preserves graded order.
lessons=['01-text-prep','01b-lemmas','02-tfidf','03-classify','03b-labels','04-embeddings','04b-transformers','04c-llm','05-project','test']
for lesson in lessons:
    for a,f in zip(rows(S/(lesson+'.input.jsonl')),rows(S/(lesson+'.feedback.jsonl'))): first.setdefault(f['id'],{**a,**f})
for e in saved:
    fg.setdefault(e['id'],e);lg[e['id']]=e
last.update(first);last.update(lg)
require(set(first)==set(fg)==set(inv),'95 student coverage sets incl quiz/predict')
o['student']={'pairs':pairs,**counts(actual),'aggregate':counts(saved),'full_payload_multiset_equal':raw_counter==saved_counter,'full_graded_payload_multiset_equal':True,'raw_only_events':raw_only,'saved_only_events':[],'aggregate_scope':'bridge logs boolean passed events only; hint and transport remain in raw pairs and walkthrough','bridge_sha256':sha(W/'bridge.cjs'),'walkthrough_full_Q1_Q4_equal':True,'walkthrough_events':len(walk),'first_event':counts(list(first.values())),'first_graded':counts(list(fg.values())),'latest_event':counts(list(last.values())),'latest_graded':counts(list(lg.values())),'by_kind':{kind:{'IDs':sum(v==kind for v in inv.values()),'first_event_pass':sum(e.get('passed') is True and inv[k]==kind for k,e in first.items()),'first_graded_pass':sum(e.get('passed') is True and inv[k]==kind for k,e in fg.items()),'latest_graded_pass':sum(e.get('passed') is True and inv[k]==kind for k,e in lg.items())} for kind in sorted(set(inv.values()))},'non_true_events':[{'payload':e,'trace':t} for e,t in zip(actual,trace) if e.get('passed') is not True],'graded_time_range':[saved_raw[0]['at'],saved_raw[-1]['at']],'order_caveat':'First raw actions from primary lesson files; graded first/latest ordered by aggregate timestamps. Ungraded hint has no timestamp and is excluded from latest outcome. Latest event here means latest non-hint submission.','graded_attempts_by_ID':dict(collections.Counter(e['id'] for e in saved))}
# Validate complete frozen programs against both results; no code execution.
C=D/'technical/checks';check_series={}
for suffix,pf in [('', 'programs.jsonl'),('extra-','extra-programs.jsonl')]:
    pp=rows(C/pf); vv=[];stats={}
    for runtime in ['native','pyodide']:
        rr=rows(C/(suffix+'before-'+runtime+'.jsonl'))
        require(len(rr)==len(pp),'check result count')
        for p,r in zip(pp,rr):
            require(all(r[k]==v for k,v in p.items()),'full frozen program metadata matches runtime')
            require(code_sha(p['code'])==p['code_sha256'],'check literal program SHA')
            if 'program_file' in p: require(sha(C/p['program_file'])==p['code_sha256'],'check on-disk program SHA')
        vv.append([r['passed'] for r in rr])
        mm=[{'index':i,'lesson':r['lesson'],'task':r['task'],'label':r['label'],'expected':r['expected'],'passed':r['passed']} for i,r in enumerate(rr) if type(r.get('passed')) is bool and r['passed']!=r['expected']]
        stats[runtime]={'count':len(rr),'normative_matches':len(rr)-len(mm),'normative_mismatches':mm,'author_pass':sum(r['label']=='author' and r['passed'] is True for r in rr),'alternative_pass':sum(r['label']=='alternative' and r['passed'] is True for r in rr),'stages':dict(collections.Counter(r['stage'] for r in rr)),'result_sha256':sha(C/(suffix+'before-'+runtime+'.jsonl'))}
    require(vv[0]==vv[1],'check runtime verdict parity')
    check_series[pf]={'program_sha256':sha(C/pf),'labels':dict(collections.Counter(p['label'] for p in pp)),'runtime_verdict_parity':True,'runtimes':stats}
require(sha(C/'programs.jsonl')==read(C/'freeze-manifest.json')['files']['programs.jsonl'],'235 final frozen manifest')
require(sha(C/'extra-programs.jsonl')==read(C/'extra-freeze.json')['program_sha256'],'18 frozen manifest')
o['checks_before']=check_series
R=D/'fixes/reviewer-evidence'
for manifest_name in ['SHA256SUMS-before','SHA256SUMS-results-before']:
    for line in (R/manifest_name).read_text().splitlines():
        digest,name=line.split('  ',1);require(sha(R/name)==digest,'reviewer frozen '+name)
cases=read(R/'cases-before.json');verdicts=[];rev={}
for runtime in ['native','pyodide']:
    rr=rows(R/('before-'+runtime+'.jsonl'));require([r['id'] for r in rr]==[p['id'] for p in cases],'reviewer ID/order')
    require(all(r['expected']==p['expected'] for r,p in zip(rr,cases)),'reviewer expectations')
    verdicts.append([r['check']['passed'] for r in rr])
    rev[runtime]={'count':len(rr),'correct_accepted':sum(r['expected'] and r['check']['passed'] for r in rr),'wrong_rejected':sum(not r['expected'] and not r['check']['passed'] for r in rr),'false_accepts':[r['id'] for r in rr if not r['expected'] and r['check']['passed']],'execution_failures':[r['id'] for r in rr if not r['ok']],'sha256':sha(R/('before-'+runtime+'.jsonl'))}
require(verdicts[0]==verdicts[1],'reviewer parity');o['reviewer_before']={'runtimes':rev,'runtime_verdict_parity':True,'cases_sha256':sha(R/'cases-before.json')}
# Independently join all six baseline CSVs and student predictions by review_id.
data={p.stem:table(p) for p in (D/'technical/data-baseline').glob('*.csv')}
new=keyed(data['reviews_new']);gold=keyed(data['reviews_new_gold']);old=keyed(data['reviews_text']);scores=keyed(table(S/'own-scored.csv'))
require(set(new)==set(gold)==set(scores),'4800 source/gold/scored sets')
for ident,r in new.items():
    s=scores[ident];require(all(s[k]==r[k] for k in ['review_id','date','shop_id','text']),'all raw fields by ID')
    require(int(s['neg'])==int(float(s['p_neg'])>=.5),'probability threshold')
    date=datetime.date.fromisoformat(r['date']);week=(date-datetime.timedelta(days=date.weekday())).isoformat()
    require(s['week']==week and s['period']==('до' if r['date']<'2026-10-05' else 'после'),'scored week and period')
shops=sorted({r['shop_id'] for r in new.values()});monthly={};weekly=collections.defaultdict(dict)
def summary(rr):
    return {'n':len(rr),'signals':sum(int(s['neg']) for s in rr),'complaints':sum(int(gold[s['review_id']]['complaint']) for s in rr)}
for shop in shops:
    sep=summary([s for s in scores.values() if s['shop_id']==shop and s['date']<'2026-10-01']);oct=summary([s for s in scores.values() if s['shop_id']==shop and s['date']>='2026-10-01'])
    monthly[shop]={'до':sep,'после':oct,'рост':oct['signals']/oct['n']-sep['signals']/sep['n']}
for week in sorted({r['week'] for r in scores.values()}):
    for shop in shops:weekly[week][shop]=summary([s for s in scores.values() if s['shop_id']==shop and s['week']==week])
focus=max(monthly,key=lambda shop:monthly[shop]['рост']);weeks=sorted(weekly)
jump=max(weeks[1:],key=lambda w:weekly[w][focus]['signals']/weekly[w][focus]['n']-weekly[weeks[weeks.index(w)-1]][focus]['signals']/weekly[weeks[weeks.index(w)-1]][focus]['n'])
require(focus=='KZN-2' and jump=='2026-10-05','independent focus/week')
for r in table(S/'own-monthly.csv'):
    m=monthly[r['shop_id']]
    for k in ['до','после']:require(abs(float(r[k])-m[k]['signals']/m[k]['n'])<1e-12,'monthly CSV')
    require(abs(float(r['рост'])-m['рост'])<1e-12,'monthly growth')
for r in table(S/'own-weekly.csv'):
    for shop in shops:require(abs(float(r[shop])-weekly[r['week']][shop]['signals']/weekly[r['week']][shop]['n'])<1e-12,'weekly CSV')
periods={};topic_counts={};comparison={}
for period in ['до','после']:
    rr=[s for s in scores.values() if s['shop_id']==focus and ('до' if s['date']<jump else 'после')==period];p=summary(rr)
    tp=sum(int(s['neg']) and int(gold[s['review_id']]['complaint']) for s in rr);fp=p['signals']-tp
    p.update(tp=tp,fp=fp,tpr=tp/p['complaints'],fpr=fp/(p['n']-p['complaints']),observed=p['signals']/p['n'],manual=p['complaints']/p['n'])
    p['adjusted']=(p['observed']-p['fpr'])/(p['tpr']-p['fpr']);periods[period]=p
    topic_counts[period]=dict(collections.Counter(s['topic'] for s in rr if int(s['neg'])))
    other=[s for s in scores.values() if s['shop_id']!=focus and ('до' if s['date']<jump else 'после')==period and int(s['neg'])]
    comparison[period]={'signals':len(other),'delivery':sum(s['topic']=='доставка' for s in other)}
for r in table(S/'own-audit.csv'):
    for k,v in periods[r['period']].items():
        if k in r:require(abs(float(r[k])-v)<1e-12,'audit '+k)
growth_topic=max(set(topic_counts['до'])|set(topic_counts['после']),key=lambda t:topic_counts['после'].get(t,0)/periods['после']['signals']-topic_counts['до'].get(t,0)/periods['до']['signals'])
quotes=table(S/'own-quotes.csv');letter=(S/'own-letter.md').read_text()
expected_quotes=sorted([s for s in scores.values() if s['shop_id']==focus and s['date']>=jump and int(s['neg']) and s['topic']==growth_topic],key=lambda s:float(s['p_neg']),reverse=True)[:5]
require(quotes==expected_quotes,'five full top quote payloads')
require(all(q['review_id']+': '+new[q['review_id']]['text'] in letter for q in quotes),'letter quotes by raw ID/text')
# Original rating test rates are recorded evidence, not independently reconstructed model predictions.
old_rates={'tpr':0.9169675090252708,'fpr':0.034055727554179564}
o['own_csv_recalculation']={'source_rows':{k:len(v) for k,v in data.items()},'all_4800_fields_periods_weeks_verified':True,'focus':focus,'jump_week':jump,'october_level_leader':max(monthly,key=lambda k:monthly[k]['после']['signals']/monthly[k]['после']['n']),'monthly':monthly,'weekly':weekly,'periods':periods,'growth_topic':growth_topic,'topic_signals':topic_counts,'other_shops_delivery':comparison,'quotes':quotes,'letter_has_numeric_volumes':{'440':'440' in letter,'372':'372' in letter},'old_rating_rates_recorded_only':old_rates,'old_rating_adjustments':{k:(p['observed']-old_rates['fpr'])/(old_rates['tpr']-old_rates['fpr']) for k,p in periods.items()},'limitation':'Arithmetic on submitted predictions, no retraining or independent old-test predictions. Gold complaint/topic are synthetic. Letter has rates and source caveats but lacks 440/372 volumes.'}
# Independent text/vocabulary and annotator arithmetic on the remaining four CSVs.
words=collections.Counter(w for r in old.values() for w in re.findall('[а-яё]+',r['text'].lower()))
require({r['word']:int(r['count']) for r in data['review_lemmas']}==dict(words),'all lemma corpus counts')
labels=collections.defaultdict(dict)
for r in data['review_labels']:labels[r['review_id']][r['annotator']]=r['label']
gold_old=keyed(data['review_gold']);names=sorted({r['annotator'] for r in data['review_labels']})
annotators={name:sum(labels[i][name]==r['label'] for i,r in gold_old.items()) for name in names}
pair_stats={}
for j,a in enumerate(names):
    for name in names[j+1:]:
        both=[v for v in labels.values() if a in v and name in v]
        agreement=sum(v[a]==v[name] for v in both)/len(both)
        ca=collections.Counter(v[a] for v in both);cb=collections.Counter(v[name] for v in both)
        chance=sum(ca[k]*cb[k] for k in set(ca)|set(cb))/len(both)**2
        pair_stats[a+'/'+name]={'n':len(both),'agreement':agreement,'kappa':(agreement-chance)/(1-chance)}
agreed=[i for i,v in labels.items() if v['аня']==v['борис']]
wrong_agreed=[i for i in agreed if labels[i]['аня']!=old[i]['topic']]
o['raw_data_arithmetic']={'annotator_pairs':pair_stats,'Anya_Boris_agreed':len(agreed),'Anya_Boris_agreed_wrong_IDs':sorted(wrong_agreed),'tokens':sum(words.values()),'vocabulary':len(words),'lemma_rows':len(data['review_lemmas']),'old_unique_texts':len({r['text'] for r in old.values()}),'new_unique_texts':len({r['text'] for r in new.values()}),'label_review_IDs':len(labels),'annotators':names,'gold_correct_of_50':annotators,'gold_copies_original_topic':all(r['label']==old[i]['topic'] for i,r in gold_old.items()),'new_gold_sources':dict(collections.Counter(r['label_source'] for r in gold.values()))}
# Every adjudicated source ID is kept, including two separate October aspects.
review=(D/'fixes/review-before.md').read_text();ledger=[]
for line in review.splitlines():
    if not line.startswith('| '):continue
    cells=[s.strip() for s in line.strip('|').split('|')]
    ident=cells[0]
    if re.fullmatch(r'(?:[SME]13-\d+|T1[01]|CH13-ST\d+|EX13-\d+|N13-M\d+|B13-\d+|T13-\d+|CH13-CHECK\d+|Октябрь, .+)',ident):
        ledger.append({'id':ident,'before_verdict':cells[1],'reviewer_evidence_criterion':' | '.join(cells[2:]),'after_status':'pending final independent review; external human evidence for M13-01'})
ledger.append({'id':'REV13-01','before_verdict':'Дополнительное замечание, P2','reviewer_evidence_criterion':re.search(r'\*\*Дополнительное замечание REV13-01.*?(?=\n\n##)',review,re.S).group(0),'after_status':'pending final independent review'})
require(len({r['id'] for r in ledger})==len(ledger),'unique source finding IDs')
def group(i):
    for prefix,g in [('CH13-ST','student'),('EX13-','expert'),('N13-M','methodist'),('B13-','business'),('T13-','test'),('CH13-CHECK','checks'),('REV13-','reviewer')]:
        if i.startswith(prefix):return g
    return 'historical including October aspects'
o['finding_ledger']={'count':len(ledger),'groups':dict(collections.Counter(group(r['id']) for r in ledger)),'rows':ledger,'meaning':'source IDs, not unique defects; overlapping observations intentionally retained'}
o['notebooks']={'own':{'code_cells':sum(c['cell_type']=='code' for c in read(S/'project-template.ipynb')['cells']),'code_cells_with_outputs':sum(c['cell_type']=='code' and bool(c.get('outputs')) for c in read(S/'project-template.ipynb')['cells']),'execution':'Student independent CLI process, clean namespace, real saved PNG/stdout. nbclient loopback bind denied; not Jupyter PASS. Coordinator inspected artifacts, did not rerun.'},'extra':{name:{'code_cells':sum(c['cell_type']=='code' for c in read(S/name)['cells']),'code_cells_with_outputs':sum(c['cell_type']=='code' and bool(c.get('outputs')) for c in read(S/name)['cells'])} for name in ['ch13-pymorphy3.ipynb','ch13-transformers.ipynb']},'reported_runtime_facts':{'pymorphy_words_lemmas':[491,450],'embedding_shape':[2400,312],'masked_batch_max_difference':5.96e-8,'binary_sentiment_F1':{'embedding':[.930,.016],'TFIDF':[.940,.015]},'F1_scope':'binary sentiment, not six-topic macro-F1'},'execution_evidence_sha256':{name:sha(S/name) for name in ['own-native.log','own-execution.log','extra-pymorphy.log','extra-transformers.log','extra-verification.log','own-static-check-final.log','execution-provenance.md']},'static_checker':'--no-run 0 errors / 0 warnings is formatting evidence only, not business acceptance'}
o['interpretation']={'quality_before_scores':[4,4,4,3,3],'quality_before_mean':3.6,'quality_after':None,'roles':['Sol medium coordinator','Sol medium student','Sol medium quiz critic','Sol high check critic','Astra high expert','Astra high methodist','Astra high business critic','Astra high independent reviewer'],'recall95':'three graded attempts: two missing required fields test_recall and test_flagged; test_precision added by student, never required','llm_same':'student index exclusion error repaired using review_id, useful feedback; not course defect','external_M13_01':'real independently human-labelled reviews for both periods with common rubric, sampling and uncertainty; owner real-flow stakeholder. Synthetic generator and LLM do not close it','pending':['actual-source checks after guards in both runtimes, explicit contract migrations','sanitized student retake without critic answers','new self-contained business letter and support transfer','final independent reviewer reconciliation','methodist after-score only if independently supplied']}
o['report_reference_sha256']={name:sha(D/name) for name in ['previous.md','expert.md','methodist.md','business.md','test-review.md','checks.md','fixes/review-before.md']}
(D/'coordination-initial.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:o[k] for k in ['inventory','student_freeze','raw_data_arithmetic']},ensure_ascii=False,indent=2))
print('Student',counts(actual),'aggregate',counts(saved),'first',o['student']['first_event'],'first graded',o['student']['first_graded'],'latest',o['student']['latest_graded'])
print('Findings',o['finding_ledger']['count'],o['finding_ledger']['groups'])

lines=['# Первичная координационная сверка главы 13', '', '## Качество подачи учебного материала', '', 'Для SQL/Excel-аналитика независимая оценка исходной подачи — **3,6/5**: ясность 4, SQL/Excel 4, последовательность 4, условия и обратная связь 3, самостоятельность 3; веса равные. Это before, оценка после редакции ещё не выставлена. Основания и подробные редакторские примеры — [методист](methodist.md).', '', '## Границы и воспроизводимость', '', 'Разрешена только глава 13. Исходный SHA `'+b['head']+'`. Сверены замороженные `original`, полный экспорт и шесть CSV; текущие параллельно изменяемые исходники не использованы как baseline. Скрипт выполняет только стандартную библиотеку: `python3 docs/reaudit-2026-11-16/ch13/coordination-initial.py`. Полные результаты, SHA, payload и реестр — [coordination-initial.json](coordination-initial.json). Учебные исходники, сайт, Git и 73 замороженных файла ученика этой ролью не изменялись.', '', '## Прохождение и полнота журналов', '', '| Ведомость | Результат |', '|---|---|', '| Ученические ID | 95: 65 задач, 5 predict, 11 встроенных, 14 итоговых вопросов |', '| Технический экспорт | 101: 65 задач, 5 predict, 31 исполняемый пример; квизы сюда не входят |', '| Все сырые действия | 100: 98 оценённых, 1 browserError, 1 UI hint |', '| Оценённые попытки | 95 true, 3 false; агрегат bridge 98 записей |', '| Первое сырое действие на ID | 92 true, 2 false, 1 transport без оценки |', '| Первая оценённая попытка на ID | 93/95 |', '| Последняя оценённая попытка на ID | 95/95 |', '| Замороженные файлы ученика | Все 73 SHA совпали; вне manifest только сам SHA256SUMS |', '', 'Полный multiset объединённых input/feedback совпал с aggregate для всех оценённых событий, включая код, выбор, видимые prompt, изображения, выход и кратность; исключено только поле `at`. Два неоценённых события не попадают в aggregate по контракту bridge, но полностью сохранены в raw и walkthrough. Полные Q1–Q3 и Q4 walkthrough сверены по каждому действию. Имена predict `q1` сопоставлены с `predict/1`. Последний исход считается по сдачам без события подсказки; порядок hint без timestamp не выдумывается.', '', '`recall95`: три оценённых попытки, сначала отсутствовал test_recall, затем test_flagged; test_precision ученик добавил сам, проверка его не требовала. Единственная UI-подсказка смешивала p_validation с y_test. `llm-same`: две оценённые попытки; drop по index заменён на исключение по review_id. Это собственная ошибка ученика, исправленная конкретной обратной связью. Parsons p-nb сначала дал транспортный browserError; первая оценённая сдача из доступных строк принята. С первой оценённой попытки без hint приняты 93 ID, один ID впоследствии восстановлен самостоятельно, один — с hint; открытых ID нет. Процент принятия не является оценкой качества подачи или успеха людей.', '', '## Независимый пересчёт результата', '', 'По всем 4800 исходным ID сверены date/shop/text, p_neg ≥ 0,5, периоды и понедельники. Заново пересчитаны все 6 месячных строк, 54 пары точка–неделя, audit и полные пять цитат. Выбор по максимальному месячному приросту даёт KZN-2, по соседним неделям — 5 октября. Максимальный октябрьский уровень отдельно у TMN-1.', '', '| KZN-2 | До 5 октября | С 5 октября |', '|---|---:|---:|', '| Все отзывы | 440 | 372 |', '| Сигналы модели | 162 (36,818 %) | 222 (59,677 %) |', '| Жалобы генератора | 161 (36,591 %) | 222 (59,677 %) |', '| TP / FP | 161 / 1 | 222 / 0 |', '| Доставка среди сигналов | 39/162 (24,074 %) | 129/222 (58,108 %) |', '', 'Календарная граница 1 октября даёт другие знаменатели: 383/429 и 142/242 сигнала. В предыдущей и следующей неделях скачка 33/95 и 53/89. У остальных точек доставка среди сигналов 167/925 → 133/814. Студенческие own-monthly, own-weekly и own-audit совпали с независимой арифметикой. Пять верхних цитат именно **растущей темы доставки**, а не всего негатива, совпали по полному payload и исходным ID. N-54090, N-53971, N-53673, N-54519, N-54719 сохранены в письме без подмены текста. Три содержат и другие проблемы.', '', 'В исходном письме верные доли 36,8/59,7 % и ограничения источника, но **нет объёмов 440/372**. Достаточность нового письма проверяется после редакции отдельно, без таблиц. Старые TPR/FPR взяты из сохранённого исполнения, не пересчитаны из отсутствующих здесь тестовых прогнозов: условные поправки 0,378/0,637 подтверждены арифметически. Новые TPR/FPR дают доли генератора на тех же строках по тождеству; это не независимая валидация.', '', 'Дополнительно по сырым CSV подтверждены 19 257 токенов, 491 слово и все частоты лемм; 2400/4800 уникальных ID и 2151/4027 разных текстов; 450×3 голоса; gold-копии исходной темы и 46/39/27 совпадений из 50. У Ани и Бориса 362 согласия, из них три расходятся с исходной темой (R-41127, R-41526, R-42152). Все 4800 новых gold имеют label_source=synthetic_kind_neg_or_mixed.', '', '## Исполнение и отдельные технические знаменатели', '', 'Свои пять code-ячеек проекта ученик реально исполнил CLI-процессом с чистым namespace; stdout и PNG сохранены. Отказ nbclient loopback bind — средовой, Jupyter PASS не заявлен. Оба extra реально исполнены offline: pymorphy3 491→450, RuBERT 2400×312 и masked batch difference 5,96e−8. F1 0,930±0,016 против TF-IDF 0,940±0,015 относится к **бинарной тональности**, не к macro-F1 шести тем. Координатор проверил сохранённые артефакты, повторного ML-исполнения не делал. `--no-run` 0/0 означает статическую проверку оформления, бизнес-приёмку не подтверждает.', '', 'Штатный before-лог содержит 101/101. Отдельно сверены полные frozen-программы и их SHA с обоими raw runtime-результатами: 235 + 18 в CPython и столько же в Pyodide, без различий вердиктов. У каждой среды 65/65 author и 65/65 alternative, 19 первоначальных и 7 дополнительных несовпадений с frozen expected. №44/№228 на исходных данных неразличимы; №98 относится к опубликованной точности. Это не 26 самостоятельных дефектов. Первичный manifest на 233 сохранён как история, действующий final-manifest на 235 проверен. Собственный reviewer: 25 проб в каждой среде, все 10 правильных приняты, 8/15 неправильных отклонены, семь FA (R07/R09/R11/R13/R15/R22/R23). Это три серии, их не складывают со студентом.', '', 'SDK-повтор эксперта на фактическом исходнике 32/32 offline и предметная редактура уже имеют отдельные артефакты. Они не закрывают все guards, новую сдачу и финальную рецензию. Актуальные проверки после параллельных правок относятся к следующему срезу.', '', '## Поимённая сверка и остаток', '', 'Из полных замечаний и независимой рецензии восстановлены **'+str(len(ledger))+' исходных ID**: 16 исторических нумерованных и 2 отдельных октябрьских аспекта, студент 6, эксперт 6, методист 7, деловой критик 5, тест 4, автопроверки 16, REV13-01. Это реестр сообщений с пересечениями, не число независимых дефектов. Полные основания и критерии каждой строки включены в JSON; решения — [review-before](fixes/review-before.md).', '', '| ID | Решение до редакции | После |', '|---|---|---|']
for row in ledger:lines.append('| '+row['id']+' | '+row['before_verdict']+' | '+('Внешняя human-проверка открыта' if row['id']=='M13-01' else 'Pending финальная рецензия')+' |')
lines += ['', '**M13-01 остаётся внешним для реального потока.** Владелец рабочего процесса должен предоставить независимо размеченные людьми отзывы двух периодов по одной инструкции, схему отбора, числители/знаменатели и неопределённость. Генератор или дополнительный LLM-запуск этих свидетельств не создаёт.', '', 'До завершения нужны actual-source guards в обеих средах с явными миграциями изменившихся контрактов; адресная сдача ученика из sanitized-пакета; новое самостоятельное письмо и перенос в поддержку; итоговая независимая рецензия и, при наличии, отдельная оценка подачи после правок. Восемь ролей текущего среза: Sol medium координатор/ученик/критик теста; Sol high критик автопроверок; Astra high эксперт/методист/деловой критик/рецензент. Глава пока не объявляется принятой.']
(D/'coordination-initial.md').write_text('\n'.join(lines)+'\n')
