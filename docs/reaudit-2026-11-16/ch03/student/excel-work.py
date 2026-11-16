from pathlib import Path
import pandas as pd
import json
DATA=Path('/private/tmp/kuch03round/student/data')
OUT=Path('/Users/dmitriikormin/Documents/Projects/ds-course/docs/reaudit-2026-11-16/ch03/student')
BOOK=DATA/'zerno_finance.xlsx'
MONTHS=['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен']
def header_row(sheet):
    first=pd.read_excel(BOOK,sheet_name=sheet,header=None,usecols=[0]).iloc[:,0]
    positions=first.index[first.eq('Код')]
    assert len(positions)==1
    return int(positions[0])
plan=pd.read_excel(BOOK,sheet_name='План',skiprows=header_row('План'))
fact=pd.read_excel(BOOK,sheet_name='Факт',skiprows=header_row('Факт'),usecols='A,D:L')
# Мои решения трёх упражнений.
fact_h=pd.read_excel(BOOK,sheet_name='Факт',header=header_row('Факт'),usecols='A,D:L')
sheets=list(pd.read_excel(BOOK,sheet_name=None))
body=fact[fact['Код']!='Итого']
pbody=plan[plan['Код']!='Итого']
monthly_done=body[MONTHS].sum()/pbody[MONTHS].sum()*100
weak=monthly_done[monthly_done<97].index.tolist()
assert fact_h.equals(fact)
p=pbody.set_index('Код')[MONTHS].sum(axis=1)
f=body.set_index('Код')[MONTHS].sum(axis=1)
report=pd.DataFrame({'план':p,'факт':f,'выполнение, %':(f/p*100).round(1)})[p>0]
with pd.ExcelWriter(OUT/'plan_fact_report.xlsx') as writer:
    report.to_excel(writer,sheet_name='Выполнение')
    body.to_excel(writer,sheet_name='Факт без итога',index=False)
back=pd.read_excel(OUT/'plan_fact_report.xlsx',sheet_name=None)
pd.testing.assert_frame_equal(back['Выполнение'].set_index('Код'),report,check_dtype=False)
pd.testing.assert_frame_equal(back['Факт без итога'],body.reset_index(drop=True),check_dtype=False)
q1=round(body[MONTHS[:3]].sum().sum(),1)
q1_check=round(fact.loc[fact['Код']=='Итого',MONTHS[:3]].sum().sum(),1)
assert q1==q1_check
result={'sheets':sheets,'fact_h_equals_fact':fact_h.equals(fact),'weak':weak,'monthly_done_pct':monthly_done.round(3).to_dict(),'q1':q1,'q1_check':q1_check,'nine_months_fact':round(f.sum(),1),'report_sheets':list(back),'report_reread_equal':True,'worst':report['выполнение, %'].idxmin(),'rows_plan_before':len(plan),'rows_plan_after':len(pbody),'rows_fact_before':len(fact),'rows_fact_after':len(body),'heads':{s:header_row(s) for s in ['План','Факт']}}
(OUT/'excel-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
