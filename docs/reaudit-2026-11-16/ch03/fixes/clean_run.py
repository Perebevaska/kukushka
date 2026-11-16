"""Чистый запуск в папке получателя. Сохранённая тетрадь не изменяется."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import sys

import nbformat
import pandas as pd
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[4]
folder = Path(sys.argv[1]).resolve()
data = root / 'site/data'
raw = pd.read_csv(data/'clients_raw.csv')
orders = pd.read_csv(data/'orders_3m.csv')
crm_files = ('clients_raw.csv','orders_3m.csv','shops.csv')
secret = {v.strip().casefold() for k in ('name','phone','client_id') for v in raw[k].dropna().astype(str)}
secret |= {re.sub(r'\D','',v)[-10:] for v in raw.phone.dropna() if len(re.sub(r'\D','',v)) in (10,11)}
pattern = re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(s) for s in sorted(secret,key=len,reverse=True) if s)+r')(?!\w)',re.I)

def privacy(nb):
    visible = '\n'.join(c.source+'\n'+json.dumps(c.get('outputs',[]),ensure_ascii=False) for c in nb.cells)
    return len(pattern.findall(visible))

saved = [nbformat.read(folder / file, as_version=4) for file in ('guests.ipynb','guests-selected-file.ipynb')]
assert all(privacy(book)==0 for book in saved)
differences = [(a.source,b.source) for a,b in zip(saved[0].cells,saved[1].cells) if a.source!=b.source]
assert len(saved[0].cells)==len(saved[1].cells) and len(differences)==1
left,right=differences[0]
assert left.replace('CLIENTS_FILE = "clients_raw.csv"','CLIENTS_FILE = "clients_selected.csv"')==right
selected_captions=' '.join(o.get('data',{}).get('text/markdown','') for c in saved[1].cells for o in c.get('outputs',[]))
assert '260 из 294 карт, 88.4%' in selected_captions and 'вход 309,' in selected_captions
print('Сохранённая альтернативная сдача: 309 строк, 260 из 294 карт, 88.4%, единственное отличие в коде — выбор файла')

for period in ('осень','новая CRM','excel'):
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        (project/'data').mkdir()
        for f in (('zerno_finance.xlsx',) if period == 'excel' else crm_files):
            shutil.copy(data/f,project/'data'/f)
        if period == 'excel':
            nb = nbformat.read(folder/'excel-completed.ipynb',as_version=4)
        else:
            nb = nbformat.read(folder/'guests.ipynb',as_version=4)
            assert privacy(nb)==0, 'Совпадение в передаваемом тексте или сохранённых выводах'
            changed=period=='новая CRM'
            if changed:
                extra=raw.iloc[[0]].copy()
                extra['client_id']='review-new-key'
                extra['signup_date']='2026-11-29'
                second=extra.assign(client_id='review-second-key')
                frame=pd.concat([raw,extra,extra,second],ignore_index=True)
                frame.to_csv(project/'data/next_period.csv',index=False)
                cell=next(c for c in nb.cells if c.cell_type=='code')
                assert 'CLIENTS_FILE = "clients_raw.csv"' in cell.source
                cell.source=cell.source.replace('CLIENTS_FILE = "clients_raw.csv"', 'CLIENTS_FILE = "next_period.csv"')
            n=295 if changed else 293
            total=310 if changed else 307
            # Числа справа вычислены независимо в recipient.py. Здесь проверяем пользовательские переменные.
            inspect=f'''assert len(raw)=={total} and len(clients)=={n} and n_orphans==0
assert summary['clients']=={n} and summary['median_age']==39
assert summary['active_pct']=={round(260/n*100,1)} and summary['avg_revenue_active']==1646.0
assert nov['active_pct']=={round(214/n*100,1)} and nov['avg_revenue_active']==705.5
assert guests.revenue.sum()==427950 and orders.amount.sum()==710195 and home_pct==85.1
assert len(pd.read_csv(PRIVATE / 'clients_clean.csv'))=={n}
assert set(log.values())=={{{total},{301 if changed else 299},{n}}}'''
            nb.cells.append(nbformat.v4.new_code_cell(inspect))
        result=NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(project)}}).execute()
        if period != 'excel':
            assert privacy(result)==0
            captions=' '.join(o.get('data',{}).get('text/markdown','') for c in result.cells for o in c.get('outputs',[]))
            assert f'260 из {n} карт, {round(260/n*100,1)}%' in captions
            assert f'вход {total}, полных копий удалено' in captions
            print('Динамическая подпись о выборе',f'260 из {n} карт, {round(260/n*100,1)}%')
            print('Ядро CRM',period,'строк',total,'карт',n,'совпадений приватных значений',privacy(result),'все сверки выполнены')
        else:
            from recipient import workbooks
            workbooks(project)
            print('Ядро Excel',len(nb.cells),'ячеек, сводка сверена по кодам и месяцам')
