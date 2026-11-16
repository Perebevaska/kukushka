"""Annotate changed contracts separately and preserve the original 25 frozen programs."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent
frozen = json.loads((root/'cases-before.json').read_text())
original = {c['id']:c['code'] for c in frozen}
new = []


def add(index, task, expected, reason, code):
    new.append(dict(id=index,task=task,expected=expected,reason=reason,code=code))


add('R26','parse-llm',True,'Новая публичная обработка None; сохраняем именованные индексы исходного R01.',original['R01'].replace('    i, j = answer.find', '    if answer is None:\n        return bad\n    i, j = answer.find'))
add('R27','adjust',True,'Семь обязательных полей с теми же данными и дополнительный осмысленный счётчик.',original['R20']+'\naudit["не_жалобы"] = audit["n"] - audit["complaints"]')
add('R28','adjust',False,'Два периода остались, но у второго пропал второй обязательный знаменатель из разбивки.', original['R20']+'\naudit.loc["после", "n"] = audit.loc["после", "complaints"]')
llm = """import math
from collections import Counter
import pandas as pd
truth = check['topic'].tolist()
flags = [answer == label for answer,label in zip(llm_topic,truth)]
counts = Counter(truth)
right = Counter(label for label,flag in zip(truth,flags) if flag)
n_invalid = sum(answer not in TOPICS for answer in llm_topic)
acc = sum(flags)/len(flags)
acc_llm = round(acc,3)
recall_by_topic = pd.Series({label:round(right[label]/count,3) for label,count in counts.items()})
worst = recall_by_topic.idxmin()
radius = 2*math.sqrt(acc*(1-acc)/len(flags))
low, high = round(acc-radius,3), round(acc+radius,3)
above_reference = acc-radius > .79"""
add('R29','llm-check',True,'Именованный above_reference сравнивает нижнюю границу одной доли с числом.',llm)
add('R30','llm-check',False,'Те же значения, но оставлено только старое имя clearly_better.',llm.replace('above_reference','clearly_better'))
add('R31','llm-check',False,'Сравнивается сама точность вместо нижней границы интервала.',llm+'\nabove_reference = acc > .79')
add('R32','recall95',True,'Контрфактические метки final при прежних текстах и validation меняют только измерение. Оригинальные выходы карточки сохраняют опубликованную фактическую истину.',original['R14']+'''
new_truth = 1 - y_test
new_recall = recall_score(new_truth, p_test >= thr)
assert round(new_recall, 3) != test_recall
assert int((p_test >= thr).sum()) == test_flagged
assert thr == round(max(good),2)
print("heldout_counterfactual",len(new_truth), "threshold",thr, "size",test_flagged,"actual",test_recall, "changed",round(new_recall,3))
''')
add('R33','adjust',False,'Третий период дублирует полную строку одного из двух обязательных.',original['R20']+'\naudit = pd.concat([audit, audit.iloc[[0]]])')
(root/'extra-after.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
(root/'combined-after.json').write_text(json.dumps(frozen+new,ensure_ascii=False,indent=2)+'\n')
(root/'expectations-after.json').write_text(json.dumps([{k:c[k] for k in ("id","task","reason")} | dict(expected_before=c['expected'] if c in frozen else None, expected_current=False if c['id']=='R01' else c['expected']) for c in frozen+new],ensure_ascii=False,indent=2)+'\n')
