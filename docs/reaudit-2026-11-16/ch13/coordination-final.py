"""Reconcile immutable retest43, initial73 and retest72. stdlib only.
This is a pending-final-closure snapshot, not a claim that REV13-02 is closed.
Does not mutate learner files or re-run any lesson/ML code.
"""
import collections,csv,datetime,hashlib,json,re
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'student';P=D/'fixes/student/retest';W=Path('/private/tmp/kuch13round')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True)
def require(x,m):
 if not x:raise AssertionError(m)
def counts(rr):return {'events':len(rr),'graded':sum(type(r.get('passed')) is bool for r in rr),'true':sum(r.get('passed') is True for r in rr),'false':sum(r.get('passed') is False for r in rr),'hints':sum('hint' in r for r in rr),'transport':sum('browserError' in r for r in rr)}
def table(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def keyed(rr):
 d={r['review_id']:r for r in rr};require(len(d)==len(rr),'unique ID');return d
freezes={}
for name,path in [('initial',S),('retest',P)]:
 manifest={l.split('  ',1)[1]:l.split('  ',1)[0] for l in (path/'SHA256SUMS').read_text().splitlines() if l.strip()}
 require(all(sha(path/n)==h for n,h in manifest.items()),name+' immutable manifest')
 freezes[name]={'files':len(manifest),'all_hashes_match':True,'manifest_sha256':sha(path/'SHA256SUMS')}
require(freezes['initial']['files']==73 and freezes['retest']['files']==72,'freeze counts')
selection=read(P/'selection.json');assigned=set(selection['task_IDs']+selection['question_IDs'])
actual=[];pairs=[];traces=[];walk_expected=[]
for p in sorted(P.glob('*.feedback.jsonl')):
 q=p.with_name(p.name.replace('.feedback.','.input.'))
 if p.name=='04c-llm.feedback.jsonl':q=P/'04c-llm.submit.input.jsonl'
 aa,bb=rows(q),rows(p);require(len(aa)==len(bb),'pair length '+p.name)
 pairs.append({'input':q.name,'feedback':p.name,**counts(bb)})
 for n,(a,b) in enumerate(zip(aa,bb),1):
  ident=a.get('question') or a['lesson']+'/'+a['task'];require(ident==b['id'],'raw pair ID')
  require(all(a.get(k) for k in ['Q1','Q2','Q3']),'Q1-Q3 preaction')
  actual.append({**a,**b});traces.append({'input':q.name,'feedback':p.name,'line':n})
  walk_expected.append({'id':ident,'stage':q.name.removesuffix('.input.jsonl'),**{k:a[k] for k in ['Q1','Q2','Q3']},'feedback':b})
aggregate_raw=rows(S/'retest-attempts.jsonl');aggregate=[{k:v for k,v in r.items() if k!='at'} for r in aggregate_raw]
require(collections.Counter(map(canonical,actual))==collections.Counter(map(canonical,aggregate)),'FULL retest raw/aggregate payload multiset, only at excluded')
require([r['at'] for r in aggregate_raw]==sorted(r['at'] for r in aggregate_raw),'chronological aggregate')
walk=[]
for section in re.split(r'(?m)^## ',(P/'walkthrough.md').read_text())[1:]:
 heading=section.splitlines()[0]
 if ' — ' not in heading:continue
 ident,stage=heading.split(' — ',1);feedback=json.loads(re.search(r'```json\n(.*?)\n```',section,re.S).group(1))
 qs={k:re.search(r'\*\*'+k+r'\.\*\* (.*?)(?=\n\n\*\*Q|\n\n\*\*Следующий)',section,re.S).group(1) for k in ['Q1','Q2','Q3']}
 walk.append({'id':ident,'stage':stage,**qs,'feedback':feedback})
require(collections.Counter(map(canonical,walk))==collections.Counter(map(canonical,walk_expected)),'full Q1-Q4 payload and stage multiset')
first={};last={}
for r in aggregate:first.setdefault(r['id'],r);last[r['id']]=r
require(set(first)==set(last)==assigned,'42 assigned/completed ID sets')
require(len(assigned)==42 and len(actual)==43,'retest counts')
initial=read(D/'coordination-initial.json')
o={'status':'pending final REV13-02 closure, final release and signatures','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freezes':freezes,'retake_export_sha256':read(P/'final-reference.json')['final_export_sha256'],'retake43':{'pairs':pairs,**counts(actual),'unique':len(first),'first_event':counts(list(first.values())),'first_graded':counts(list(first.values())),'latest':counts(list(last.values())),'assigned_IDs':sorted(assigned),'full_raw_aggregate_payload_equal':True,'full_Q1_Q4_equal':True,'walkthrough_events':len(walk),'aggregate_sha256':sha(S/'retest-attempts.jsonl'),'aggregate_scope':'completed42 selection only, immutable first retest phase; later closure stored separately','unused_draft':'04c-llm.input.jsonl was unsent; submit.input is paired to actual feedback','failures':[{'payload':r,'trace':t} for r,t in zip(actual,traces) if r.get('passed') is not True],'time_range':[aggregate_raw[0]['at'],aggregate_raw[-1]['at']]}}
# Independently recompute new predictions, all source fields/periods/weeks and CSVs.
new=keyed(table(D/'technical/data-baseline/reviews_new.csv'));gold=keyed(table(D/'technical/data-baseline/reviews_new_gold.csv'));scored=keyed(table(P/'own-scored.csv'))
require(set(new)==set(gold)==set(scored),'4800 source/gold/new scored IDs')
for i,r in new.items():
 s=scored[i];require(all(s[k]==r[k] for k in ['review_id','date','shop_id','text']),'raw source fields all IDs')
 day=datetime.date.fromisoformat(r['date']);week=(day-datetime.timedelta(days=day.weekday())).isoformat()
 require(s['week']==week and s['period']==('до' if r['date']<'2026-10-05' else 'после'),'all periods and weeks')
 require(int(s['neg'])==int(float(s['p_neg'])>=.5),'all threshold flags')
def summarize(rr):return {'n':len(rr),'signals':sum(int(r['neg']) for r in rr),'complaints':sum(int(gold[r['review_id']]['complaint']) for r in rr)}
shops=sorted({r['shop_id'] for r in scored.values()});months={};weekly={}
for shop in shops:
 parts={k:summarize([r for r in scored.values() if r['shop_id']==shop and ('до' if r['date']<'2026-10-01' else 'после')==k]) for k in ['до','после']}
 months[shop]={**parts,'growth':parts['после']['signals']/parts['после']['n']-parts['до']['signals']/parts['до']['n']}
for week in sorted({r['week'] for r in scored.values()}):weekly[week]={shop:summarize([r for r in scored.values() if r['shop_id']==shop and r['week']==week]) for shop in shops}
focus=max(months,key=lambda k:months[k]['growth']);weeks=sorted(weekly)
boundary=max(weeks[1:],key=lambda w:weekly[w][focus]['signals']/weekly[w][focus]['n']-weekly[weeks[weeks.index(w)-1]][focus]['signals']/weekly[weeks[weeks.index(w)-1]][focus]['n'])
for r in table(P/'own-monthly.csv'):
 for k in ['до','после']:require(abs(float(r[k])-months[r['shop_id']][k]['signals']/months[r['shop_id']][k]['n'])<1e-12,'monthly CSV')
 require(abs(float(r['рост'])-months[r['shop_id']]['growth'])<1e-12,'monthly growth CSV')
for r in table(P/'own-weekly.csv'):
 for shop in shops:require(abs(float(r[shop])-weekly[r['week']][shop]['signals']/weekly[r['week']][shop]['n'])<1e-12,'weekly CSV')
periods={};topics={}
for k in ['до','после']:
 rr=[r for r in scored.values() if r['shop_id']==focus and ('до' if r['date']<boundary else 'после')==k];p=summarize(rr)
 tp=sum(int(r['neg']) and int(gold[r['review_id']]['complaint']) for r in rr);fp=p['signals']-tp
 p.update(tp=tp,fp=fp,tpr=tp/p['complaints'],fpr=fp/(p['n']-p['complaints']),observed=p['signals']/p['n'],manual=p['complaints']/p['n']);p['adjusted']=(p['observed']-p['fpr'])/(p['tpr']-p['fpr'])
 periods[k]=p;topics[k]=dict(collections.Counter(r['topic'] for r in rr if int(r['neg'])))
for r in table(P/'own-audit.csv'):
 for k,v in periods[r['period']].items():
  if k in r:require(abs(float(r[k])-v)<1e-12,'audit CSV')
for r in table(P/'retest-period-summary.csv'):
 p=periods[r['period']]
 for k,v in {'signals':p['signals'],'n':p['n'],'all_signals':p['signals'],'delivery_signals':topics[r['period']]['доставка'],'signal_share':p['observed'],'topic_share_among_signals':topics[r['period']]['доставка']/p['signals']}.items():require(abs(float(r[k])-v)<1e-12,'letter source summary CSV')
growing=max(set(topics['до'])|set(topics['после']),key=lambda t:topics['после'].get(t,0)/periods['после']['signals']-topics['до'].get(t,0)/periods['до']['signals'])
quotes=table(P/'own-quotes.csv');expected=sorted([r for r in scored.values() if r['shop_id']==focus and r['date']>=boundary and int(r['neg']) and r['topic']==growing],key=lambda r:float(r['p_neg']),reverse=True)[:5]
require(quotes==expected,'full top five quote payloads selected growing topic')
letter=(P/'letter-retest.md').read_text();require(all(r['review_id']+': «'+new[r['review_id']]['text']+'»' in letter for r in quotes),'new letter verbatim quotes by source ID')
require(all(str(p['n']) in letter and str(p['signals'])+'/'+str(p['n']) in letter for p in periods.values()),'new letter has both numerical volumes/fractions')
require('synthetic_kind_neg_or_mixed' in letter,'letter simulation source explicit')
require(sha(P/'letter-retest.md')==read(D/'fixes/business-letter-check.json')['letter_sha256'],'critic checked actual new letter')
require(sha(P/'own-letter.md')==sha(S/'own-letter.md'),'old copied letter remains old, not submitted new letter')
notebook=read(P/'project-retest.ipynb');code=[c for c in notebook['cells'] if c['cell_type']=='code'];require(len(code)==6 and all(c.get('outputs') for c in code),'six code cells with saved outputs')
o['new_project']={'focus':focus,'boundary':boundary,'highest_october_level':max(months,key=lambda k:months[k]['после']['signals']/months[k]['после']['n']),'monthly':months,'weekly':weekly,'periods':periods,'topic_signals':topics,'growing_topic':growing,'quotes':quotes,'all_4800_IDs_fields_flags_periods_weeks_verified':True,'all_six_CSV_arithmetic_verified':True,'letter_sha256':sha(P/'letter-retest.md'),'letter_has_both_volumes':True,'business_critic_acceptance':'fixes/business.md B13-01 accepted after actual letter; M13-01 external','execution':{'code_cells':6,'saved_output_cells':sum(bool(c.get('outputs')) for c in code),'kind':'student fresh namespace Python execution; no nbclient/Jupyter PASS','log_sha256':sha(P/'project-execution.log')},'extra':'17 old code-cell outputs reused explicitly; new Markdown read, no new inference','limitations':'Independent arithmetic on submitted predictions, no retraining by coordinator; semantic evidence belongs to reviewed actual letter/quotes; no independent human-labelled real flow'}
# Reused six student IDs are updated observations, not six additional source defects.
student_findings=(P/'own-findings.md').read_text();student_ids=re.findall(r'^## (CH13-ST\d+)',student_findings,re.M)
review=(D/'fixes/review-after.md').read_text();require('REV13-02' in review,'reviewer confirmed new categorical bar finding')
source_ids={r['id'] for r in initial['finding_ledger']['rows']};new_ids=set(student_ids)-source_ids|{'REV13-02'}
crosswalk={'CH13-ST01':{'source':['CH13-ST01','EX13-06','N13-M02','CH13-CHECK01','CH13-CHECK02','REV13-01'],'evidence':'recall95 accepted first attempt, no hint; updated hints not opened by student'},'CH13-ST02':{'source':['CH13-ST02','M13-04','E13-04'],'evidence':'own index-exclusion error did not recur; common IDs preserved'},'CH13-ST03':{'source':['CH13-ST03','B13-01','N13-M01','N13-M04'],'evidence':'actual letter has both volumes, quote IDs and secondary-topic/meaning descriptions; business critic accepted'},'CH13-ST04':{'source':['CH13-ST04','M13-01','B13-02','B13-04','B13-05','N13-M07'],'evidence':'support counterexample before sample; human real-period labels still absent'},'CH13-ST05':{'source':['CH13-ST05'],'evidence':'6 new project cells executed by CLI, extra17 outputs clearly historical; no Jupyter PASS'},'CH13-ST06':{'source':['CH13-ST06'],'evidence':'p-nb not part of selected retake; no new transport claim'},'CH13-ST07':{'source':['CH13-CHECK10','CH13-CHECK11','REV13-02'],'evidence':'weekly first pandasbar attempt failed in Pyodide; direct ax.bar accepted; reviewer independently established native correct render followed by false check and Pyodide render error','status':'pending narrow source fix and separate one-ID student closure'}}
o['finding_crosswalk']={'initial_source_ID_count':len(source_ids),'retest_student_IDs':student_ids,'new_unique_IDs':sorted(new_ids),'union_ID_count':len(source_ids|set(student_ids)|{'REV13-02'}),'observations':crosswalk,'source_ledger':initial['finding_ledger']['rows'],'adjudication':'63 original messages retained; ST01-ST06 are reused IDs; new ST07 and REV13-02 retained separately; final per-ID signature pending'}
o['quality']={'before':[4,4,4,3,3],'before_mean':3.6,'after_preliminary':[5,5,4,4,4],'after_preliminary_mean':4.4,'final_signature':'pending after REV13-02 closure','reference':'fixes/methodist.md'}
o['open_actions']=[{'id':'REV13-02','owner':'Sol high check critic, then original student and Astra high independent reviewer','action':'Publish portable ax.bar example and categorical-coordinate guard; distinguish whole pair permutations from label swaps, preserve date/line controls; original student makes separate one-ID closure after reading current example; final reviewer verifies runtime stages and feedback'},{'id':'final_release','owner':'root coordinator','action':'Freeze new release/export/source/HTML after weekly closure; keep retest43 and both73/72 manifests immutable; compare only affected export fields without inventing full final runtime rerun'},{'id':'quality_signature','owner':'Astra high methodist','action':'Sign final five-criterion after assessment with new closure evidence, preserve provisional4.4 as distinct from final'},{'id':'final63crosswalk','owner':'Astra high independent reviewer and Sol medium coordinator','action':'Sign per-ID decisions for63 original messages plusST07/REV13-02, identify remaining external owner and next action'},{'id':'M13-01','owner':'managing stakeholder together with support lead/data owner','action':'Select real texts from both periods including unsignalled rows; independent blind human labels under common rubric, sampling/missingness/disagreements, numerators/denominators and uncertainty'},{'id':'future_NB_brief_P2','owner':'course editor','action':'Later add direct path to full managerial brief before project task1 in published practice NB; recipient opening NB separately finds letter requirements and both denominators. No editing during this retake.'},{'id':'future_models_pilot_P3','owner':'methodist and SQL-analyst pilot organizer','action':'Observe first-time learner assign training/control IDs for six different reviews with one repeated phrase and different targets; preserve tempo if all three slices reconstructed independently. No required source edit now.'}]
# Categorical narrow patch and both regression sets; Pyodide pandas fails before check.
C=D/'technical/checks';pp=rows(C/'categorical-bar/programs.jsonl');cat={}
for runtime in ['native','pyodide']:
 rr=rows(C/('categorical-after-'+runtime+'.jsonl'));require(len(rr)==len(pp)==7,'categorical7')
 for p,r in zip(pp,rr):require(r['code']==p['code'] and r['code_sha256']==p['code_sha256'],'whole categorical code and SHA')
 reached=[(p,r) for p,r in zip(pp,rr) if r['stage']!='submission_execution']
 cat[runtime]={'total':len(rr),'reached_check':len(reached),'normative_matches_reached':sum(p['expected']==r['passed'] for p,r in reached),'render_errors':[{'index':r['index'],'label':r['label'],'stage':r['stage']} for r in rr if r['stage']=='submission_execution'],'sha256':sha(C/('categorical-after-'+runtime+'.jsonl'))}
 reg=rows(C/('categorical-regression14-'+runtime+'.jsonl'));old=rows(C/'weekly-closure-programs.jsonl');require(len(reg)==len(old)==14,'categorical regression14')
 require(all(r['code']==p['code'] and r['passed']==p['expected'] for p,r in zip(old,reg)),'literal prior14 regression')
 cat[runtime]['old14_matches']=14
left=read(W/'final.json');right=read(W/'final-categorical.json');require(len(left)==len(right)==2454,'full export2454')
require(sha(W/'final.json')==o['retake_export_sha256'],'immutable completed retake export')
idx=lambda rr:{(r['lesson'],r['kind'],r['id']):r for r in rr}
a,b=idx(left),idx(right);require(set(a)==set(b),'full categorical export IDset')
diffs={str(k):sorted(f for f in set(a[k])|set(b[k]) if a[k].get(f)!=b[k].get(f)) for k in a if a[k]!=b[k]}
require(diffs=={str(('ch13/05-project','task','weekly')):['check']},'only weekly.check changes in2454 records')
release=read(D/'technical/release.json');root=D.parents[2]
require(release['full_course_export_sha256'] in [sha(W/'final-categorical.json'),sha(W/'final-clean.json')],'latest release narrow export')
require(all(sha(root/n)==h for n,h in release['files'].items()),'latest57 release hashes')
require(all(sha(root/'site/data'/n)==h for n,h in release['data'].items()),'latest6 CSV hashes')
o['categorical_phase']={'export_sha256':sha(W/'final-categorical.json'),'only_export_diffs':diffs,'full_export_records':len(a),'regressions':cat,'release_files':len(release['files']),'data_files':len(release['data']),'release_all_hashes_match':True,'student_one_ID_closure':'pending; new phase stored separately from retest43','scope':'Native7/7; Pyodide6/6 reachable plus unchanged pandas rendering error before check; old14/14 each runtime. No claim that pandas plotting runtime error itself was fixed.'}
(D/'coordination-final.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

coverage=read(D/'coverage.json')
coverage.update(status=o['status'],retake_results=o['retake43'],own_project_after=o['new_project'],finding_crosswalk=o['finding_crosswalk'],quality=o['quality'],open_actions=o['open_actions'],freeze_retest=o['freezes']['retest'],freeze_initial=o['freezes']['initial'])
coverage['future_observations']={'retake_student_IDs':student_ids,'crosswalk_status':'ST01-ST06 reused; ST07 plus REV13-02 new; pending final categoricalbar closure/signature'}
coverage['current_release_caveat']='Retest43 frozen on68157; current categorical source/export081da5 and release57+6 verified separately. Student one-ID closure and final signatures pending.'
coverage['phases']['categorical_closure']=o['categorical_phase']
coverage['release']={'export_sha256':o['categorical_phase']['export_sha256'],'files':o['categorical_phase']['release_files'],'data':o['categorical_phase']['data_files'],'all_hashes_match':True}
(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')

# Final signed acceptance, including the failed editor-addressing attempt as a separate event.
import ast
closures={}
for phase,expected_pass,expected_files in [('weekly-closure',False,8),('weekly-closure-2',True,9)]:
 path=D/'fixes/student'/phase
 mm={l.split('  ',1)[1]:l.split('  ',1)[0] for l in (path/'SHA256SUMS').read_text().splitlines() if l.strip()}
 require(len(mm)==expected_files and all(sha(path/n)==h for n,h in mm.items()),phase+' freeze')
 aa=rows(path/'weekly.input.jsonl');bb=rows(path/'weekly.feedback.jsonl');gg=rows(S/(phase+'-attempts.jsonl'))
 require(len(aa)==len(bb)==len(gg)==1,phase+' one event')
 g={k:v for k,v in gg[0].items() if k!='at'}
 require({**aa[0],**bb[0]}==g,phase+' entire LOGGED payload equality')
 require(bb[0]['passed'] is expected_pass,phase+' recorded verdict')
 wt=(path/'walkthrough.md').read_text();fb=json.loads(re.search(r'```json\n(.*?)\n```',wt,re.S).group(1))
 require(fb==bb[0],phase+' full Q4')
 for k in ['Q1','Q2','Q3']:
  q=re.search(r'\*\*'+k+r'\.\*\* (.*?)(?=\n\n\*\*Q)',wt,re.S).group(1)
  require(q==aa[0][k],phase+' full '+k)
 closures[phase]={'files':len(mm),'all_hashes_match':True,'manifest_sha256':sha(path/'SHA256SUMS'),'counts':counts(bb),'input_code_sha256':hashlib.sha256(aa[0]['code'].encode()).hexdigest(),'full_LOGGED_payload_and_Q1_Q4_equal':True,'executed_code_equals_input':phase=='weekly-closure-2','semantically_valid_submission_of_input_code':phase=='weekly-closure-2','new_unique_relative_to_retake42':0,'provenance':'Wrong first CodeMirror edited; task executed untouched starter' if phase=='weekly-closure' else 'Task CodeMirror selected and read back; exact same submitted code accepted'}
require(closures['weekly-closure']['input_code_sha256']==closures['weekly-closure-2']['input_code_sha256']=='54948a3300fb28c8ea8e0f48e371b7342706d04b60b58220d44cd27990370383','same code both closures')
diag=read(D/'technical/editor-selector-diagnosis.json');require(diag['card_editors']==2 and diag['task_editors']==1 and diag['first_is_task'] is False,'wrong editor diagnosis')
o['closure_events']=closures
o['event_accounting']={'retake43':43,'wrong_editor_technical_event':1,'corrected_same_code_closure':1,'total_recorded_events':45,'semantically_valid_attempts_of_input_code':44,'unique_selected_IDs':42,'meaning':'43+1+1 raw graded events; the wrong-editor event ran starter, not logged input code, and is excluded from44 semantic attempts. No new ID.'}
review_final=(D/'fixes/review.md').read_text();method_final=(D/'fixes/methodist.md').read_text()
require('Итог независимой приёмки' in review_final and 'исправления учебного содержания' in review_final.lower(),'reviewer final acceptance')
require('Окончательная оценка после точечной проверки weekly' in method_final and 'Пять оценок остаются' in method_final,'methodist final signature')
adjudicated={}
for line in review_final.splitlines():
 if not line.startswith('| '):continue
 cells=[x.strip() for x in line.strip('|').split('|')]
 if cells[0] in source_ids|{'CH13-ST07','REV13-02'}:adjudicated[cells[0]]={'id':cells[0],'after_verdict':cells[1],'evidence_and_limit':' | '.join(cells[2:])}
require(set(adjudicated)==source_ids|{'CH13-ST07','REV13-02'},'all65 final reviewer adjudications')
o['finding_crosswalk']['final_adjudications']=[adjudicated[k] for k in sorted(adjudicated)]
o['finding_crosswalk']['adjudication']='Final reviewer signed all63 original source IDs plusST07/REV13-02; M13-01 external. No separate course defect for bridge addressing.'
for row in o['finding_crosswalk']['source_ledger']:
 row['after_status']=adjudicated[row['id']]['after_verdict'];row['after_evidence']=adjudicated[row['id']]['evidence_and_limit']
o['finding_crosswalk']['observations']['CH13-ST07']['status']='Accepted after independent native/Pyodide differentiation, published portable ax.bar and corrected same-code closure; pandas Pyodide render limitation remains explicit'
# Independent AST/record proof of the final whitespace-only release.
a,b=idx(read(W/'final-categorical.json')),idx(read(W/'final-clean.json'));require(set(a)==set(b) and len(a)==2454,'final export record set')
changed=[k for k in a if a[k]!=b[k]]
require(set(changed)=={('ch13/01-text-prep','task','bigrams'),('ch13/05-project','task','weekly')},'exactly two whitespace records')
for k in changed:
 require([f for f in set(a[k])|set(b[k]) if a[k].get(f)!=b[k].get(f)]==['check'],'only check whitespace')
 require(ast.dump(ast.parse(a[k]['check']),include_attributes=False)==ast.dump(ast.parse(b[k]['check']),include_attributes=False),'AST identical checks')
final_release=read(D/'technical/release.json');require(final_release['full_course_export_sha256']==sha(W/'final-clean.json')=='983b778fba8b204d1b7efcaabf823dcb05d9fa9aa9526f1aabb722a0e24f7d76','signed final release export')
require(all(sha(root/n)==h for n,h in final_release['files'].items()),'final57 SHA');require(all(sha(root/'site/data'/n)==h for n,h in final_release['data'].items()),'final6 data SHA')
o['final_release']={'export_sha256':sha(W/'final-clean.json'),'chapter_snapshot_sha256':final_release['chapter_snapshot_sha256'],'files':len(final_release['files']),'data':len(final_release['data']),'all_hashes_match':True,'runtime_evidence_export':sha(W/'final-categorical.json'),'AST_identical_check_records':[str(k) for k in changed],'unchanged_other_records':len(a)-len(changed),'no_new_runtime_run_claimed':True}
services=read(D/'technical/services.json');require(services['all_services_stopped'] and all(v==0 for k,v in services.items() if k.endswith('exit_code')),'services stopped with exit0');o['services']=services
o['status']='accepted for published educational flow; explicit external and future improvements remain'
o['quality'].update(after=[5,5,4,4,4],after_mean=4.4,final_signature='fixes/methodist.md final signed section')
o['categorical_phase']['student_one_ID_closure']='accepted unchanged code on983b778f after correcting temporary bridge editor selector; original false editor event isolated'
o['open_actions']=[x for x in o['open_actions'] if x['id'] in ['M13-01','future_NB_brief_P2','future_models_pilot_P3']]
o['open_actions'].append({'id':'upstream_Pyodide_pandasbar','owner':'course runtime maintainer and upstream pandas/Pyodide maintainers','action':'Retain tested public ax.bar route. At a runtime upgrade repeat the literal pandas DatetimeIndex bar and portable example; do not claim current upstream renderError was fixed by course guard.'})
o['next_point']={'chapter':14,'action':'Read chapter14 prior report and establish permitted source baseline before delegation; then15, global student interview before critics, universities/all15 assessment, one final push'}
(D/'coordination-final.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
coverage.update(status=o['status'],final_export_sha256=o['final_release']['export_sha256'],release=o['final_release'],quality=o['quality'],finding_crosswalk=o['finding_crosswalk'],findings={'count':len(source_ids),'rows':o['finding_crosswalk']['source_ledger'],'new_IDs':['CH13-ST07','REV13-02'],'final_adjudication_count':len(adjudicated)},closure_events=closures,event_accounting=o['event_accounting'],services=services,next_point=o['next_point'],open_actions=o['open_actions'])
coverage['current_release_caveat']='Full runtime logs retain their original phase SHA. Final983b whitespace AST proof and2452 identical other records transfer evidence without inventing new full execution.'
coverage['phases']['categorical_closure']=o['categorical_phase'];coverage['phases']['final_whitespace_release']=o['final_release'];coverage['future_observations']['crosswalk_status']='All65 unique message IDs signed in fixes/review.md'
(D/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print('ACCEPTED',o['final_release']['export_sha256'],'65 adjudications; freezes73/72/8/9; raw45 semantic44 unique42; services exit0')
