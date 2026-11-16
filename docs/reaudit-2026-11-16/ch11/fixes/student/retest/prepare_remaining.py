from pathlib import Path
import json
D=Path(__file__).resolve().parent; S=D.parents[2]/'student'
targets=json.loads(Path('/private/tmp/kuch11round/student-retest/targets-public.json').read_text())
notes={
'alpha-sweep':'четыре alpha, res с train/validation, лучший по округлённой validation; 600 final не участвовали.',
'arch-grid':'CV=3 внутри pipeline, четыре кандидата, test_auc и hgb_auc на общих600; не делаю общего вывода обо всех таблицах.',
'depth':'три архитектуры на1350/450, params растёт с шириной; выбор по450validation.',
'epoch-gap':'два списка длины150 без округления; лучший индекс+1 по validation. Формы1350/450 проверяю явно.',
'loss-curve':'curve из200 эпох train; first>last, halved_at от1; графикtrain не заменяетvalidation.',
'regression-net':'две MAE в минутах на тех же461заказах; winner по меньшейMAE, warning при2000 допустим.',
'float32':'ratio=2, revenue32=123456792, lost_rub=2.88; ошибка X по двум значащим цифрам.',
'zero-grad':'с обнулением потери стабилизируются, без накопление даст первый рост; final это последняя записанная loss до обновления.',
'dropout-net':'сравню0,.3,.5 на60train/390validation;150final не трогаю. Одна маска forward/backward.',
'simple':'две доли верных по450цифрам; kNN близокMLP в этом наборе, не гарантия другогонабора.',
'mlp':'proba формы450×10 совпадает с model.predict_proba; acc из тойже матрицы.',
'blur-transfer':'сначала покажу увереннуюошибкуvalidation; меткиblindпока не открываю, ожидаю candidate>=.9 и изображение.'}
for t in targets:
 if t['kind']!='task': continue
 lesson,task=t['id'].split('/')
 dest=D/'raw'/(lesson+'-'+task+'.input.jsonl')
 if dest.exists(): continue
 rows=[json.loads(s) for s in (S/(lesson+'.input.jsonl')).read_text().splitlines()]
 if task=='epoch-gap': rows += [json.loads(s) for s in (S/'03-mlp.retry1.input.jsonl').read_text().splitlines()]
 r=[r for r in rows if r.get('task')==task][-1]
 if task in ['alpha-sweep','depth']: r['code']=r['code'].replace('X_test','X_validation').replace('y_test','y_validation')
 if task=='dropout-net':
  # В публичной карточке валидация именуется X_test в готовой accuracy;
  # явным образом создаю разделение60/390/150 из открытой теории.
  r['code']='from sklearn.datasets import make_moons\nfrom sklearn.model_selection import train_test_split\nX,y=make_moons(600,noise=.3,random_state=1)\nX,X_final,y,y_final=train_test_split(X,y,test_size=.25,random_state=42)\nX_train,X_test,y_train,y_test=train_test_split(X,y,train_size=60,random_state=0)\n'+r['code']
 r['expect']='Q1 решить '+task+'. Q2 доступны актуальные теория/заготовка и мой прежний код. Q3 '+notes[task]
 dest.write_text(json.dumps(r,ensure_ascii=False)+'\n')
