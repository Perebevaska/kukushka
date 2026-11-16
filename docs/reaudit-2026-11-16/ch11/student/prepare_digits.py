import json
from pathlib import Path
D=Path(__file__).parent
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s))
def code(s):cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None))
md('# Самостоятельный проект: очередь проверки рукописных цифр\n\n## 1. Цель\nПроверить, сколько ошибок отдельных цифр оставляет автоматизация после очереди из37цифр. Выбираю модель по validation, правило confidence фиксирую до меток финальной партии. Критерий: качество цифр выше простого ориентира и измеренное число пропущенных ошибок. Прогноз целых телефонов из этих данных не оценивается.')
code('''import sys,json,time,joblib
from pathlib import Path
import numpy as np,pandas as pd,matplotlib,matplotlib.pyplot as plt,sklearn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score,confusion_matrix
from scipy.ndimage import gaussian_filter
RANDOM_STATE=42
ART=Path('digits_transfer');ART.mkdir(exist_ok=True)
print('Python',sys.version.split()[0],'numpy',np.__version__,'sklearn',sklearn.__version__)
''')
md('## 2. Данные\nSklearn digits: одна строка — отдельный символ8×8,64яркости0..16,1797строк. Это учебный набор; нет связи с анкетой, номера телефона и результатов оператора.')
code('''digits=load_digits();X=digits.data/16.;y=digits.target
print(X.shape,'missing',np.isnan(X).sum(),'range',X.min(),X.max())
print('counts',np.bincount(y))
fig,axes=plt.subplots(1,10,figsize=(12,2))
for k,ax in enumerate(axes):
    ax.imshow(digits.images[y==k].mean(axis=0),cmap='gray_r');ax.set_title(str(k));ax.axis('off')
fig.suptitle('Средняя яркость по классу');plt.show()
''')
md('**Вывод по данным.**1797символов и64признака, классы имеют около180примеров. Средние формы подходят для первичного осмотра, но индивидуальный почерк и шум на сканах здесь не представлены.')
md('## 3. Предобработка\nДелю яркость на16 по известной шкале; статистики теста не нужны. Финальные25% откладываю до выбора модели и правила; в development ещё25%validation. Дубли автоматически не удаляю: одинаковая картинка может быть отдельным наблюдением; явно отчитаюсь об их числе.')
code('''print('duplicate pixel rows',len(X)-len(np.unique(X,axis=0)))
ix=np.arange(len(y));dev_idx,final_idx=train_test_split(ix,test_size=.25,random_state=RANDOM_STATE,stratify=y)
fit_idx,val_idx=train_test_split(dev_idx,test_size=.25,random_state=7,stratify=y[dev_idx])
print('fit,val,final',len(fit_idx),len(val_idx),len(final_idx))
''')
md('**Вывод по предобработке.**Обучение1010,валидация337,финал450. Общая подготовка — заданная шкала0..1; финальные метки до фиксации выбора не участвуют в сравнении.')
md('## 4. Анализ и модели\nСравниваю Dummy,логит,kNN3,MLP64. Основная метрикаaccuracy на validation. Затем фиксирую выбранный рецепт и ruleconfidence с tie-break по позиции. Дополнительно проверяю новое размытие; правило очереди тоже сохраняется до доступа к финальным меткам.')
code('''recipes={'dummy':lambda:DummyClassifier(strategy='most_frequent'),'logit':lambda:LogisticRegression(max_iter=2000),'knn3':lambda:KNeighborsClassifier(n_neighbors=3),'mlp64':lambda:MLPClassifier(hidden_layer_sizes=(64,),alpha=.001,max_iter=500,random_state=RANDOM_STATE)}
rows=[]
for name,recipe in recipes.items():
    candidate=recipe().fit(X[fit_idx],y[fit_idx]);rows.append({'model':name,'validation_accuracy':candidate.score(X[val_idx],y[val_idx])})
log=pd.DataFrame(rows);best_name=str(log.sort_values(['validation_accuracy','model'],ascending=[False,True]).iloc[0]['model'])
print(log.to_string(index=False));print('frozen model',best_name)
selected=recipes[best_name]().fit(X[dev_idx],y[dev_idx])
def blur(batch):
    return np.array([gaussian_filter(im.reshape(8,8),sigma=.65,mode='constant',cval=0) for im in batch]).reshape(-1,64)
request=X[final_idx];blurred=blur(request);P=selected.predict_proba(blurred);pred=selected.classes_[P.argmax(axis=1)];confidence=P.max(axis=1)
queue=np.lexsort((np.arange(len(request)),confidence))[:37].tolist()
manifest={'model':best_name,'rule':'confidence','tie_break':'smaller_position','capacity_digits':37,'queue':queue,'unit':'digit','sigma':.65,'border':'constant0','reason':'Низкая максимальная вероятность даёт понятное правило без доступа к меткам. Уверенные ошибки этим правилом не гарантируется поймать.'}
(ART/'decision_before_labels.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
joblib.dump(selected,ART/'digits_model.joblib');np.save(ART/'control_features.npy',request[:16]);np.save(ART/'control_proba.npy',selected.predict_proba(request[:16]))
print('SAVED before opening final labels',manifest)
''')
code('''# Открываю final labels только после записанногоmanifest.
final_labels=y[final_idx];wrong=pred!=final_labels;inside=np.zeros(len(wrong),dtype=bool);inside[queue]=True
clean_acc=selected.score(request,final_labels);blur_acc=accuracy_score(final_labels,pred)
metrics={'model':best_name,'clean_accuracy':float(clean_acc),'blur_accuracy':float(blur_acc),'total_errors':int(wrong.sum()),'caught_errors':int((wrong&inside).sum()),'missed_errors':int((wrong&~inside).sum()),'review_share':len(queue)/len(request),'phone_accuracy':None}
print(metrics)
pd.DataFrame({'position':np.arange(len(request)),'original_index':final_idx,'truth':final_labels,'prediction':pred,'confidence':confidence,'review':inside}).to_csv(ART/'evaluation.csv',index=False)
(ART/'metrics.json').write_text(json.dumps(metrics,indent=2));log.to_csv(ART/'validation.csv',index=False)
cm=confusion_matrix(final_labels,pred)
fig,ax=plt.subplots(figsize=(5,4));im=ax.imshow(cm);ax.set_xlabel('Прогноз');ax.set_ylabel('Истина');ax.set_title('Ошибки на размытой финальной партии');plt.colorbar(im,ax=ax);plt.show()
restored=joblib.load(ART/'digits_model.joblib');np.testing.assert_allclose(restored.predict_proba(np.load(ART/'control_features.npy')),np.load(ART/'control_proba.npy'))
print('Restored model:16control predictions match')
''')
md('**Вывод по анализу.**Фактическиеaccuracy и числа очереди в предыдущем output иmetrics.json. Сравнение на validation определило рецепт до финальных меток. Очередь имеет37цифр; ошибку после размытия нельзя выводить из качества чистых картинок.')
md('## 5. Выводы и рекомендации\nСамостоятельный результат передаётся как модель,контрольныепрогнозы,решение до меток,таблица ошибок. Не предлагаю записывать телефоны автоматически: нужны реальные анкеты, сегментация, связьцифр сзаписью ипорядок,эталонполнойстрокой(включая начальные нули),результат оператора и нагрузка по карточкам. Для восьмизначного кода считаю среднее точного совпадения всех8символов, без предположения независимости. Качество цифр наdigits не доказывает экономию времени оператора.')
(D/'digits-project.ipynb').write_text(json.dumps(dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}},nbformat=4,nbformat_minor=5),ensure_ascii=False,indent=1))
