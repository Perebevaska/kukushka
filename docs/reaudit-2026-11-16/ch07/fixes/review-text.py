"""Arithmetic counterexamples and scikit-learn sampler, using the course environment."""
from pathlib import Path
import json
from statistics import mean
import warnings

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from sklearn.model_selection import ParameterSampler

# XNOR depends only on the existing binary fields. The product lets a linear model separate four points.
x=np.array([[0,0],[0,1],[1,0],[1,1]])
y=np.array([1,0,0,1])
full=np.column_stack([x,x[:,0]*x[:,1]])
threshold_scores=[.80,.72,.75,.81]
with warnings.catch_warnings(record=True) as warning:
    samples=list(ParameterSampler({'C':[.1,1]}, n_iter=20, random_state=0))
fpr,tpr,thresholds=roc_curve([1,0],[.7,.3],drop_intermediate=False)
out={
    'sklearn':sklearn.__version__,
    'mixed_leaves':{'raw':[.2,.8],'mean_probability':mean([.2,.8]),'hard_votes':mean([0,1])},
    'random_score_realization':{'raw':[.7,.3],'true':[1,0],'fpr':fpr.tolist(),'tpr':tpr.tolist()},
    'deterministic_interaction':{'x':x.tolist(),'y':y.tolist(),'linear_training_accuracy':LogisticRegression(C=100).fit(x,y).score(x,y),'same_rows_plus_product_accuracy':LogisticRegression(C=100).fit(full,y).score(full,y)},
    'finite_parameter_lists':{'n_iter':20,'draws':samples,'fits_with_five_folds_and_refit':len(samples)*5+1,'warning':[str(w.message) for w in warning]},
    'best_at_edge':{'C':[.01,.1,1,10],'fold_means':threshold_scores,'best_C':10,'monotone':all(a<=b for a,b in zip(threshold_scores,threshold_scores[1:]))}}
assert out['deterministic_interaction']['linear_training_accuracy']==.5 and out['deterministic_interaction']['same_rows_plus_product_accuracy']==1
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
