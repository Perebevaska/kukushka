from acceptance_runner import Chapter

def replaced(source, before, after):
    assert before in source, f'Проба не изменила программу: нет {before!r}.'
    result = source.replace(before, after)
    assert result != source
    return result

with Chapter('ch08') as c:
    c.probe('04b-segments','report-text', 'report_metrics["pred_mean"],report_metrics["fact_rate"]=report_metrics["fact_rate"],report_metrics["pred_mean"]')
    c.probe('04b-segments','report-text', 'report_metrics["n"],report_metrics["deals"]=report_metrics["deals"],report_metrics["n"]')
    c.probe('07-final-project','fp-portrait', 'rest["city"]="Неверный город"')
    source=c.tasks['07-final-project','fp-money']['solution']
    c.probe('07-final-project','fp-money', code=replaced(source, 'best_t = supported.loc[supported["margin"].idxmax(), "threshold"]', 'best_t = 0.10'),expected=True)
    source=c.tasks['07-final-project','fp-honest']['solution']
    c.probe('07-final-project','fp-honest', code=replaced(source, 'best_t = 0.08', 'best_t = 0.10'),expected=True)
    source=c.tasks['07-final-project','fp-portrait']['solution']
    c.probe('07-final-project','fp-portrait', code=replaced(source, 'best_t = 0.08', 'best_t = 0.10'),expected=True)
    c.probe('06-project','decision',expected=True)
    source=c.tasks['06-project','decision']['solution']
    c.probe('06-project','decision',code=source.replace('ok["mean"].idxmax()', 'risk["mean"].idxmax()'))
    c.probe('06-project','decision',code=source.replace('<= 0.025', '< 0.025'))
    c.probe('06-project','decision',code=source.replace('passed = list(ok.index)', 'passed = sorted(ok.index)'))
    c.probe('06-project','decision',code=source+'\ncost_of_safety=0')
    c.probe('06-project','decision',code=source+'\ncost_of_safety=round(cost_of_safety) if cost_of_safety is not None else None')
    c.probe('06-project','decision',code=source.replace(' if len(ok) else None', ''))
    c.probe('06-project','decision',code=source.replace('if choice is not None else None', 'if choice is not None else 0'))
    alternative='''
# Preserve all setup columns and use numpy/pandas supplied by setup.
frame=pd.DataFrame(risk).loc[:,["mean","low","high","p_loss"]]
passed=frame.index[np.asarray(frame.p_loss)<=.025].tolist()
ranked=frame.loc[passed].sort_values("mean",ascending=False)
choice=ranked.index[0] if len(ranked) else None
cost_of_safety=np.max(frame["mean"])-ranked.iloc[0]["mean"] if len(ranked) else None
'''
    c.probe('06-project','decision',code=alternative,expected=True)
    loop='''
passed=[]
choice=None
cost_of_safety=None
best=-np.inf
for city,row in risk.iterrows():
    if row.p_loss<=.025:
        passed.append(city)
        if row["mean"]>best:
            choice=city
            best=row["mean"]
if choice is not None:
    cost_of_safety=risk["mean"].max()-best
'''
    c.probe('06-project','decision',code=loop,expected=True)

    c.probe('02-budget','gains-plot',expected=True)
    source=c.tasks['02-budget','gains-plot']['solution']
    c.probe('02-budget','gains-plot',code=source.replace('ax.plot(share, caught, label="модель")', 'ax.plot(np.r_[0,share],np.r_[0,caught],label="модель")'),expected=True)
    swapped=source.replace('ax.plot(share, caught, label="модель")\nax.plot([0, 1], [0, 1], "--", color="grey", label="случайно")', 'ax.plot(np.linspace(0,1,7),np.linspace(0,1,7),"--")\nax.plot(share,caught)')
    c.probe('02-budget','gains-plot',code=swapped,expected=True)
    c.probe('02-budget','gains-plot',code=source.replace('ax.plot(share, caught, label="модель")', 'ax.step(share,caught,where="post")'),expected=True)
    c.probe('02-budget','gains-plot',code=source.replace('ax.plot(share, caught, label="модель")', 'ax.plot(share[::-1],caught[::-1])'),expected=True)
    c.probe('02-budget','gains-plot','ax.lines[0].set_ydata(np.full(600,caught[59]))')
    c.probe('02-budget','gains-plot','wrong=caught.copy()\nwrong[100]=.8\nax.lines[0].set_ydata(wrong)')
    c.probe('02-budget','gains-plot','ax.lines[0].set_xdata(np.arange(600)/600)')
    c.probe('02-budget','gains-plot','ax.lines[1].set_ydata([0,.8])')
    c.probe('02-budget','gains-plot',code=source.replace('ax.plot([0, 1], [0, 1], "--", color="grey", label="случайно")', 'ax.plot([0,.5,1],[0,.8,1])'))
    c.probe('02-budget','gains-plot','ax.lines[1].set_visible(False)')
    c.probe('02-budget','gains-plot','ax.lines[0].set_alpha(0)')
    c.probe('02-budget','gains-plot','at10=.1')
    c.probe('02-budget','gains-plot',code=source.replace('ax.plot(share, caught, label="модель")', 'idx=np.random.default_rng(2).permutation(600)\nax.plot(share[idx],caught[idx])'))
    diagonal_line='ax.plot([0, 1], [0, 1], "--", color="grey", label="случайно")'
    c.probe('02-budget','gains-plot',code=source.replace(diagonal_line,'ax.axline((0,0),slope=1)'),expected=True)
    c.probe('02-budget','gains-plot',code=source.replace(diagonal_line,'ax.axline((0,.2),slope=1)'))
    c.probe('02-budget','gains-plot',code=source.replace(diagonal_line,'ax.axline((0,.4),slope=0)'))
    c.probe('02-budget','gains-plot','ax.set(xlim=(2,3),ylim=(2,3))')
    c.probe('02-budget','gains-plot','ax.set_xlim(.2,1)')
