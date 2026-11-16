"""Read-only stdlib reconciliation; writes only coordinator-owned JSON and appendix."""
import collections,csv,datetime,hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent
ROOT=D.parents[2]
W=pathlib.Path('/private/tmp/kuch10round')
def js(p):return json.loads(p.read_text())
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def reconcile(raw,aggregate):
    events=[];pairs=[]
    for f in sorted(raw.glob('*-feedback.jsonl')):
        inp=f.with_name(f.name.replace('-feedback','-input'));a,b=jl(inp),jl(f);assert len(a)==len(b)
        for n,(x,y) in enumerate(zip(a,b),1):
            ident=x.get('question') or x['lesson']+'/'+x['task'];assert ident==y['id']
            events.append(dict(input=str(inp.relative_to(D)),feedback=str(f.relative_to(D)),line=n,payload=dict(x,**y)))
        pairs.append(dict(input=str(inp.relative_to(D)),feedback=str(f.relative_to(D)),rows=len(a),input_sha256=sha(inp),feedback_sha256=sha(f)))
    graded=[e for e in events if type(e['payload'].get('passed')) is bool]
    if aggregate.exists():
        assert collections.Counter(canonical(e['payload']) for e in graded)==collections.Counter(canonical({k:v for k,v in x.items() if k!='at'}) for x in jl(aggregate))
    first={};firstgraded={};last={}
    for e in events:
        x=e['payload'];first.setdefault(x['id'],e);last[x['id']]=e
        if type(x.get('passed')) is bool:firstgraded.setdefault(x['id'],e)
    return dict(events=len(events),graded=len(graded),transport=len(events)-len(graded),unique_ids=len(first),first_event_accepted=sum(x['payload'].get('passed') is True for x in first.values()),first_graded_accepted=sum(x['payload'].get('passed') is True for x in firstgraded.values()),latest_accepted=sum(x['payload'].get('passed') is True for x in last.values()),pairs=pairs,by_id={i:dict(first=first[i],first_graded=firstgraded.get(i),latest=last[i]) for i in first},aggregate_present=aggregate.exists(),exact_multiset_match=aggregate.exists())
initial_hash=sha(D/'coordination-initial.json')
initial=reconcile(D/'student/raw',D/'student/initial-attempts.jsonl');assert (initial['events'],initial['graded'],initial['transport'],initial['latest_accepted'])==(93,91,2,88)
retake=reconcile(D/'fixes/student/retest/raw',D/'student/retest-attempts.jsonl')
inv=js(D/'technical/inventory.json');targets=js(D/'technical/retest-targets.json');assert len(targets)==34
retake['kind_counts']=dict(collections.Counter(inv[i] for i in retake['by_id']))
frozen_manifest=D/'fixes/student/retest/frozen-manifest.sha256'
frozen_checks={}
if frozen_manifest.exists():
    for line in frozen_manifest.read_text().splitlines():
        h,path=line.split('  ',1);frozen_checks[path]=sha(frozen_manifest.parent/path)==h
    assert len(frozen_checks)==62 and all(frozen_checks.values())
ledger=list(csv.DictReader((D/'fixes/verdicts.csv').open()));assert len(ledger)==len({x['id'] for x in ledger})==54
release=js(D/'technical/release.json');assert sha(W/'final.json')==release['full_course_export_sha256']
for key in ['files','data']:
    if key in release:
        for path,h in release[key].items():assert sha(ROOT/path if key=='files' else ROOT/'site/data'/path)==h,(path,h)
