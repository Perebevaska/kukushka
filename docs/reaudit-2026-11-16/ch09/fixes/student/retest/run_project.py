from pathlib import Path
import argparse
import json
HERE=Path(__file__).resolve().parent

def run_project(data=None,key=None,new_member=None,output=None):
    """Repeat the same participant split with an explicit key and new row.

    key: 4x4 numeric array, or None for the documented default seed42 key.
    new_member: four values ordered gender,age,income_k,family_size.
    output: destination for separated internal and contractor-demo packages.
    """
    if output is None:
        output=HERE/"artifacts/default"
    import os
    import sys
    from pathlib import Path
    import json
    import joblib
    import numpy as np
    import pandas as pd
    import sklearn
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_absolute_error
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeRegressor
    from own_model import MyOLS

    RANDOM_STATE = 42
    DATA = Path(data) if data is not None else Path(os.environ.get("COURSE_DATA", str(HERE / "../../../technical/data-baseline")))
    ARTIFACTS = Path(output)
    INTERNAL = ARTIFACTS / "internal"
    CONTRACTOR = ARTIFACTS / "contractor-demo"
    for p in [INTERNAL, CONTRACTOR]:
        p.mkdir(parents=True,exist_ok=True)
    print("Python",sys.version.split()[0],"numpy",np.__version__,"pandas",pd.__version__,"sklearn",sklearn.__version__)
    print("Случайность",RANDOM_STATE,"данные",DATA)


    f = pd.read_csv(DATA / "family_members.csv")
    cols = ["gender","age","income_k","family_size"]
    print("Строк/столбцов",f.shape)
    print("Пропуски",f.isna().sum().to_dict())
    print("Полные дубли",int(f.duplicated().sum()),"повторные ID",int(f.member_id.duplicated().sum()))
    print("Повторные профили",int(f.duplicated(cols).sum()))
    print(f[cols+["spend_k"]].describe().round(2).to_string())


    assert not f.isna().any().any()
    assert f.member_id.is_unique
    assert np.isfinite(f[cols+["spend_k"]].to_numpy()).all()
    assert f.gender.isin([0,1]).all()
    assert (f[["age","income_k","family_size"]]>=0).all().all()
    manifest = pd.read_csv(HERE / "inputs/split-ids.csv")
    assert manifest.member_id.is_unique and set(manifest.member_id)==set(f.member_id)
    row_for_id = pd.Series(np.arange(len(f)),index=f.member_id)
    train_ids = manifest[manifest.split=="train"].sort_values("order").member_id
    test_ids = manifest[manifest.split=="test"].sort_values("order").member_id
    train_idx = row_for_id.loc[train_ids].to_numpy()
    test_idx = row_for_id.loc[test_ids].to_numpy()
    assert len(set(train_ids)&set(test_ids))==0
    X = f[cols].to_numpy(dtype=float)
    y = f.spend_k.to_numpy(dtype=float)
    X_train,X_test = X[train_idx],X[test_idx]
    y_train,y_test = y[train_idx],y[test_idx]
    P = np.asarray(key,dtype=float) if key is not None else np.random.default_rng(RANDOM_STATE).normal(size=(4,4))
    assert P.shape==(4,4) and np.isfinite(P).all()
    rank = int(np.linalg.matrix_rank(P))
    cond = float(np.linalg.cond(P))
    aug_rank = int(np.linalg.matrix_rank(np.column_stack([np.ones(len(X_train)),X_train])))
    hidden = X @ P
    restore_error = float(np.abs(hidden @ np.linalg.inv(P)-X).max())
    assert rank==4 and aug_rank==5
    assert np.allclose(hidden @ np.linalg.inv(P),X)
    print("train/test",len(train_idx),len(test_idx),"ранг P",rank,"cond",cond)
    print("ранг [1,X_train]",aug_rank,"максимальная ошибка восстановления",restore_error)


    open_model = MyOLS().fit(X_train,y_train)
    hidden_model = MyOLS().fit(X_train @ P,y_train)
    sk_model = LinearRegression().fit(X_train,y_train)
    dummy = DummyRegressor(strategy="mean").fit(X_train,y_train)
    pred_open = open_model.predict(X_test)
    pred_hidden = hidden_model.predict(X_test @ P)
    pred_dummy = dummy.predict(X_test)
    metrics = pd.DataFrame([
        {"model":"mean","R2":r2_score(y_test,pred_dummy),"MAE_k":mean_absolute_error(y_test,pred_dummy)},
        {"model":"MyOLS open","R2":r2_score(y_test,pred_open),"MAE_k":mean_absolute_error(y_test,pred_open)},
        {"model":"MyOLS hidden","R2":r2_score(y_test,pred_hidden),"MAE_k":mean_absolute_error(y_test,pred_hidden)}
    ])
    max_pred_diff = float(np.abs(pred_open-pred_hidden).max())
    weight_match = bool(np.allclose(hidden_model.coef_,np.linalg.solve(P,open_model.coef_)))
    assert np.allclose(pred_open,sk_model.predict(X_test))
    assert abs(r2_score(y_test,pred_open)-r2_score(y_test,pred_hidden))<=1e-9
    assert max_pred_diff<1e-7 and weight_match
    print(metrics.round(6).to_string(index=False))
    print("Максимальная разница прогнозов",max_pred_diff,"связь весов",weight_match)


    bad = P.copy()
    bad[:,3] = bad[:,0]+bad[:,1]
    bad_model = MyOLS().fit(X_train @ bad,y_train)
    r2_bad = float(r2_score(y_test,bad_model.predict(X_test @ bad)))
    rows=[]
    for depth in [3,5,8]:
        a=DecisionTreeRegressor(max_depth=depth,random_state=RANDOM_STATE).fit(X_train,y_train)
        b=DecisionTreeRegressor(max_depth=depth,random_state=RANDOM_STATE).fit(X_train @ P,y_train)
        rows.append({"depth":depth,"open":r2_score(y_test,a.predict(X_test)),"hidden":r2_score(y_test,b.predict(X_test @ P))})
    trees = pd.DataFrame(rows)
    print("Плохой ключ: ранг",int(np.linalg.matrix_rank(bad)),"R2",r2_bad,"потеря",r2_score(y_test,pred_open)-r2_bad)
    print(trees.round(6).to_string(index=False))


    known = X[:4]
    assert np.linalg.matrix_rank(known)==4
    P_found = np.linalg.solve(known,hidden[:4])
    restored = hidden @ np.linalg.inv(P_found)
    leaked = float((np.abs(restored-X)<=0.01).all(axis=1).mean())
    new = np.asarray(new_member if new_member is not None else [1,34,95,3],dtype=float).reshape(1,4)
    assert np.isfinite(new).all()
    new_open = float(open_model.predict(new)[0])
    new_hidden = float(hidden_model.predict(new @ P)[0])
    wrong_P = np.random.default_rng(RANDOM_STATE+1).normal(size=(4,4))
    if np.allclose(wrong_P,P):
        wrong_P = np.random.default_rng(RANDOM_STATE+2).normal(size=(4,4))
    new_wrong = float(hidden_model.predict(new @ wrong_P)[0])
    assert np.isclose(new_open,new_hidden)
    print("Восстановленная доля",leaked,"ключ совпал",np.allclose(P_found,P))
    print("Новая анкета,тыс.руб: open",new_open,"hidden",new_hidden,"другой ключ",new_wrong)

    test_predictions = pd.DataFrame({"member_id":f.iloc[test_idx].member_id.to_numpy(),"actual_spend_k":y_test,"open_pred_k":pred_open,"hidden_pred_k":pred_hidden})
    test_predictions.to_csv(INTERNAL/"test-predictions.csv",index=False)
    pd.DataFrame({"member_id":f.iloc[train_idx].member_id.to_numpy(),"split":"train"}).to_csv(INTERNAL/"train-ids.csv",index=False)
    np.save(INTERNAL/"key.npy",P)
    joblib.dump(hidden_model,INTERNAL/"hidden-model.joblib")
    train_export = pd.DataFrame(X_train @ P,columns=["f1","f2","f3","f4"])
    train_export["spend_k"] = y_train
    train_export.to_csv(CONTRACTOR/"train-hidden.csv",index=False)
    pd.DataFrame(X_test @ P,columns=["f1","f2","f3","f4"]).to_csv(CONTRACTOR/"test-hidden.csv",index=False)
    pd.DataFrame(new @ P,columns=["f1","f2","f3","f4"]).to_csv(CONTRACTOR/"new-hidden.csv",index=False)
    pd.DataFrame([dict(zip(cols,new[0])) | {"prediction_k":new_hidden,"wrong_key_prediction_k":new_wrong}]).to_csv(INTERNAL/"new-member.csv",index=False)
    metrics.to_csv(INTERNAL/"metrics.csv",index=False)
    trees.to_csv(INTERNAL/"tree-diagnostic.csv",index=False)
    summary={"rows":len(f),"train":len(train_idx),"test":len(test_idx),"rank":rank,"condition":cond,"r2_open":float(r2_score(y_test,pred_open)),"r2_hidden":float(r2_score(y_test,pred_hidden)),"max_prediction_difference":max_pred_diff,"bad_key_r2":r2_bad,"leaked_fraction":leaked,"new_prediction_k":new_hidden,"wrong_key_prediction_k":new_wrong}
    (INTERNAL/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    letter=f"""Руководителю данных

    На {len(f)} учебных анкетах использовано разбиение {len(train_idx)}/{len(test_idx)}. На тесте R² обычного МНК {summary['r2_open']:.6f}, после обратимого преобразования {summary['r2_hidden']:.6f}. Максимальная разница прогнозов {max_pred_diff:.3g} тыс. ₽. Новая анкета даёт {new_hidden:.2f} тыс. ₽ в год при том же ключе; другой ключ даёт {new_wrong:.2f}.

    Сохраняется множество линейных прогнозов МНК без штрафа. При полном ранге расширенной обучающей матрицы независимо обученные модели совпадают и на новых строках. Явный перенос весов через P^-1 сохраняет любой прогноз независимо от единственности решения. Деревьям и Ridge это обещание не даю. Обусловленность ключа {cond:.2f}; зависимый ключ ранга3 даёт R² {r2_bad:.6f}.

    Эта смесь не обезличивание и не криптографическая защита: по четырём независимым известным парам восстановлена доля {leaked:.1%} профилей. Годовые траты передаются как цель без защиты; отсутствие member_id не предотвращает сопоставление по другим сведениям. Не рекомендую передавать реальные анкеты на основании одного этого приёма. Нужен выбранный владельцем данных защищённый контур доступа и отдельная проверка условий передачи.

    В artifacts/contractor-demo только учебные смеси train/test/new и цель train. В artifacts/internal находятся ID, истинные тестовые ответы, ключ, модель и новые открытые признаки: это внутренний пакет, не комплект подрядчика. Файлы созданы локально, никуда не отправлены. Ключ генерируется один раз и хранится внутри; замена требует повторного согласованного преобразования и обучения.
    """
    (INTERNAL/"letter.md").write_text(letter)
    print(letter)

    receipt_information = {
        "contractor_demo": ["four mixed feature columns", "train spend_k target", "row order within each file"],
        "internal_only": ["member_id mapping", "test targets", "P key", "trained model", "open new row", "seed and preparation source"],
        "warning": "If recipient gets this reproducibility source or the default seed, P can be regenerated. Known independent pairs can recover P. Missing full P does not prove any field confidential."
    }
    (INTERNAL/"receiver-information.json").write_text(json.dumps(receipt_information,ensure_ascii=False,indent=2))
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Repeat a fixed-ID family OLS experiment")
    parser.add_argument("--data",type=Path,default=None)
    parser.add_argument("--key",type=Path,default=None)
    parser.add_argument("--new",type=Path,default=None)
    parser.add_argument("--output",type=Path,default=None)
    args=parser.parse_args()
    key=json.loads(args.key.read_text()) if args.key else None
    new=json.loads(args.new.read_text()) if args.new else None
    print(json.dumps(run_project(args.data,key,new,args.output),ensure_ascii=False,indent=2))
