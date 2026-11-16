import json,shutil
from pathlib import Path
D=Path(__file__).parent;P=Path('/private/tmp/kuch13round/student')
shutil.copytree(P/'data',D/'data',dirs_exist_ok=True)
nb=json.loads((P/'project-template.ipynb').read_text()); cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):cells.append(dict(cell_type='code',metadata={},source=s.splitlines(True),execution_count=None,outputs=[]))
md('# Проект: рост сигналов жалобы в отзывах\n\nСамостоятельный анализ синтетического потока. Единица — отзыв. Проект выполнен по публичному брифу, выбранная точка определяется расчётом максимального месячного прироста.')
code('''import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sklearn
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
RANDOM_STATE=42
DATA=Path('data')
print('Python',sys.version.split()[0])
for lib in [pd,np,sklearn,matplotlib]: print(lib.__name__,lib.__version__)
pd.set_option('display.max_columns',30)
def new_model(class_weight=None):
    return make_pipeline(TfidfVectorizer(ngram_range=(1,2)),LogisticRegression(max_iter=1000,class_weight=class_weight))
''')
md('## 1. Цель\n\nНайти кофейню с наибольшим ростом доли текстов с сигналом жалобы, затем по недельным данным выбрать границу. Управляющая получит таблицы, исходные ключи цитат и письмо. До оценки задаю ориентиры: модели должны обойти наиболее частый класс по accuracy, для тем дополнительно macro-F1; доли и их изменение описывают отзывы, а не посетителей.')
md('## 2. Данные')
code('''r=pd.read_csv(DATA/'reviews_text.csv')
n=pd.read_csv(DATA/'reviews_new.csv',parse_dates=['date'])
print('Старые',r.shape,'новые',n.shape,'диапазон',n.date.min(),n.date.max())
print(n.groupby('shop_id').size())
print(r.isna().sum(),n.isna().sum())
print('Повторы ID',r.review_id.duplicated().sum(),n.review_id.duplicated().sum())
print('Повторяющиеся тексты старые/новые',r.text.duplicated().sum(),n.text.duplicated().sum())
''')
md('**Вывод по данным.** Строки с повторяющимся текстом сохраняю: разные ID могут соответствовать разным отзывам. Дубли текста проверю отдельно при оценке обобщения. Новые отзывы не имеют рейтинга, поэтому модельная доля не равна измеренной доле жалоб.')
md('## 3. Предобработка\n\nПропуски и уникальность ключей проверены выше. Нормализацию выполняет TF-IDF, отрицания сохраняются, добавлены биграммы. Новые прогнозы присоединяю по review_id, а не положением строк.')
code('''assert r.review_id.is_unique and n.review_id.is_unique
assert not r.isna().any().any() and not n.isna().any().any()
labels=sorted(r.topic.unique())
y=(r.rating<=3).astype(int)
quality=[]; text_quality_rows={k:{} for k in ['повторы','новые','без пересечения']}
models={}
for target,name in [(y,'sent'),(r.topic,'topic')]:
    a,b=train_test_split(r.index,test_size=.25,random_state=RANDOM_STATE,stratify=target)
    m=new_model().fit(r.loc[a,'text'],target.loc[a])
    pred=m.predict(r.loc[b,'text'])
    dummy=DummyClassifier(strategy='most_frequent').fit(r.loc[a,['text']],target.loc[a])
    quality.append(dict(target=name,n=len(b),acc=accuracy_score(target.loc[b],pred),dummy=accuracy_score(target.loc[b],dummy.predict(r.loc[b,['text']]))))
    repeated=r.loc[b,'text'].isin(r.loc[a,'text']).to_numpy()
    for key,mask in [('повторы',repeated),('новые',~repeated)]:
        text_quality_rows[key]['n_'+name]=int(mask.sum())
        text_quality_rows[key]['acc_'+name]=accuracy_score(target.loc[b].to_numpy()[mask],pred[mask])
        if name=='topic': text_quality_rows[key]['macro_f1_topic']=f1_score(target.loc[b].to_numpy()[mask],pred[mask],labels=labels,average='macro',zero_division=0)
    models[name]=new_model().fit(r.text,target)
    if name=='sent':
        acc_sent=round(quality[-1]['acc'],3)
        tn,fp,fn,tp=confusion_matrix(target.loc[b],pred,labels=[0,1]).ravel()
        tpr=tp/(tp+fn); fpr=fp/(fp+tn)
    else:
        acc_topic=round(quality[-1]['acc'],3)
        f1_by_topic=dict(zip(labels,f1_score(target.loc[b],pred,labels=labels,average=None)))
        macro_f1=f1_score(target.loc[b],pred,labels=labels,average='macro')
        rarest=target.loc[b].value_counts().idxmin()
        count_ratio=(pred==rarest).sum()/(target.loc[b]==rarest).sum()
        bal=new_model('balanced').fit(r.loc[a,'text'],target.loc[a])
        f1_rare_balanced=f1_score(target.loc[b],bal.predict(r.loc[b,'text']),labels=[rarest],average=None)[0]
a,b=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=RANDOM_STATE).split(r,groups=r.text))
group_test_ids=r.iloc[b].review_id.tolist()
for target,name in [(y,'sent'),(r.topic,'topic')]:
    m=new_model().fit(r.iloc[a].text,target.iloc[a]);p=m.predict(r.iloc[b].text)
    text_quality_rows['без пересечения']['n_'+name]=len(b)
    text_quality_rows['без пересечения']['acc_'+name]=accuracy_score(target.iloc[b],p)
    if name=='topic':text_quality_rows['без пересечения']['macro_f1_topic']=f1_score(target.iloc[b],p,labels=labels,average='macro',zero_division=0)
text_quality=pd.DataFrame(text_quality_rows).T.round(3)
sent=models['sent']; topic_model=models['topic']
print(pd.DataFrame(quality).round(3).to_string(index=False))
print(text_quality.to_string())
print('F1 тем',f1_by_topic,'macro',macro_f1,'редчайшая',rarest,'ratio',count_ratio,'balanced F1',f1_rare_balanced)
print('Старый тест TPR/FPR',tpr,fpr)
''')
md('**Вывод по предобработке и оценке.** Модели проверены отдельно от финального обучения, ориентир most_frequent посчитан на тех же отложенных строках. Сравнение повторов, новых формулировок и группового разбиения выше ограничивает перенос случайного теста на новый источник. Macro-F1 учитывает каждую тему одинаково; balanced меняет компромисс, поэтому финальный заранее заданный конвейер оставлен без перевыбора по новым отзывам.')
md('## 4. Анализ и модели')
code('''predictions=pd.DataFrame({'review_id':n.review_id,'p_neg':sent.predict_proba(n.text)[:,1],'topic':topic_model.predict(n.text)})
predictions=predictions.sample(frac=1,random_state=RANDOM_STATE)
n=n.merge(predictions,on='review_id',validate='one_to_one')
n['neg']=(n.p_neg>=.5).astype(int)
n['period']=np.where(n.date>=pd.Timestamp('2026-10-01'),'после','до')
by_shop=n.pivot_table(index='shop_id',columns='period',values='neg',aggfunc='mean')
by_shop['рост']=by_shop['после']-by_shop['до']
by_shop=by_shop.sort_values('рост',ascending=False)
worst_level=by_shop['после'].idxmax();worst_growth=by_shop['рост'].idxmax();focus_shop=worst_growth
n['week']=n.date.dt.to_period('W-SUN').dt.start_time
weekly=n.pivot_table(index='week',columns='shop_id',values='neg',aggfunc='mean')
weekly_counts=n.pivot_table(index='week',columns='shop_id',values='neg',aggfunc='size')
jump_week=weekly[focus_shop].diff().idxmax();change_date=jump_week
sept_max=round(weekly.loc[weekly.index<jump_week,focus_shop].max(),3)
print('Месяцы',by_shop.round(3).to_string(),'\\nУровень',worst_level,'рост',worst_growth)
print('Недельные доли',weekly.round(3).to_string())
print('Недельные n',weekly_counts.to_string())
print('Выбор',focus_shop,change_date,'max до границы',sept_max)
ax=weekly.plot(figsize=(10,4),marker='o');ax.set(title='Доля отзывов с сигналом жалобы по неделям',xlabel='Понедельник недели',ylabel='Доля отзывов');ax.axvline(change_date,color='black',linestyle='--');plt.tight_layout();plt.savefig('own-weekly.png');plt.show()
n['period']=np.where(n.date>=change_date,'после','до')
focus=n[n.shop_id==focus_shop]
assert focus.groupby('period').size().min()>=30
bad=n[n.neg==1]
def theme_table(frame):
    return pd.crosstab(frame.topic,frame.period,normalize='columns')
kzn=theme_table(bad[bad.shop_id==focus_shop]);others=theme_table(bad[bad.shop_id!=focus_shop])
cause=(kzn['после']-kzn['до']).idxmax()
q=bad[(bad.shop_id==focus_shop)&(bad.period=='после')&(bad.topic==cause)].sort_values('p_neg',ascending=False).head(5)
quotes=q.text.tolist();quote_ids=q.review_id.tolist()
print('Темы среди сигналов выбранной точки',kzn.round(3).to_string())
print('Остальные точки',others.round(3).to_string())
print('Цитаты',q[['review_id','date','shop_id','text','p_neg','topic','week']].to_string(index=False))
print('Цепочка одного отзыва',n.set_index('review_id').loc[quote_ids[0]].to_dict())
n.to_csv('own-scored.csv',index=False);by_shop.to_csv('own-monthly.csv');weekly.to_csv('own-weekly.csv');q.to_csv('own-quotes.csv',index=False)
''')
md('**Вывод по анализу.** Выбор точки сделан по максимальному приросту между календарными месяцами, граница — неделя максимального положительного шага этой точки. Темы ниже сравнивают только тексты с модельным сигналом; это другой знаменатель, чем все отзывы. Динамика и объёмы недель показаны, для операционного объяснения потребуется информация о работе смен и доставке.')
code('''observed=focus.groupby('period').neg.mean()
adj={key:round(float((p-fpr)/(tpr-fpr)),3) for key,p in observed.items()}
gold=pd.read_csv(DATA/'reviews_new_gold.csv')
g=n.merge(gold,on='review_id',validate='one_to_one',suffixes=('','_gold'))
assert g.label_source.eq('synthetic_kind_neg_or_mixed').all()
audit_rows=[]
for period,part in g[g.shop_id==focus_shop].groupby('period'):
    tn1,fp1,fn1,tp1=confusion_matrix(part.complaint,part.neg,labels=[0,1]).ravel()
    tp_rate=tp1/(tp1+fn1);fp_rate=fp1/(fp1+tn1);p=part.neg.mean()
    audit_rows.append(dict(period=period,n=len(part),complaints=int(part.complaint.sum()),tpr=tp_rate,fpr=fp_rate,observed=p,manual=part.complaint.mean(),adjusted=(p-fp_rate)/(tp_rate-fp_rate)))
audit=pd.DataFrame(audit_rows).set_index('period')
print('Доли всех отзывов выбранной точки',focus.groupby('period').neg.agg(['size','mean']).to_string())
print('Перенос старых TPR/FPR',adj)
print('Новые синтетические метки',audit.round(4).to_string())
print('3 октября при 1/5 октября:',pd.Timestamp('2026-10-03')>=pd.Timestamp('2026-10-01'),pd.Timestamp('2026-10-03')>=pd.Timestamp('2026-10-05'))
audit.to_csv('own-audit.csv')
letter=f"Управляющей сетью. Проверить {focus_shop} начиная с недели {change_date.date()}: доля отзывов с сигналом модели до/после выбранной даты {observed['до']:.1%}/{observed['после']:.1%}. Знаменатель — все отзывы этой точки в каждом периоде; граница включена в после. Наибольший прирост доли среди текстов с сигналом жалобы у темы {cause}. Это гипотеза для проверки операций, а не доказанная причина. Наибольший уровень октября у {worst_level}, максимальный прирост — {worst_growth}. Цитаты с исходными ID приведены ниже. Поправка по старым рейтинговым меткам даёт {adj}; её переносимость на жалобы не установлена. Синтетические контрольные метки не заменяют независимую человеческую разметку. Данные описывают отзывы, уникальных гостей и всех посетителей не считаем. Предлагаю проверить журнал доставки и смен, а также независимо разметить новые тексты обоих периодов."
letter+='\\n\\n'+'\\n'.join(f'{i}: {t}' for i,t in zip(quote_ids,quotes))
Path('own-letter.md').write_text(letter)
print(letter)
''')
md('## 5. Выводы и рекомендации\n\nПисьмо выше содержит выбранную точку, дату, масштабы и исходные цитаты. Проверьте операционные журналы; по этим данным причинного эффекта не установлено. Оценка поправки на тех же синтетически размеченных строках алгебраически совпадает с долей меток и не проверяет будущую неделю. Для переноса нужны независимая человеческая разметка обоих периодов, доверительные интервалы, проверка TPR/FPR и устойчивости к выбору границы. Рост одной и той же линейной поправки не является доказательством переносимости.')
nb['cells']=cells;(D/'project-template.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
