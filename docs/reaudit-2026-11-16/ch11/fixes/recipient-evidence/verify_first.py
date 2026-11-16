from pathlib import Path
import os,sys,json,hashlib,subprocess,platform,importlib.metadata as im
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','LOKY_MAX_CPU_COUNT'):os.environ[k]='1'
import numpy as np,pandas as pd,joblib,torch
from scipy.ndimage import gaussian_filter
from threadpoolctl import threadpool_limits
threadpool_limits(1)
torch.set_num_threads(1);torch.set_num_interop_threads(1)
D=Path(__file__).resolve().parent; N=D/'first-inputs/native'; G=D/'first-inputs/digits'; O=D/'first-outputs'; O.mkdir(exist_ok=True)
report={'python':sys.version,'platform':platform.platform(),'versions':{p:im.version(p) for p in ('torch','scikit-learn','numpy','pandas','joblib','scipy')},'device':'cpu','threads':1,'commands':[]}
def cli(kind,name,input_path=None):
 script={'native':N,'digits':G}[kind]/'predict.py'
 cmd=[sys.executable,str(script)]+([str(input_path)] if input_path else [])
 p=subprocess.run(cmd,text=True,capture_output=True,env=os.environ)
 (O/(name+'.stdout')).write_text(p.stdout);(O/(name+'.stderr')).write_text(p.stderr)
 report['commands'].append({'name':name,'command':cmd,'returncode':p.returncode,'stdout':str((O/(name+'.stdout')).relative_to(D)),'stderr':str((O/(name+'.stderr')).relative_to(D))})
 if p.returncode:raise RuntimeError(name+': '+p.stderr)
 return json.loads(p.stdout.strip().splitlines()[-1])
# The first executable path for each package remains its documented reload command.
native_cli=cli('native','native-control');digits_cli=cli('digits','digits-control')
# Check stable feature hashes as keys because the native package does not carry source IDs.
meta=json.loads((N/'metadata.json').read_text()); X=pd.read_csv(N/'control_features.csv')[meta['columns']]
key=lambda row:hashlib.sha256(np.asarray(row,dtype='<f8').tobytes()).hexdigest()
native_keys=[key(row) for row in X.to_numpy()]
ref=pd.read_csv(N/'control_predictions.csv').prediction_minutes.to_numpy()
pred=np.asarray(native_cli['predictions']);np.testing.assert_allclose(pred,ref,atol=1e-5,rtol=1e-5)
rows=[]
for i,(k,r,p) in enumerate(zip(native_keys,ref,pred)):rows.append({'position':i,'features_sha256':k,'expected_minutes':r,'actual_minutes':p,'absdiff_minutes':abs(r-p)})
pd.DataFrame(rows).to_csv(O/'native-controls-keyed.csv',index=False)
perm=np.random.default_rng(157).permutation(16)
requests={'single':X.iloc[[7]],'shuffle':X.iloc[perm,list(range(15,-1,-1))],'subset':X.iloc[[15,2,11,4]]}
native_checks={}
for name,frame in requests.items():
 f=O/('native-'+name+'.csv');frame.to_csv(f,index=False);got=np.array(cli('native','native-'+name,f)['predictions'])
 keyed=dict(zip(native_keys,pred));expect=np.array([keyed[key(row)] for row in frame[meta['columns']].to_numpy()])
 np.testing.assert_allclose(got,expect,atol=1e-5,rtol=1e-5);native_checks[name]={'n':len(frame),'maxdiff_minutes':float(abs(got-expect).max()),'keys':[key(row) for row in frame[meta['columns']].to_numpy()]}
report['native']={'control_n':16,'maxdiff_minutes':float(abs(pred-ref).max()),'unique_feature_keys':len(set(native_keys)),'original_source_ids_present':False,'checks':native_checks,'architecture':meta['architecture'],'input_columns':meta['columns'],'unit':'minutes','inverse_target_transform':{'y_std':meta['y_std'],'y_mean':meta['y_mean']},'labels_available':False,'accuracy_or_mae_recomputed':None}
# Freeze the provided queue/rule using only confidence and position, before the full truth column.
decision=json.loads((G/'decision_before_labels.json').read_text());scores=pd.read_csv(G/'evaluation.csv',usecols=['position','confidence'])
queue=scores.sort_values(['confidence','position'],kind='stable').head(decision['capacity_digits']).position.astype(int).tolist()
freeze={'rule':'ascending confidence; then ascending position','capacity_digits':37,'selected_positions':queue,'artifact_positions':decision['queue'],'matches_artifact':queue==decision['queue'],'unit':'digit','label_access_note':'README and first three evaluation rows inspected earlier; no rule or position was changed after label access. Full truth read only after this freeze.'}
(O/'queue-rule-before-full-labels.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n');assert freeze['matches_artifact']
# Independent saved model check; prevent any fit on the recipient object.
model=joblib.load(G/'digits_model.joblib')
def forbid(*a,**kw):raise AssertionError('Recipient verification forbids fitting')
model.fit=forbid
control=np.load(G/'control_features.npy');P=model.predict_proba(control);refP=np.load(G/'control_proba.npy');np.testing.assert_allclose(P,refP)
assert P.shape==(16,10);assert (model.classes_==np.arange(10)).all()
dkeys=[key(row) for row in control];dref=dict(zip(dkeys,P));digit_checks={}
for name,indices in {'single':[7],'shuffle':perm,'subset':[15,2,11,4]}.items():
 incoming=control[indices];f=O/('digits-'+name+'.npy');np.save(f,incoming);got=cli('digits','digits-'+name,f)
 expected=np.array([dref[key(row)] for row in incoming]);actual=model.predict_proba(incoming)
 np.testing.assert_allclose(actual,expected);assert got['prediction']==model.classes_[expected.argmax(1)].tolist();np.testing.assert_allclose(got['confidence'],expected.max(1))
 digit_checks[name]={'n':len(incoming),'maxdiff_proba':float(abs(actual-expected).max()),'keys':[key(row) for row in incoming]}
