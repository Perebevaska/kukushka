from acceptance_runner import Chapter
with Chapter('ch09') as c:
    item=c.tasks['05-project','hidden-quality']
    starter=item['starter']+'\nr2_hidden=round(r2_base,4)\nsame=True'
    c.probe('05-project','hidden-quality',code=starter)
    c.probe('05-project','weights','max_diff=-100')
    c.probe('02b-vectorize','vectorize','pay_vec=pay_loop\nt_loop,t_vec,speedup=.4,.1,4')
    c.probe('02b-vectorize','best-of',expected=True)
    item=c.tasks['02b-vectorize','best-of']
    bad=item['solution'].replace('return min(times)','return 0.0')
    c.probe('02b-vectorize','best-of',code=bad)

    c.probe('03-normal-equation','many-solutions',expected=True)
    source=c.tasks['03-normal-equation','many-solutions']['solution']
    c.probe('03-normal-equation','many-solutions',code=source.replace('np.linalg.lstsq(full, y, rcond=None)[0]', 'np.linalg.pinv(full) @ y'),expected=True)
    shifted=source.replace('w_b = w_a.copy()', 'w_a += np.array([37.,0.,-37.,-37.,-37.])\nw_b = w_a.copy()')
    c.probe('03-normal-equation','many-solutions',code=shifted,expected=True)
    reduced=source.replace('w_a = np.linalg.lstsq(full, y, rcond=None)[0]', 'reduced=np.linalg.lstsq(full[:,:-1],y,rcond=None)[0]\nw_a=np.r_[reduced,0.]')
    c.probe('03-normal-equation','many-solutions',code=reduced,expected=True)
    c.probe('03-normal-equation','many-solutions',code=source.replace('np.linalg.lstsq(full, y, rcond=None)[0]', 'np.zeros(5)'))
    c.probe('03-normal-equation','many-solutions',code=source.replace('np.linalg.lstsq(full, y, rcond=None)[0]', 'np.array([5.,2.,1.,3.,4.])'))
    c.probe('03-normal-equation','many-solutions',code=source.replace('w_a = np.linalg.lstsq(full, y, rcond=None)[0]', 'full=np.zeros_like(full)\ny=np.zeros_like(y)\nw_a=np.zeros(5)'))
    c.probe('03-normal-equation','many-solutions','max_diff=-1e-12')
    c.probe('03-normal-equation','many-solutions','max_diff=1e-8')
    c.probe('03-normal-equation','many-solutions','max_diff=float("nan")')
    c.probe('03-normal-equation','many-solutions','max_diff=float("inf")')
    c.probe('03-normal-equation','many-solutions','weights_differ=-10')
    c.probe('03-normal-equation','many-solutions','weights_differ=9.9')
    c.probe('03-normal-equation','many-solutions','weights_differ=float("nan")')
    c.probe('03-normal-equation','many-solutions','weights_differ=float("inf")')
    c.probe('03-normal-equation','many-solutions','w_a[0]=float("nan")')
    c.probe('03-normal-equation','many-solutions','w_b[0]=float("inf")')
    c.probe('03-normal-equation','many-solutions',code=source.replace('w_b[0] += 10','w_b[0] += 20').replace('w_b[2:] -= 10','w_b[2:] -= 20'))
    c.probe('03-normal-equation','many-solutions',code=source.replace('w_b[1]', 'w_b[0]')+'\nw_b[1]+=1\nmax_diff=0\nweights_differ=10')
    c.probe('03-normal-equation','many-solutions',code=source.replace('w_b = w_a.copy()', 'w_a[1]+=1\nw_b=w_a.copy()')+'\nmax_diff=0\nweights_differ=10')
    replaced_csv=source.replace('d = pd.read_csv("deliveries.csv")', 'd = pd.read_csv("deliveries.csv")\nd["actual_min"]=25\nd.to_csv("deliveries.csv",index=False)')
    c.probe('03-normal-equation','many-solutions',code=replaced_csv)
