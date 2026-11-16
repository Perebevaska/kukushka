"""Из корня курса: python recipient.py [папка студента]. Печатает только агрегаты."""
from contextlib import chdir, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / 'site/data'
NOTEBOOKS = ROOT / 'site/notebooks'
BASE = "6201fa939fbb25f8230f8d3d9e65f7bf5875c4e6"
FILES = ('clients_raw.csv', 'orders_3m.csv', 'shops.csv')
MONTHS = 'Янв Фев Мар Апр Май Июн Июл Авг Сен'.split()

def load_code(path):
    return [''.join(c['source']) for c in json.loads(path.read_text())['cells'] if c['cell_type']=='code']

def template():
    with TemporaryDirectory() as tmp, chdir(tmp):
        n = Path('notebooks')
        n.mkdir()
        d = Path('data')
        d.mkdir()
        (n / 'data').mkdir()
        shutil.copy(DATA / FILES[0], n / 'data' / FILES[0])
        for file in FILES:
            shutil.copy(DATA / file, d / file)
        raw = pd.read_csv(d / FILES[0])
        raw.iloc[:23].to_csv(d / 'crm_next.csv',index=False)
        with chdir(n):
            for name, expected in [(FILES[0],307),('crm_next.csv',23)]:
                ns = {}
                code = load_code(NOTEBOOKS / 'ch03-project-template.ipynb')
                code[0] = code[0].replace('CLIENTS_FILE = "clients_raw.csv"', 'CLIENTS_FILE = "'+name+'"')
                with redirect_stdout(StringIO()):
                    for cell in code:
                        exec(cell,ns)
                assert ns['DATA'] == Path('../data') and len(ns['raw'])==expected
                print('Шаблон, полная папка, анкеты', expected, 'заказы',len(ns['orders']),'кофейни',len(ns['shops']))

def subjects():
    raw=pd.read_csv(DATA/FILES[0]); orders=pd.read_csv(DATA/FILES[1]); shops=pd.read_csv(DATA/FILES[2])
    unique=raw.drop_duplicates(); norm=unique.assign(key=unique.client_id.str.upper().str.strip())
    clients=norm.sort_values('signup_date').groupby('key').tail(1)
    assert (len(raw),len(unique),len(clients))==(307,299,293)
    earliest=norm.groupby('key').signup_date.min()
    registered=pd.to_datetime(orders.client_id.str.strip().str.upper().map(earliest))
    earlier=orders[pd.to_datetime(orders.datetime).dt.normalize().lt(registered)]
    assert (len(earlier),earlier.client_id.nunique(),earlier.amount.sum())==(30,10,11168)
    print('До ранней даты анкеты: заказов / карт / ₽',len(earlier),earlier.client_id.nunique(),earlier.amount.sum())
    morning=pd.DataFrame({'part':pd.cut([8],bins=[0,12,17,24],labels=['утро','день','вечер'],right=False)})
    assert morning.groupby('part').size().tolist()==[1]
    assert morning.groupby('part',observed=False).size().tolist()==[1,0,0]
    print('Категории pandas по умолчанию / observed=False', [1], [1,0,0])
    money=pd.to_numeric(raw.bonus.str.replace(' ',''),errors='coerce')
    assert (money.count(),raw[money.notna()].client_id.str.strip().str.upper().nunique())==(286,273)
    print('Бонусы: строк, карт, среднее с пропусками и с нулём',money.count(),273,round(money.mean(),1),round(money.fillna(0).mean(),1))
    parsed=pd.to_datetime(raw.birth_date,format='%Y-%m-%d',errors='coerce').fillna(pd.to_datetime(raw.birth_date,format='%d.%m.%Y',errors='coerce'))
    years=parsed.dropna().map(lambda x: 2026-x.year-((x.month,x.day)>(12,1)))
    print('Возраст с заглушками / без',round(years.mean(),3),round(years[parsed.ne('1900-01-01')].mean(),3))
    city=clients.set_index('key').city.str.strip().str.lower().str.removeprefix('г.').str.strip().replace({'екб':'екатеринбург'}).str.capitalize()
    known=pd.DataFrame({'home':orders.client_id.map(city),'sale': orders.shop_id.map(shops.set_index('shop_id').city)}).dropna()
    print('Города: заказы / пары / совпали',len(orders),len(known),known.home.eq(known.sale).sum())
    wrong=pd.read_csv(DATA/'pos_december.csv')
    pos=pd.read_csv(DATA/'pos_december.csv',sep=';',decimal=',')
    assert str(wrong.index[0]).endswith(';187') and wrong.iloc[0,0]=='50;10%'
    print('POS: дробь разрезана запятой; час первой строки',pd.to_datetime(pos.time.iloc[0],format='%d.%m.%Y %H:%M').hour)
    for label,md in [('до',subprocess.check_output(['git','show',BASE+':content/ch03/08-pipeline.md'],cwd=ROOT,text=True)),('после',(ROOT/'content/ch03/08-pipeline.md').read_text())]:
        code=md.split('## Вся очистка анкет',1)[1].split('```python\n',1)[1].split('```',1)[0].split('clients = clean_clients')[0]
        ns={}
        exec(code,ns)
        print('Теория',label,'неизвестных ответов',ns['clean_gender'](pd.Series(['море','желаю пропустить'])).isna().sum(),
              'даты рождения',ns['parse_birth'](pd.Series(['1925-12-01','1925-12-02','1926-05-01'])).notna().tolist(),
              'анкет «карты»',ns['clean_clients'](raw).source.eq('карты').sum())
    for k,md in [('до',subprocess.check_output(['git','show',BASE+':content/ch03/test.md'],cwd=ROOT,text=True)),('после',(ROOT/'content/ch03/test.md').read_text())]:
        tasks=re.findall(r'^::: quiz [^\n]+\n(.*?)^:::$',md,re.S|re.M)
        maxima=[];minima=[];feedback=0
        for i,block in enumerate(tasks,1):
            opts=[(key=='x',len(' '.join(value.replace('`','').split()))) for key,value in re.findall(r'^- \[([ x])\] (.+)$',block,re.M)]
            assert len(opts)==4 and sum(key for key,num in opts)==1
            feedback+=len(re.findall(r'^  > ',block,re.M))
            counts=[n for _,n in opts]
            key=next(n for b,n in opts if b)
            if key==max(counts) and counts.count(key)==1: maxima.append(i)
            if key==min(counts) and counts.count(key)==1: minima.append(i)
        print('Тест',k,len(tasks),'пояснений',feedback,'длинные',maxima,'короткие',minima)
    for col in [orders, orders[orders.datetime.str.startswith('2026-11')]]:
        by=col.groupby('client_id').amount.sum()
        print('Карты, активные, доля, средняя по активным', len(clients),len(by),round(len(by)/len(clients)*100,1),round(by.mean(),1))
    amounts=orders.groupby(orders.client_id.notna()).amount.sum()
    print('Чеки с картой, без карты, все',amounts.loc[True],amounts.loc[False],amounts.sum())