# A separate available batch: original 16 pixels blurred at sigma=1.1, constant-zero border.
blur=np.array([gaussian_filter(row.reshape(8,8),sigma=1.1,mode='constant',cval=0).reshape(64) for row in control])
f=O/'digits-other-batch-sigma1.1.npy';np.save(f,blur);blur_cli=cli('digits','digits-other-batch-sigma1.1',f);bP=model.predict_proba(blur)
assert blur_cli['prediction']==model.classes_[bP.argmax(1)].tolist()
np.save(O/'digits-other-batch-sigma1.1-proba.npy',bP)
# Audit provided evaluation as a keyed table; do not replace truth with predictions.
eval=pd.read_csv(G/'evaluation.csv');assert eval.position.is_unique and eval.original_index.is_unique
selected=eval.position.isin(queue);errors=eval.truth!=eval.prediction
assert selected.sum()==37;assert np.array_equal(selected.to_numpy(),eval.review.to_numpy())
metrics={'n':len(eval),'provided_evaluation_accuracy':float((~errors).mean()),'errors':int(errors.sum()),'caught_errors':int((errors&selected).sum()),'missed_errors':int((errors&~selected).sum()),'review_share':float(selected.mean()),'unit':'digit','phone_accuracy':None}
# Match the 16 control rows using pixel hash -> prediction, plus their provided position/original_index keys.
# Whole batch pixels are not present, so full450 saved predictions cannot yet be independently recomputed.
rows=[]
for i,k in enumerate(dkeys):
 row=eval.iloc[i];rows.append({'position':int(row.position),'original_index':int(row.original_index),'pixels_sha256':k,'saved_model_prediction':int(model.classes_[P[i].argmax()]),'provided_evaluation_prediction':int(row.prediction),'provided_truth':int(row.truth)})
pd.DataFrame(rows).to_csv(O/'digits-controls-keyed.csv',index=False)
control_eval_match=all(r['saved_model_prediction']==r['provided_evaluation_prediction'] for r in rows)
report['digits']={'control_n':16,'control_proba_shape':list(P.shape),'control_maxdiff_proba':float(abs(P-refP).max()),'unique_pixel_keys':len(set(dkeys)),'classes':model.classes_.tolist(),'control_vs_evaluation_first16_match':control_eval_match,'checks':digit_checks,'other_batch':{'n':16,'source':'provided control_features.npy','transform':'each row reshape8x8; scipy.ndimage.gaussian_filter sigma1.1 modeconstant cval0; flattenrowmajor; already0..1','changed_predictions':int((P.argmax(1)!=bP.argmax(1)).sum()),'accuracy':None,'reason_accuracy_unavailable':'independent labels not supplied with the pixel batch; original evaluation is a different blur condition'},'queue':freeze,'evaluation_table_check':metrics,'full450_reprediction_from_first_package':False,'first_missing_step':'To rerun the full450 clean/blurred accuracy and queue from model outputs, supply the actual450 pixel matrices with position/original_index mapping, or a complete documented data/split/blur reconstruction entry point. evaluation.csv gives only truth, prediction, confidence and IDs.'}
report['first_delivery_result']='16 saved controls and documented new-input CLIs reproduced for both packages; full450 metrics independently recalculated from supplied evaluation table but not yet from missing pixels'
report['source_manifest_unchanged']={}
manifest=json.loads((D/'manifest.json').read_text())
for kind,files in manifest.items():
 p=D/'first-inputs'/kind;report['source_manifest_unchanged'][kind]=all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in files.items())
(D/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['native','digits','source_manifest_unchanged']},ensure_ascii=False,indent=2))
