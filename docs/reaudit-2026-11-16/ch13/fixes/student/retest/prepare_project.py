from pathlib import Path
import json,shutil
D=Path(__file__).parent;P=Path('/private/tmp/kuch13round/student-retest')
shutil.copytree(P/'data',D/'data',dirs_exist_ok=True)
n=json.loads((P/'own-previous/project-template.ipynb').read_text())
n['cells'][0]['source']=['# Повтор проекта главы 13\n\nНовая копия моего ранее выполненного проекта, текущие CSV из публичного пакета. Выборы и код переиспользованы явно; это повтор знакомых данных, а не новый слепой эксперимент. Все code-ячейки в этой копии будут реально исполнены заново в отдельном Python-процессе с чистым namespace.']
for c in n['cells']:
 if c['cell_type']=='code':
  c['outputs']=[];c['execution_count']=None
  s=''.join(c['source'])
  s=s.replace("macro_f1=f1_score(target.loc[b],pred,labels=labels,average='macro')","macro_f1=f1_score(target.loc[b],pred,labels=labels,average='macro',zero_division=0)")
  s=s.replace("labels=labels,average=None)","labels=labels,average=None,zero_division=0)")
  c['source']=s.splitlines(True)
code="""counts=focus.groupby('period').neg.agg(signals='sum',n='size')
bad_counts=bad[bad.shop_id==focus_shop].groupby('period').size()
theme_counts=bad[(bad.shop_id==focus_shop)&(bad.topic==cause)].groupby('period').size()
summary=counts.join(bad_counts.rename('all_signals')).join(theme_counts.rename('delivery_signals'))
summary['signal_share']=summary.signals/summary.n
summary['topic_share_among_signals']=summary.delivery_signals/summary.all_signals
summary.to_csv('retest-period-summary.csv')
start=n.date.min().date();end=n.date.max().date();border=change_date.date()
lines=[f'Управляющей сетью. По синтетическому reviews_new.csv проверяем {focus_shop}.',
 f'До: {start} включительно до {border} исключительно; после: {border} включительно по {end} включительно. Единица — отзыв, не уникальный гость или посетитель.']
for period in ['до','после']:
 a=summary.loc[period]
 lines.append(f'{period}: сигналов {int(a.signals)}/{int(a.n)} всех отзывов точки = {a.signal_share:.1%}; основная тема {cause}: {int(a.delivery_signals)}/{int(a.all_signals)} всех сигналов этого периода = {a.topic_share_among_signals:.1%}.')
lines += [f'Точка выбрана по максимальному месячному приросту, неделя — {border}; максимум уровня октября у {worst_level}. В неделю скачка {int(weekly_counts.loc[change_date,focus_shop])} отзывов. Обе группы больше30; отдельные цитаты и редкие темы не трактуем как репрезентативную выборку.',
 'Прошу управляющую сопоставить с журналом доставок этой точки до/после: опоздания/все доставки, неверные заказы/все доставки, смены курьеров и упаковку. Это проверка гипотезы, причинный эффект по отзывам не установлен.',
 f'Поправка старыми рейтингами TPR={tpr:.3f}, FPR={fpr:.3f} даёт {adj}; перенос на жалобы и оба периода не доказан. reviews_new_gold.csv имеет label_source=synthetic_kind_neg_or_mixed: это генератор, не независимые люди.',
 'Следующий шаг: собрать новые реальные отзывы обоих периодов и независимо, вслепую разметить по единой инструкции (включая отмеченные и неотмеченные), оценить неопределённость долей и ошибок по периодам; затем решать об операционном вмешательстве.']
interpretations=['Подтверждает проблему поиска адреса; дополнительно негативно оценивает капучино.', 'Подтверждает проблему поиска адреса; дополнительно жалуется на отсутствие приветствия.', 'Подтверждает проблему поиска адреса и намерение не возвращаться.', 'Подтверждает пролитый кофе в упаковке; не доказывает опоздание.', 'Подтверждает неверный заказ; дополнительно содержит жалобу на волос в салате.']
for id,text,meaning in zip(quote_ids,quotes,interpretations):lines += [f'{id}: «{text}»',meaning]
lines += ['Цитаты подтверждают конкретные ситуации в этих текстах, не частоту среди всех гостей и не одну доказанную причину. Частоты тем посчитаны по всем сигналам соответствующего периода, одна основная тема не покрывает остальные упоминания.']
Path('letter-retest.md').write_text('\\n\\n'.join(lines))
print(summary.to_string());print('\\n\\n'.join(lines))
"""
n['cells'].extend([dict(cell_type='markdown',metadata={},source=['## Дополнение к текущему брифу: письмо и знаменатели']),dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=code.splitlines(True)),dict(cell_type='markdown',metadata={},source=['**Вывод.** Письмо выводит числители и знаменатели из тех же текущих строк, сохраняет обе границы периодов и исходные ID цитат. Содержимое цитат проверено отдельно от основной темы, внешний недостаток независимой человеческой разметки явно остаётся.'])])
for i,c in enumerate(n['cells']):c['id']=f'retest-{i:03}'
(D/'project-retest.ipynb').write_text(json.dumps(n,ensure_ascii=False,indent=1))
# Updated extra prose + explicitly historical outputs; do not rerun unchanged code.
for name in ['ch13-pymorphy3.ipynb','ch13-transformers.ipynb']:
 new=json.loads((P/'extra'/name).read_text());old=json.loads((P/'own-previous'/name).read_text())
 old_code=[c for c in old['cells'] if c['cell_type']=='code'];new_code=[c for c in new['cells'] if c['cell_type']=='code'];assert len(old_code)==len(new_code)
 for a,b in zip(new_code,old_code):
  a['source']=b['source'];a['outputs']=b['outputs'];a['execution_count']=b['execution_count']
 new['cells'].insert(1,dict(cell_type='markdown',metadata={},source=['## Происхождение outputs\n\nOutputs и code с локальными путями/offline/threads перенесены из МОЕГО прежнего реально исполненного notebook own-previous. Они выполнены в первом прохождении; сейчас заново прочитана новая Markdown-подача, повторного inference/обучения extra нет. Нельзя считать эти outputs новым запуском.']))
 (D/name).write_text(json.dumps(new,ensure_ascii=False,indent=1))
