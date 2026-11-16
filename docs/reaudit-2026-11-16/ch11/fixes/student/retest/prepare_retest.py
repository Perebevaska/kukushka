from pathlib import Path
import json
D=Path(__file__).resolve().parent
S=D.parents[2]/'student'
# Собственные прежние ответы на неизменённые формулы; обновлённые карточки будут
# сверены с актуальным публичным текстом после сигнала готовности пакета.
selected={'01-neuron':['collapse'],'02-backprop':['grad-check','backprop-check'],'04b-softmax':['head-loss','batches']}
expect={
'collapse':'Q1 показать схлопывание линейных слоёв. Q2 формула ассоциативности и numpy из карточки. Q3 W формы (3,2), same=True, with_relu_same=False.',
'grad-check':'Q1 проверить p-y. Q2 центральная разность L(z) при eps=1e-5 из теории. Q3 analytic и numeric около -0.40131 и совпадут до 5 знаков.',
'backprop-check':'Q1 проверить скрытый градиент. Q2 формулы outer, маска ReLU и копии W1 для центральной разности. Q3 значения совпадут до 6 знаков, относительная ошибка будет много меньше 1e-4.',
'head-loss':'Q1 выбрать потери под три цели. Q2 MSE и logaddexp из теории. Q3 три конечные неотрицательные потери; n_cats=[1,2,1,3], потому что sigmoid(z)>.5 при z>0.',
'batches':'Q1 нарезать все 10 строк без потерь и рассогласования. Q2 общая permutation для X и y, yield из теории. Q3 sizes=[4,4,2], covered=True; произвольные метки проверю отдельно на 11 заказах.'}
for lesson,tasks in selected.items():
    rows=[json.loads(x) for x in (S/(lesson+'.input.jsonl')).read_text().splitlines()]
    for task in tasks:
        row=next(x for x in rows if x.get('task')==task)
        row['expect']=expect[task]
        (D/'raw'/(lesson+'-'+task+'.input.jsonl')).write_text(json.dumps(row,ensure_ascii=False)+'\n')
