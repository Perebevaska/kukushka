"""From repository root: python docs/reaudit-2026-11-16/ch11/technical/expert-numbers.py."""
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS', 'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
os.environ.setdefault('MPLBACKEND', 'Agg')
import contextlib
import hashlib
import io
import json
import platform
import random
import sys
import tempfile
import warnings
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_digits
from threadpoolctl import threadpool_limits

root = Path.cwd()
tech = Path(__file__).resolve().parent
cards = {row['id']: row for row in json.loads((tech/'baseline-export.json').read_text()) if row['kind'] == 'task'}
sys.path.insert(0, str(root/'tools'))
import gen_data
result = {'versions': {p: version(p) for p in ('numpy', 'pandas', 'scipy', 'scikit-learn', 'torch')},
          'python': platform.python_version()}

def namespace(task):
    record = cards[task]
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(record['setup'], ns)
        exec(record['solution'], ns)
    ns['need'] = lambda name, *args: ns[name]
    ns['close'] = lambda x,y,atol=1e-6: np.isclose(x,y,atol=atol,rtol=0)
    return ns

def verdict(task, ns):
    try:
        exec(cards[task]['check'], ns)
    except AssertionError as exc:
        return str(exc)
    return 'accepted'

def capture(task, names):
    ns = namespace(task)
    result[task] = {name: ns[name] for name in names.split()}
    return ns

def compact(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    if isinstance(value, pd.DataFrame): return value.to_dict('records')
    raise TypeError(type(value))

def run():
    with tempfile.TemporaryDirectory() as temp:
        gen_data.OUT = Path(temp)
        with contextlib.redirect_stdout(io.StringIO()):
            gen_data.gen_chapter4(random.Random(4004))
            gen_data.gen_chapter6(random.Random(6006))
        result['data'] = {}
        for filename, key in [('deliveries.csv','delivery_id'),('guests_churn.csv','guest_id')]:
            orig = tech/'data-baseline'/filename
            frame = pd.read_csv(orig)
            result['data'][filename] = {'sha256':hashlib.sha256(orig.read_bytes()).hexdigest(),
                'generated_match':(Path(temp)/filename).read_bytes()==orig.read_bytes(), 'rows':len(frame),
                'duplicate_key':int(frame[key].duplicated().sum()), 'missing':frame.isna().sum()[lambda s:s>0].to_dict()}
            if key == 'delivery_id':
                result['data'][filename].update(dates=[min(frame.created),max(frame.created)], accepted=int(frame.actual_min.between(1,299).sum()))
            else:
                result['data'][filename].update(churn=int(frame.churned.sum()), missing_average_without_visits=int(((frame.visits_90d==0)&frame.avg_check.isna()).sum()))
    os.chdir(tech/'data-baseline')
    capture('shapes','shapes out_shape err_type')
    capture('backprop-check','g_analytic g_numeric rel_err')
    capture('clip-norm','a b c norm_c')
    capture('float32','ratio lost_rub')
    for name, fields in [('alpha-sweep','res best_alpha gap_small gap_big'), ('depth','res params best'), ('epoch-gap','best_epoch best_validation gap_end'), ('dropout-net','res best_rate')]:
        ns = capture(name, fields)
        if name == 'depth': result[name]['samples']=[len(ns[k]) for k in ['y_train','y_test','y_final']]
        if name == 'dropout-net': result[name]['samples']=[len(ns[k]) for k in ['y_train','y_test','y_final']]
    ns = capture('batchnorm','out1 run_mean run_var pred')
    result['batchnorm']['example_running_var'] = {'population':.9+.1*np.var([2,4,6,8]),'torch_convention':.9+.1*np.var([2,4,6,8],ddof=1)}
    ns = namespace('batches')
    result['batches']={'author': verdict('batches',ns)}
    exec('def batches(X,y,size,rng):\n    order=rng.permutation(len(y))\n    yield from ((X[block], y[block]) for block in np.split(order,np.arange(size,len(order),size)))', ns)
    result['batches']['alternative'] = verdict('batches', ns)
    exec('original_batches=batches\ndef batches(X,y,size,rng):\n    for xb,yb in original_batches(X,y,size,rng):\n        yield xb,yb[::-1]', ns)
    result['batches']['wrong_labels'] = verdict('batches', ns)
    ns = namespace('zero-grad')
    result['zero-grad'] = {'author': verdict('zero-grad',ns)}
    original = ns['run']
    ns['run'] = lambda zero_grad,lr=.01,steps=30: original(zero_grad,lr,steps)
    result['zero-grad']['alternative'] = verdict('zero-grad',ns)
    ns['run'] = lambda zero_grad,lr=.01,steps=30: original(zero_grad)
    result['zero-grad']['ignores_lr_and_steps'] = verdict('zero-grad',ns)
    result['zero-grad']['expected_len_if_steps_4'] = 4
    result['zero-grad']['actual_len_if_steps_4'] = len(ns['run'](True,.02,4)[1])
    dg=load_digits()
    result['digits']={'shape':dg.data.shape,'unique_images':len(np.unique(dg.data,axis=0)), 'missing':int(np.isnan(dg.data).sum()),'classes':np.bincount(dg.target), 'range':[dg.data.min(),dg.data.max()]}
    ns = namespace('blur-transfer')
    ps=ns['blind']['proba']
    err=ps.argmax(1)!=ns['final_labels']
    q=ns['queue']
    idx=int(np.flatnonzero(err & ~np.isin(np.arange(len(err)),q))[0])
    result['blur-transfer']={'validation':len(ns['validation']['target']), 'blind':len(err),'rule':ns['rule_name'],'queue':q,
         'stored_before_labels':list(ns['_blur_state']['queue']) == q, 'missed_position':idx,'truth':int(ns['final_labels'][idx]),'pred':int(ps[idx].argmax()),
         'confidence':ps[idx].max(),'errors':[ns[k] for k in ('total_errors','caught_errors','missed_errors')],
         'without_concrete_position':verdict('blur-transfer',ns)}
    # Retain first selection and try to change rule within this submission.
    try:
        ns['open_blur_labels'](ns['example'],'confidence',np.argsort(ps.max(1),kind='stable')[:37],ns['rule_reason'])
        result['blur-transfer']['changed_rule']='accepted'
    except AssertionError as e:
        result['blur-transfer']['changed_rule']=str(e)
    ns=capture('shift','acc_shift acc_aug defense holdout_accuracy')
    result['shift']['new_left_n']=450

with warnings.catch_warnings(), threadpool_limits(limits=1):
    warnings.simplefilter('ignore', category=UserWarning)
    run()
print(json.dumps(result, ensure_ascii=False, indent=2, default=compact))