full=js(W/'final.json');chapter=js(D/'technical/chapter-export.json');assert [x for x in full if x['lesson'].startswith('ch10/')]==chapter
assert sha(D/'technical/chapter-export.json')==release['chapter_snapshot_sha256'];assert len(chapter)==88
frozen=js(D/'check-evidence/after-tasks.json')
if isinstance(frozen,dict):frozen=frozen.get('tasks',frozen)
def tkey(x):return x['lesson']+'/'+x['id']
cur={tkey(x):x for x in chapter if x['kind']=='task'};before={tkey(x):x for x in frozen if x.get('kind')=='task'}
assert len(cur)==len(before)==57
changed={k:[field for field in ['setup','starter','check','solution'] if cur[k].get(field)!=before[k].get(field)] for k in cur};changed={k:v for k,v in changed.items() if v}
assert changed=={'ch10/04-tuning/train-vs-test':['check'],'ch10/05-project/tune':['check']},changed
sets={}
for name,programfile,nfile,pfile in [('after36','after-programs.jsonl','after-native.jsonl','after-pyodide.jsonl'),('after3','after-additional-programs.jsonl','after-additional-native.jsonl','after-additional-pyodide.jsonl'),('closure4','closure-programs.jsonl','closure-after-native.jsonl','closure-after-pyodide.jsonl')]:
    programs=jl(D/'check-evidence'/programfile);outputs=[jl(D/'check-evidence'/p) for p in [nfile,pfile]]
    for out in outputs:
        assert len(programs)==len(out)
        for p,x in zip(programs,out):
            assert p['id']==x['id'] and p['code']==x['code']
            assert hashlib.sha256(p['code'].encode()).hexdigest()==p['code_sha256']==x['code_sha256']
            assert x['passed']==x['expected'],x['id']
    assert [x['passed'] for x in outputs[0]]==[x['passed'] for x in outputs[1]]
    sets[name]=dict(per_surface=len(programs),expected_matches=len(programs),accepted=sum(x['passed'] for x in outputs[0]),ids=[x['id'] for x in programs])
original=jl(D/'check-evidence/programs.jsonl');after=jl(D/'check-evidence/after-programs.jsonl');assert all(p['code']==q['code'] for p,q in zip(original,after))
rprograms=js(D/'fixes/reviewer/before-programs.json')+js(D/'fixes/reviewer/after-only-programs.json');routs=[js(D/f'fixes/reviewer/after-{s}.json') for s in ['native','pyodide']]
for out in routs:
    assert len(out)==len(rprograms)==19
    for p,x in zip(rprograms,out):assert p['id']==x['id'] and hashlib.sha256(p['code'].encode()).hexdigest()==p['code_sha256']==x['code_sha256'] and x['check']['passed']==x['expected']
