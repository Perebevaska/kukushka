from acceptance_runner import Chapter
with Chapter('ch13') as c:
    c.probe('05-project','score', "n=n.sample(frac=1,random_state=3)",expected=True)
    c.probe('05-project','score', "n.loc[n.shop_id=='KZN-2','shop_id']='TMN-1'")
    c.probe('05-project','weekly', "weekly.index=weekly.index+pd.Timedelta(days=7)")
    c.probe('05-project','why','quotes[0]="Цитата из другого источника"')
    c.probe('05-project','adjust',expected=True)
    c.probe('03-classify','recall95',expected=True)
