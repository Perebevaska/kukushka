from acceptance_runner import Chapter, ROOT
import numpy as np
import pandas as pd

with Chapter('ch06') as c:
    c.probe('09-project','prepare', "X_train.iloc[0, 0] += 100")
    c.probe('09-project','final', "model.fit(X_train, y_train * 0)")
    c.probe('09-project','final', 'test_acc = round((model.predict(X_test)==y_test).mean(),3)', expected=True)
    c.probe('09-project','top','top_ids=top_ids[::-1]')
    c.probe('07-regression','residuals',"res['pred'] = res['pred'].iloc[::-1].to_numpy()")
    c.probe('02-split','depth-curve',expected=True)
    source=c.tasks['02-split','depth-curve']['solution']
    # Test labels may change after final ID allocation; tuning must not consult them.
    c.probe('02-split','depth-curve',code=source.replace('train_scores, validation_scores = [], []', 'y_test = ~y_test\ntrain_scores, validation_scores = [], []'),expected=True)
    p=pd.Series([0,.25,.5,.75,1])
    bins=pd.cut(p,[0,.25,.5,.75,1],include_lowest=True)
    assert bins.notna().sum()==5
    dates=pd.read_csv(ROOT/'site/data/guests_churn_dates.csv')
    assert dates.guest_id.is_unique and (dates.target_end_exclusive=='2026-11-30').all()
    fresh=pd.read_csv(ROOT/'site/data/guests_current.csv')
    assert not {'churned','card_blocked'} & set(fresh)
    print('OK calibration edges, dates, fresh schema')
