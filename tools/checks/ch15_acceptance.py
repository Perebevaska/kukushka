from acceptance_runner import Chapter,ROOT
with Chapter('ch15') as c:
    source=c.tasks['06-final-project','target']['solution']
    closure='''
def make_bound(frame):
    def target(cutoff,months=3):
        c=pd.Timestamp(cutoff)
        a=frame[(frame.start_date<=c)&(frame.end_date.isna()|(frame.end_date>c))]
        if c+pd.offsets.MonthEnd(months)>pd.Timestamp('2026-09-30'):
            return pd.Series(pd.NA,index=a.client_id.values,dtype='Int64')
        return pd.Series((a.end_date.notna()&(a.end_date<=c+pd.offsets.MonthEnd(months))).astype(int).values,index=a.client_id.values)
    return target
build_target=make_bound(base)
'''
    c.probe('06-final-project','target',code=source+closure,expected=True)
    module='\nimport sys\nsys.path.insert(0,'+repr(str(ROOT/'docs/audit-2026-11-13/ch15/student-project'))+')\nfrom src.features import build_target\n'
    c.probe('06-final-project','target',code=source+module,expected=True)
    c.probe('06-final-project','target',code=source.replace('pd.Series(pd.NA,index=active', 'pd.Series(0,index=active'))
    source=c.tasks['06-final-project','profit']['solution']
    c.probe('06-final-project','profit',code=source.replace('index[:150]','index[:10]',1),expected=True)
    import pandas as pd
    import shutil
    item=c.tasks['06-final-project','models']
    for filename in item['files']:shutil.copy(ROOT/'site/data'/filename,filename)
    ns={};exec(item['setup'],ns)
    cut=pd.Timestamp('2026-06-30')
    client=ns['active_at'](cut).sort_values('start_date').client_id.iloc[0]
    template=ns['orders'].iloc[:2].copy()
    template['client_id']=client;template['status']='доставлен';template['late_min']=0
    template['order_date']=[cut-pd.Timedelta(days=30),cut-pd.Timedelta(days=120)]
    for recent,previous in [(100,50),(-20,0),(0,0),(-1,0)]:
        orders=template.copy();orders['amount']=[recent,previous];ns['orders']=orders
        actual=ns['build_features'](cut).loc[client,'revenue_trend']
        expected=(recent-previous)/(recent+previous+1) if recent+previous+1 else 0
        assert abs(actual-expected)<1e-12,(recent,previous,actual)
        print('OK revenue_trend',recent,previous,actual)