def workbooks(folder):
    full={}
    for sheet in ['План','Факт']:
        rows=pd.read_excel(DATA/'zerno_finance.xlsx',sheet_name=sheet,header=None)
        header=rows[rows[0].eq('Код')].index.item()
        full[sheet]=pd.read_excel(DATA/'zerno_finance.xlsx',sheet_name=sheet,header=header).set_index('Код').drop('Итого')[MONTHS]
    book=pd.read_excel(folder/'plan_fact_report.xlsx',sheet_name=None)
    report=book['Выполнение'].set_index('Код')
    body=book['Факт без итога'].set_index('Код')
    pd.testing.assert_frame_equal(body.loc[:, MONTHS].sort_index(),full['Факт'].sort_index(),check_dtype=False)
    p,f=full['План'],full['Факт']
    done=(f.sum(axis=1).div(p.sum(axis=1)).mul(100)).where(f.count(axis=1).eq(9)&p.count(axis=1).eq(9)&p.sum(axis=1).gt(0)).round(1)
    pd.testing.assert_series_equal(report['выполнение, %'].dropna().sort_index(),done.dropna().sort_index(),check_names=False)
    amount_cols = ('план','факт') if len(report)==6 else ('сумма внесённого плана, тыс. ₽','сумма внесённого факта, тыс. ₽')
    for col,frame in zip(amount_cols,[p,f]):
        pd.testing.assert_series_equal(report[col].sort_index(),frame.sum(axis=1).round(1).reindex(report.index).sort_index(),check_names=False,atol=0.000001)
    if len(report)==7:
        for col,frame in [('месяцев плана',p),('месяцев факта',f)]:
            pd.testing.assert_series_equal(report[col].sort_index(),frame.count(axis=1).sort_index(),check_names=False,check_dtype=False)
    print('Сохранённая книга: листов, строк сводки, строк факта, процентов, Q1, январь–сентябрь',len(book),len(report),len(body),done.count(),round(f.iloc[:,:3].sum().sum(),1),round(f.sum().sum(),1))

if __name__=='__main__':
    print('Python',sys.version.split()[0],'pandas',pd.__version__)
    template()
    subjects()
    for folder in sys.argv[1:]:
        workbooks(Path(folder))
