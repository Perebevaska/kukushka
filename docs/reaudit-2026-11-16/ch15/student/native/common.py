# Own assembly of the public training header used in lessons01/03.
import hashlib
import pandas as pd
from sklearn.model_selection import train_test_split,StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline,make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
g=pd.read_csv('guests_churn.csv');X=g.drop(columns=['guest_id','churned','card_blocked'])
X_train,X_test,y_train,y_test=train_test_split(X,g.churned,test_size=.25,random_state=42,stratify=g.churned)
NUM=['tenure_months','app','visits_90d','days_since_last','avg_check','delivery_share','promo_used','complaints'];CAT=['city','fav_category']
CV=StratifiedKFold(5,shuffle=True,random_state=0)
DATA_MD5=hashlib.md5(open('guests_churn.csv','rb').read()).hexdigest()
def make(est):
 pre=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median'),StandardScaler()),NUM),('cat',OneHotEncoder(handle_unknown='ignore'),CAT)])
 return Pipeline([('prep',pre),('model',est)])