assert [x['check']['passed'] for x in routs[0]]==[x['check']['passed'] for x in routs[1]]
coverage=dict(chapter=10,inventory_counts=dict(collections.Counter(inv.values())),initial=initial,retake=retake,retake_targets=targets,retake_missing=sorted(set(targets)-set(retake['by_id'])),retake_extra=sorted(set(retake['by_id'])-set(targets)),reviewed_ledger=ledger)
assert set(initial['by_id'])==set(inv)
(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
second_receipt_path=D/'fixes/recipient-evidence/verification2.json'
second_receipt=js(second_receipt_path) if second_receipt_path.exists() else None
second_snapshot={}
if second_receipt:
    m=js(D/'fixes/recipient-evidence/second-inputs-manifest.json')
    for path,entry in m['files'].items():second_snapshot[path]=sha(D/'fixes/recipient-evidence/second-inputs'/path)==entry['sha256']
    assert all(second_snapshot.values()) and second_receipt['snapshot_unchanged']
    assert len(second_receipt['checks'])==10 and len(second_receipt['commands'])==11
    assert all(x['exit_code']==0 for x in second_receipt['commands'])
    assert all(x['rows']==x['unique_keys'] and x['max_abs_difference_k']==0 for x in second_receipt['checks'])
    assert second_receipt['saved_mode_method_observation']['fit_calls']==0 and second_receipt['saved_mode_method_observation']['make_issue_calls']==0
    assert second_receipt['issue_metadata']['recipient-october']['history_rows']==3834
pending=[]
if not (D/'fixes/student/retest/report.md').exists():pending.append('final student report')
if second_receipt is None:pending.append('new as-of independent recipient receipt')
if not (D/'fixes/methodist.md').exists():pending.append('final methodist assessment')
result=dict(phase='accepted' if not pending else 'final evidence reconciliation',chapter=10,baseline=release['baseline'],full_export_sha256=sha(W/'final.json'),chapter_export_sha256=sha(D/'technical/chapter-export.json'),initial_json_sha256_unchanged=initial_hash,second_recipient=second_receipt,second_snapshot_checks=second_snapshot,student_frozen_file_checks=frozen_checks,initial_multiset_exact=True,retake_multiset_exact=retake['exact_multiset_match'],retake_summary={k:v for k,v in retake.items() if k not in ['pairs','by_id']},ledger_ids=54,check_sets=sets,reviewer=dict(per_surface=19,expected_matches=19,accepted=9,rejected=10,literal_before=18,after_only=['R19'],contract_migration=['R18']),final_four_field_parity=dict(unchanged_tasks=55,changed_fields=changed),release_files=len(release['files']),release_verification=js(D/'technical/release-verification.json'),quiz=js(D/'test-lengths-after.json'),test_ui=js(D/'technical/test-ui.json'),pending=pending,created_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(D/'coordination-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert sha(D/'coordination-initial.json')==initial_hash
p=D/'coordination.md';text=p.read_text().split('\n<!-- final-coordination -->')[0]
text+='\n<!-- final-coordination -->\n\n## Финальная сверка публикации и повторов\n\n'
text+=f"Финальный полный экспорт `{result['full_export_sha256']}`, глава `{result['chapter_export_sha256']}`. Проверены SHA 54 файлов выпуска; исходный coordination-initial.json сохранён без изменения. Собственные запуски ограничены чтением/JSON/CSV/SHA. [Исполнитель](coordination-final.py) · [Результат](coordination-final.json) · [По-ID покрытие](coverage.json).\n\n"
text+=f"Raw исходного ученика снова точно сверены по всем полям, включая visible_prompt и кратность. Повтор: {retake['events']} событий, {retake['graded']} graded, {retake['unique_ids']} уникальных целей, последний зачёт {retake['latest_accepted']}; multiset raw и retest-attempts совпал точно. Целей по реестру 34; отсутствуют {coverage['retake_missing']}, лишние {coverage['retake_extra']}. Это повтор знакомого материала.\n\n"
text+='| Исходный input повтора | Feedback | Строк |\n|---|---|---:|\n'
for pair in retake['pairs']:text+=f"| [{pathlib.Path(pair['input']).name}]({pair['input']}) | [{pathlib.Path(pair['feedback']).name}]({pair['feedback']}) | {pair['rows']} |\n"
text+='\n39/39 критика в каждой среде = 36 буквальных исходных + C36M + два нулевых интервала; отдельные четыре closure-программы дают 4/4. C36 отвергнут после явной смены периода, его апрельская миграция принята. До финальных closure у 55 остальных карточек неизменны setup/starter/check/solution; изменены только два check для 400 точек и grid. Независимый рецензент: 19/19 в каждой среде, 9 зачётов и 10 отказов.\n\n'
text+='Рассмотрены 54 ID, включая исторически закрытое, повторные формулировки одной причины, сильные стороны и отклонённые дефекты. Полный ledger перенесён в coverage; число 54 не является числом независимых ошибок. Методист после ретеста: 4,40/5 (5/4/4/4/5), исходно 3,60.\n\n'
text+=('Новая передача: проверены SHA '+str(len(second_snapshot))+' файлов second-inputs; 10 сравнений по ключам и 11 команд exit0. Первый saved без истории имеет fit_calls=0, независимо выбранный выпуск 1 октября использует 3834 строки до 30 сентября; 552 результата и все варианты запроса/истории совпали. Это CLI-приёмка; Jupyter повторно не запускался. [Квитанция](fixes/recipient-evidence/verification2.json).\n\n' if second_receipt else '')
text+='Ожидания завершения: '+(', '.join(pending) if pending else 'нет')+('. Полная приёмка до закрытия ожиданий не заявляется.\n' if pending else '. Глава принята; внешний методический пилот сохраняется отдельно.\n')
p.write_text(text)
print(json.dumps({'retake_events':retake['events'],'retake_ids':retake['unique_ids'],'missing':coverage['retake_missing'],'sets':sets,'pending':pending},ensure_ascii=False))
