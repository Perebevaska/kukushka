"""Recipient's independent, no-fit second receipt. Run only after CPU release."""
from pathlib import Path
import os, sys, json, hashlib, shutil, subprocess, platform, traceback
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
    os.environ[name] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
import numpy as np
import pandas as pd
import sklearn, scipy, joblib, torch
from scipy.ndimage import gaussian_filter
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
D = Path(__file__).resolve().parent
I = D/'second-inputs'
N, G = I/'native', I/'digits'
O = D/'second-outputs'
O.mkdir(exist_ok=True)
report = {'python': sys.version, 'platform': platform.platform(),
          'versions': {x.__name__: x.__version__ for x in [np, pd, sklearn, scipy, joblib, torch]},
          'device': 'cpu', 'torch_threads': torch.get_num_threads(),
          'torch_interop_threads': torch.get_num_interop_threads(), 'commands': [],
          'fits': 0, 'optimizer_steps': 0, 'external_data': False}
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def key(row):
    return hashlib.sha256(np.asarray(row, dtype='<f8').tobytes()).hexdigest()
def save(name, value):
    (O/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def run(name, script, args=(), cwd=None):
    cmd = [sys.executable, str(script), *map(str, args)]
    p = subprocess.run(cmd, cwd=cwd, env=os.environ.copy(), text=True, capture_output=True)
    (O/(name+'.stdout')).write_text(p.stdout)
    (O/(name+'.stderr')).write_text(p.stderr)
    report['commands'].append({'name': name, 'command': cmd, 'cwd': str(cwd or D),
                               'returncode': p.returncode, 'stdout': 'second-outputs/'+name+'.stdout',
                               'stderr': 'second-outputs/'+name+'.stderr'})
    assert p.returncode == 0, (name, p.stderr)
    return p.stdout
def cli(kind, name, arraypath):
    return json.loads(run(name, I/kind/'predict.py', [arraypath]).splitlines()[-1])
def forbid(*args, **kwargs):
    raise AssertionError('Recipient forbids training/fit')
try:
    # First execution of both second packages follows their README short commands.
    run('native-control', N/'predict.py')
    run('digits-control', G/'predict.py')
    # README replay writes files beside itself, hence execute an explicitly separate copy.
    W = O/'documented-replay'
    assert not W.exists(), 'Retain previous run; do not silently overwrite evidence'
    shutil.copytree(G, W)
    run('digits-readme-replay', W/'replay.py', cwd=W)

    sys.path.insert(0, str(N))
    from model_def import DeliveryNet
    meta = json.loads((N/'metadata.json').read_text())
    scaler = joblib.load(N/'scaler.joblib')
    scaler.fit = forbid
    scaler.partial_fit = forbid
    native = DeliveryNet(meta['n_in'], **meta['architecture'])
    native.load_state_dict(torch.load(N/'delivery_state.pt', map_location='cpu', weights_only=True))
    native.eval()
    features = pd.read_csv(N/'control_features.csv')[meta['columns']]
    tensor = torch.tensor(scaler.transform(features), dtype=torch.float32)
    with torch.no_grad():
        raw = native(tensor).numpy()
    minutes = raw*meta['y_std']+meta['y_mean']
    expected = pd.read_csv(N/'control_predictions.csv').prediction_minutes.to_numpy()
    np.testing.assert_allclose(minutes, expected, atol=1e-5, rtol=1e-5)
    nkeys = [key(r) for r in features.to_numpy()]
    assert len(nkeys) == len(set(nkeys)) == 16
    pd.DataFrame({'row': np.arange(16), 'features_sha256': nkeys, 'raw_standardized_output': raw,
                  'prediction_minutes': minutes, 'saved_minutes': expected,
                  'absdiff_minutes': abs(minutes-expected)}).to_csv(O/'native-controls-keyed.csv', index=False)
    native_checks = {}
    perm16 = np.array([9,0,15,2,13,1,10,6,14,3,12,4,11,7,5,8])
    for name, ix in {'single': [7], 'shuffle': perm16, 'subset': [15,2,11,4]}.items():
        request = features.iloc[ix]
        if name == 'shuffle':
            request = request.iloc[:, ::-1]
        path = O/('native-'+name+'.csv')
        request.to_csv(path, index=False)
        actual = np.asarray(cli('native', 'native-'+name, path)['predictions'])
        ref = dict(zip(nkeys, minutes))
        keys = [key(r) for r in request[meta['columns']].to_numpy()]
        wanted = np.asarray([ref[k] for k in keys])
        np.testing.assert_allclose(actual, wanted, atol=1e-5, rtol=1e-5)
        native_checks[name] = {'n': len(keys), 'keys': keys, 'maxdiff_minutes': float(abs(actual-wanted).max())}
    report['native'] = {'n': 16, 'maxdiff_minutes': float(abs(minutes-expected).max()),
                        'checks': native_checks, 'architecture': meta['architecture'], 'unit': 'minutes',
                        'input_columns': meta['columns'], 'dtype': str(tensor.dtype),
                        'training': native.training, 'scaler': type(scaler).__name__,
                        'inverse_y': {'mean': meta['y_mean'], 'std': meta['y_std']},
                        'labels_available': False, 'mae': None}

    # Full requests and IDs are sufficient; do not use load_digits or reconstruction code.
    ids = pd.read_csv(G/'request_ids.csv')
    assert len(ids) == 450 and ids.position.is_unique and ids.original_index.is_unique
    np.testing.assert_array_equal(ids.position.to_numpy(), np.arange(450))
    rule = json.loads((G/'decision_before_labels.json').read_text())
    assert rule['capacity_digits'] == 37 and rule['tie_break'] == 'smaller_position'
    model = joblib.load(G/'digits_model.joblib')
    model.fit = forbid
    np.testing.assert_array_equal(model.classes_, np.arange(10))
    X = {name: np.load(G/(name+'_request.npy')) for name in ['clean', 'blur']}
    probabilities, frames, queues = {}, {}, {}
    for name, pixels in X.items():
        assert pixels.shape == (450,64) and np.isfinite(pixels).all() and 0 <= pixels.min() <= pixels.max() <= 1
        probs = model.predict_proba(pixels)
        probabilities[name] = probs
        np.save(O/(name+'-actual-proba.npy'), probs)
        frame = ids.copy()
        frame['pixels_sha256'] = [key(r) for r in pixels]
        assert frame.pixels_sha256.is_unique
        frame['prediction'] = model.classes_[probs.argmax(1)]
        frame['confidence'] = probs.max(1)
        ordered = np.lexsort((ids.position.to_numpy(), frame.confidence.to_numpy()))[:37]
        queues[name] = ids.position.iloc[ordered].astype(int).tolist()
        frame['review'] = frame.position.isin(queues[name])
        frames[name] = frame
    # Persist this file before any full final truth read in this run.
    frozen = {'rule': 'ascending maximum predicted probability, then ascending position',
              'capacity_digits': 37, 'unit': 'digit', 'queues': queues,
              'saved_blur_queue': rule['queue'], 'matches_saved': queues['blur'] == rule['queue'],
              'truth_read_in_this_run': False,
              'prior_knowledge': 'First receipt historical metrics and labels are known; no threshold/model/queue changed.'}
    save('queue-rule-before-labels.json', frozen)
    assert frozen['matches_saved']
    expected_blur = np.array([gaussian_filter(row.reshape(8,8), sigma=.65, mode='constant', cval=0).reshape(64) for row in X['clean']])
    np.testing.assert_allclose(X['blur'], expected_blur, atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(X['clean'][:16], np.load(G/'control_features.npy'))
    np.testing.assert_allclose(probabilities['clean'][:16], np.load(G/'control_proba.npy'))
    checks = {}
    perm = np.random.default_rng(20261116).permutation(450)
    for condition in ['clean','blur']:
        checks[condition] = {}
        for name, ix in {'single': [137], 'shuffle': perm, 'subset': [449,17,302,5]}.items():
            path = O/(condition+'-'+name+'.npy')
            np.save(path, X[condition][ix])
            actual = cli('digits', 'digits-'+condition+'-'+name, path)
            wanted = probabilities[condition][ix]
            np.testing.assert_array_equal(actual['prediction'], model.classes_[wanted.argmax(1)])
            np.testing.assert_allclose(actual['confidence'], wanted.max(1), atol=1e-12, rtol=1e-12)
            independent = model.predict_proba(X[condition][ix])
            np.testing.assert_allclose(independent, wanted, atol=1e-12, rtol=1e-12)
            checks[condition][name] = {'n': len(ix), 'maxdiff_proba': float(abs(independent-wanted).max()),
                                      'positions': ids.position.iloc[ix].astype(int).tolist()}
    other = np.array([gaussian_filter(row.reshape(8,8), sigma=1.1, mode='constant', cval=0).reshape(64) for row in X['clean']])
    path = O/'digits-other-sigma1.1.npy'
    np.save(path, other)
    other_cli = cli('digits', 'digits-other-sigma1.1', path)
    other_probs = model.predict_proba(other)
    np.testing.assert_array_equal(other_cli['prediction'], model.classes_[other_probs.argmax(1)])
    np.testing.assert_allclose(other_cli['confidence'], other_probs.max(1), atol=1e-12, rtol=1e-12)
    np.save(O/'digits-other-sigma1.1-proba.npy', other_probs)
    pd.DataFrame({'position': ids.position, 'original_index': ids.original_index,
                  'pixels_sha256': [key(r) for r in other], 'prediction': other_cli['prediction'],
                  'confidence': other_cli['confidence']}).to_csv(O/'digits-other-sigma1.1-results.csv', index=False)

    # Only now read the second-delivery final labels and saved evaluation outputs.
    evaluation = pd.read_csv(G/'evaluation.csv')
    assert len(evaluation) == 450 and evaluation.position.is_unique and evaluation.original_index.is_unique
    joined_truth = ids.merge(evaluation[['position','original_index','truth']], on=['position','original_index'],
                             how='left', validate='one_to_one')
    assert not joined_truth.truth.isna().any()
    full = {}
    for name in ['clean','blur']:
        frame = frames[name]
        saved = pd.read_csv(G/(name+'_replayed.csv'))
        assert len(saved) == 450 and saved.position.is_unique and saved.original_index.is_unique
        compared = frame.merge(saved, on=['position','original_index'], suffixes=('_actual','_saved'), validate='one_to_one')
        assert len(compared) == 450
        compared['prediction_match'] = compared.prediction_actual == compared.prediction_saved
        compared['confidence_absdiff'] = abs(compared.confidence_actual-compared.confidence_saved)
        compared['review_match'] = compared.review_actual == compared.review_saved
        assert compared.prediction_match.all() and compared.review_match.all()
        np.testing.assert_allclose(compared.confidence_actual, compared.confidence_saved, atol=1e-12, rtol=1e-12)
        saved_proba = np.load(G/(name+'_proba.npy'))
        np.testing.assert_allclose(probabilities[name], saved_proba, atol=1e-12, rtol=1e-12)
        compared = compared.merge(joined_truth, on=['position','original_index'], validate='one_to_one')
        compared['error'] = compared.prediction_actual != compared.truth
        compared['caught'] = compared.error & compared.review_actual
        compared['missed'] = compared.error & ~compared.review_actual
        compared.to_csv(O/(name+'-all450-row-verification.csv'), index=False)
        err = compared.error
        full[name] = {'n': len(compared), 'correct': int((~err).sum()), 'accuracy': float((~err).mean()),
                      'errors': int(err.sum()), 'queue_n': int(compared.review_actual.sum()),
                      'caught_errors': int(compared.caught.sum()), 'missed_errors': int(compared.missed.sum()),
                      'review_share': float(compared.review_actual.mean()),
                      'all450_prediction_review_match': True,
                      'maxdiff_confidence': float(compared.confidence_absdiff.max()),
                      'maxdiff_proba': float(abs(probabilities[name]-saved_proba).max()),
                      'unit': 'digit', 'phone_accuracy': None}
    blur_eval = frames['blur'].merge(evaluation, on=['position','original_index'], suffixes=('_actual','_evaluation'), validate='one_to_one')
    assert len(blur_eval) == 450
    blur_eval['prediction_match'] = blur_eval.prediction_actual == blur_eval.prediction_evaluation
    blur_eval['confidence_absdiff'] = abs(blur_eval.confidence_actual-blur_eval.confidence_evaluation)
    blur_eval['review_match'] = blur_eval.review_actual == blur_eval.review_evaluation
    assert blur_eval.prediction_match.all() and blur_eval.review_match.all()
    np.testing.assert_allclose(blur_eval.confidence_actual, blur_eval.confidence_evaluation, atol=1e-12, rtol=1e-12)
    blur_eval.to_csv(O/'blur-evaluation-all450-keyed.csv', index=False)
    report['digits'] = {'classes': model.classes_.tolist(), 'model': str(model), 'full450': full,
                        'checks': checks, 'queue_frozen_before_truth': frozen,
                        'blur_transform_maxdiff': float(abs(X['blur']-expected_blur).max()),
                        'all450_evaluation_match': True,
                        'other_request': {'n': 450, 'sigma': 1.1, 'border': 'constant0',
                                          'changed_predictions_vs_clean': int((other_probs.argmax(1)!=probabilities['clean'].argmax(1)).sum()),
                                          'accuracy': None, 'labels_used': False,
                                          'purpose': 'New inference request, no new quality claim'}}
    report['RCP11-01'] = 'closed: full450 clean/blur inference, keys, confidence, queue and labels reproduced without fitting'
    report['status'] = 'passed'
except Exception as error:
    report['status'] = 'failed'
    report['failure'] = repr(error)
    report['traceback'] = traceback.format_exc()
    raise
finally:
    manifest = json.loads((D/'second-manifest.json').read_text())
    report['second_inputs_unchanged'] = {k: all(sha(I/k/n)==h for n,h in m.items()) for k,m in manifest.items()}
    source = D.parent/'student/retest'
    report['second_student_sources_unchanged'] = {k: all(sha(source/(k+'_transfer')/n)==h for n,h in m.items()) for k,m in manifest.items()}
    first = json.loads((D/'first-receipt.json').read_text())['manifest_sha256']
    report['first19_unchanged'] = {k: all(sha(D/'first-inputs'/k/n)==h for n,h in m.items()) for k,m in first.items()}
    (D/'verification2.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
