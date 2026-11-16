"""Из корня репозитория: оценка двух знаменателей по исходным файлам проекта."""
from pathlib import Path
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
p=Path(__file__).resolve().parents[3]/'site/data'
r=pd.read_csv(p/'reviews_text.csv')
n=pd.read_csv(p/'reviews_new.csv')
def model(y):
    return make_pipeline(TfidfVectorizer(ngram_range=(1,2)),LogisticRegression(max_iter=1000)).fit(r.text,y)
n['pred_neg']=model(r.rating<=3).predict_proba(n.text)[:,1]>=.5
n['pred_topic']=model(r.topic).predict(n.text)
n['kzn']=n.shop_id.eq('KZN-2');n['after']=n.date.ge('2026-10-05')
n['delivery_neg']=n.pred_neg & n.pred_topic.eq('доставка')
n['seen_exact']=n.text.isin(r.text)
stats=n.groupby(['kzn','after']).agg(n=('review_id','size'),negative=('pred_neg','sum'),delivery_negative=('delivery_neg','sum'),seen_exact=('seen_exact','sum'))
print(stats.assign(share_all=stats.delivery_negative/stats.n, share_negative=stats.delivery_negative/stats.negative).to_string())
print('Разных текстов в обучении и в новой партии:',r.text.nunique(),n.text.nunique())
