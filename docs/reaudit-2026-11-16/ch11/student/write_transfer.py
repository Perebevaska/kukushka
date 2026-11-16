import json
from pathlib import Path
D=Path(__file__).parent; T=D/'native_transfer';T.mkdir(exist_ok=True)
n=json.load(open('/private/tmp/kuch11round/student/extra/ch11-pytorch-tabular.ipynb'))
cls=''.join(n['cells'][12]['source']).split('\nmodel = DeliveryNet')[0]
(T/'model_def.py').write_text('import torch\nfrom torch import nn\n'+cls+'\n')
(T/'predict.py').write_text('''import json,sys,joblib
from pathlib import Path
import numpy as np,pandas as pd,torch
from model_def import DeliveryNet
torch.set_num_threads(1);torch.set_num_interop_threads(1)
D=Path(__file__).resolve().parent
meta=json.loads((D/'metadata.json').read_text());scaler=joblib.load(D/'scaler.joblib')
model=DeliveryNet(meta['n_in'],**meta['architecture'])
model.load_state_dict(torch.load(D/'delivery_state.pt',map_location='cpu',weights_only=True));model.eval()
features=pd.read_csv(sys.argv[1]) if len(sys.argv)>1 else pd.read_csv(D/'control_features.csv')
if set(features.columns)!=set(meta['columns']):raise ValueError('Expected encoded features: '+str(meta['columns']))
xt=torch.tensor(scaler.transform(features[meta['columns']]),dtype=torch.float32)
with torch.no_grad():pred=model(xt).numpy()*meta['y_std']+meta['y_mean']
if len(sys.argv)==1:
    expected=pd.read_csv(D/'control_predictions.csv')['prediction_minutes'].to_numpy()
    np.testing.assert_allclose(pred,expected,atol=1e-5,rtol=1e-5)
    print('16 control predictions match; maxdiff minutes',float(abs(pred-expected).max()))
print(json.dumps({'unit':'minutes','predictions':pred.tolist()}))
''')
(T/'README.md').write_text('''# Передача сети времени доставки

Это фактически выбранная по validation сеть моего native-extra.ipynb, состояние после лучшей эпохи. `metadata.json` хранит архитектуру, порядок one-hot столбцов, y_mean/y_std и версии. `scaler.joblib` обучен только на train. `delivery_state.pt` — веса.

Запуск без обучения: `python predict.py` сверяет16контрольных строк; `python predict.py encoded_features.csv` выдаёт минуты. Нужны numpy,pandas,scikit-learn,torch,joblib из указанной в metadata среды. УстройствоCPU,1поток.

Вход — уже подготовленные16числовых/one-hot столбцов с именами вmetadata. Для исходных доставок: created→час, distance_km/items/hour/courier/weather/shop_id→get_dummies, затем reindex(columns=metadata columns,fill_value=0). Передавайте типы courier/weather/shop_id как при обучении и сообщайте неизвестные категории; не подгоняйте scaler заново. Обучение отфильтровало actual_min1..299; actual_min для прогноза не нужен.

Контрольные прогнозы сохранены до загрузки нового объекта, в исходных минутах. Рецепт и состояние не выбираются по финальномуtest. Файлы ytest в передачу не входят.
''')
T=D/'digits_transfer';T.mkdir(exist_ok=True)
(T/'predict.py').write_text('''import json,sys,joblib
from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent
model=joblib.load(D/'digits_model.joblib')
X=np.load(sys.argv[1]) if len(sys.argv)>1 else np.load(D/'control_features.npy')
if X.ndim!=2 or X.shape[1]!=64 or not np.isfinite(X).all() or X.min()<0 or X.max()>1:raise ValueError('Input must be n x 64 finite pixels in [0,1]')
P=model.predict_proba(X)
if len(sys.argv)==1:
    np.testing.assert_allclose(P,np.load(D/'control_proba.npy'))
    print('16 control predictions match')
print(json.dumps({'prediction':model.classes_[P.argmax(axis=1)].tolist(),'confidence':P.max(axis=1).tolist()}))
''')
(T/'README.md').write_text('''# Передача digits

Свой проект — digits-project.ipynb. Запуск `python predict.py` загружает сохранённую модель безfit и сверяет16прогнозов; `python predict.py request.npy` принимает(n,64)яркости0..1,развёрнутые по строкам8×8. Сначала делите исходныеpixels0..16на16; не стандартизуйте заново. Модель поддерживает10классовdigits,это не готовый распознаватель целого документа.

`decision_before_labels.json` фиксирует выбранную поvalidation модель и очередь37цифр дооткрытияфинальныхметок. `evaluation.csv` — оценкапослефиксации; `metrics.json` —accuracyчистая/размытая и ошибкивнеочереди. Входыcontrolне содержатметок.

Для других размеров/фона нужны отдельная подготовка и независимаяпроверка. Телефоннуюточность по этим цифрам не вычисляю. Использованы sklearn1.8.0,numpy средыnative; точныеверсиивoutputпервойячейки.
''')
