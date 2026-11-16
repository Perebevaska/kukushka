from acceptance_runner import Chapter
import pandas as pd

with Chapter('ch04') as chapter:
    chapter.probe('07-readable','title','ax.patches[1].set_height(0)')
    chapter.probe('07-readable','title','ax.patches[-1].remove()')
    chapter.probe('07-readable','title','ax.clear()\nax.bar(m.index[::-1], m.values[::-1])\nax.set_ylabel("минут")\nax.set_title(f"{m.index[0]} — самые медленные: медиана {int(m.iloc[0])} мин")', expected=True)
    chapter.probe('09-project','clean','ok["delay"] = -ok["delay"]')
    chapter.probe('09-project','scale','ax.clear()\nax.hist(-ok["delay"],bins=16,range=(-40,40))\nax.axvline(0)')
    chapter.probe('09-project','report', expected=True)
    def branch_with_late_cars():
        deliveries = pd.read_csv('deliveries.csv')
        deliveries['courier'] = deliveries['courier'].replace({'пеший': 'авто', 'авто': 'пеший'})
        deliveries.to_csv('deliveries.csv', index=False)

    chapter.probe('09-project', 'walkers', prepare=branch_with_late_cars, expected=True)
    walkers = chapter.tasks['09-project', 'walkers']['solution']
    fixed_group = walkers.replace('group = ok.groupby("courier", sort=True)["late"].mean().idxmax()', 'group = "пеший"')
    assert fixed_group != walkers
    chapter.probe('09-project', 'walkers', prepare=branch_with_late_cars, code=fixed_group)
    def zero_day():
        raw=pd.read_csv('preorders.csv')
        raw[raw.date != '2026-01-07'].to_csv('preorders.csv',index=False)
    chapter.probe('05c-dau-mau','sticky',prepare=zero_day,expected=True)
    chapter.probe('05c-dau-mau','wau-full',prepare=zero_day,expected=True)
    source=chapter.tasks['05c-dau-mau','wau-full']['solution']
    wrong=source.replace('"days": days', '"days": g["date"].nunique()')
    chapter.probe('05c-dau-mau','wau-full',code=wrong,prepare=zero_day)

    # Early chart cards: verify the drawn values and visible axis order.
    chapter.probe('01-plots','bar-shop',expected=True)
    chapter.probe('01-plots','bar-shop','ax.set_xticks(ax.get_xticks(),counts.index[::-1])')
    chapter.probe('01-plots','bar-shop','ax.clear()\nax.bar(counts.index[::-1],counts.values[::-1])\nax.invert_xaxis()\nax.set_ylabel("заказов")',expected=True)
    chapter.probe('01-plots','bar-shop','ax.clear()\nax.bar(counts.index[::-1],counts.values[::-1])\nax.set_ylabel("заказов")')

    chapter.probe('01-plots','barh',expected=True)
    chapter.probe('01-plots','barh','ax.clear()\ns=counts.sort_values(ascending=False)\nax.barh(s.index,s.values)\nax.invert_yaxis()\nax.set_title("Заказы по напиткам")',expected=True)
    # The brief only requires the maximum at the top, not all other bars sorted.
    chapter.probe('01-plots','barh','ax.clear()\norder=[counts.idxmax()]+[name for name in counts.index if name!=counts.idxmax()]\ns=counts.reindex(order)\nax.barh(s.index,s.values)\nax.invert_yaxis()\nax.set_title("Заказы по напиткам")',expected=True)
    chapter.probe('01-plots','barh','ax.clear()\ns=counts.sort_values(ascending=False)\nax.barh(s.index,s.values)\nax.set_title("Заказы по напиткам")')
    chapter.probe('01-plots','barh','ax.set_yticks(ax.get_yticks(),counts.index[::-1])')

    chapter.probe('01-plots','pandas-plot',expected=True)
    source=chapter.tasks['01-plots','pandas-plot']['solution']
    accessor=source.replace('by_size.plot(kind="bar",','by_size.plot.bar(')
    chapter.probe('01-plots','pandas-plot',code=accessor,expected=True)
    chapter.probe('01-plots','pandas-plot',code=accessor.replace('by_size.plot.bar(', 'by_size.iloc[::-1].plot.bar(')+'\nax.invert_xaxis()',expected=True)
    chapter.probe('01-plots','pandas-plot','ax.set_xticks(ax.get_xticks(),["L","M","S"])')

    chapter.probe('02-histograms','hist-km',expected=True)
    source=chapter.tasks['02-histograms','hist-km']['solution']
    chapter.probe('02-histograms','hist-km',code=source.replace('d["distance_km"]','d["amount"]'))
    chapter.probe('02-histograms','hist-km',code=source.replace('bins=30','bins=30, range=(0,float(d["distance_km"].max())+1)'),expected=True)
    chapter.probe('02-histograms','hist-km','ax.patches[0].set_height(ax.patches[0].get_height()+1)')
    chapter.probe('02-histograms','hist-km','for patch in ax.patches:\n    patch.set_x(patch.get_x()+1000)')

    chapter.probe('06-correlation','scatter',expected=True)
    chapter.probe('06-correlation','scatter','ax.collections[0].set_offsets(ax.collections[0].get_offsets()[::-1])',expected=True)
    chapter.probe('06-correlation','scatter','ax.collections[0].set_offsets(ax.collections[0].get_offsets()[:,::-1])')
    chapter.probe('06-correlation','scatter','points=ax.collections[0].get_offsets().copy()\npoints[:,1]=points[::-1,1]\nax.collections[0].set_offsets(points)')
    chapter.probe('06-correlation','scatter','ax.collections[0].set_sizes([20])')
    chapter.probe('06-correlation','scatter','ax.clear()\nfor part in (ok.iloc[::2],ok.iloc[1::2]):\n    ax.scatter(part.distance_km,part.actual_min,s=8,alpha=.4)\nax.set_xlabel("км")\nax.set_ylabel("мин")',expected=True)

    chapter.probe('07-readable','percent-axis',expected=True)
    chapter.probe('07-readable','percent-axis','ax.clear()\ns=shares.sort_values(ascending=False)\nax.barh(s.index,s.values)\nax.invert_yaxis()\nax.set_xlim(0,100)\nax.set_xlabel("доля заказов, %")',expected=True)
    chapter.probe('07-readable','percent-axis','ax.clear()\norder=[shares.idxmax()]+list(shares.drop(shares.idxmax()).sort_values().index)\ns=shares.reindex(order)\nax.barh(s.index,s.values)\nax.invert_yaxis()\nax.set_xlim(0,100)\nax.set_xlabel("доля заказов, %")',expected=True)
    chapter.probe('07-readable','percent-axis','for patch in ax.patches:\n    patch.set_width(patch.get_width()/100)')
    chapter.probe('07-readable','percent-axis','ax.set_yticks(ax.get_yticks(),s.index[::-1])')
    chapter.probe('07-readable','percent-axis','ax.invert_yaxis()')

    # Additional styles and the boundaries of each stated requirement.
    chapter.probe('01-plots','bar-shop','for patch in ax.patches:\n    patch.set_y(50)')
    chapter.probe('07-readable','percent-axis','for patch in ax.patches:\n    patch.set_x(20)')
    source=chapter.tasks['01-plots','pandas-plot']['solution']
    fake=source.replace('by_size.plot(kind="bar", ax=ax, title="Выручка по размерам", rot=0)', 'ax.bar(by_size.index,by_size.values)\nax.plot([],[])\nax.set_title("Выручка по размерам")')
    chapter.probe('01-plots','pandas-plot',code=fake)
    inline=source.replace('by_size.plot(kind="bar",', 'df.groupby("size")["amount"].sum().reindex(["S","M","L"]).plot(kind="bar",')
    chapter.probe('01-plots','pandas-plot',code=inline,expected=True)
    source=chapter.tasks['02-histograms','hist-km']['solution']
    for options in ['histtype="step"','histtype="stepfilled"','rwidth=.7','range=(0,20)','align="left"','align="right"']:
        chapter.probe('02-histograms','hist-km',code=source.replace('bins=30','bins=30, '+options),expected=True)
    stairs=source.replace('ax.hist(d["distance_km"], bins=30)', 'import numpy as np\ncounts,edges=np.histogram(d["distance_km"],bins=30)\nax.stairs(counts,edges)')
    chapter.probe('02-histograms','hist-km',code=stairs,expected=True)
    source=chapter.tasks['01-plots','pandas-plot']['solution']
    helper=source.replace('by_size.plot(kind="bar", ax=ax, title="Выручка по размерам", rot=0)', 'def draw(series):\n    return series.plot.bar(ax=ax,title="Выручка по размерам")\ndraw(by_size)')
    chapter.probe('01-plots','pandas-plot',code=helper,expected=True)
    chained=source.replace('by_size.plot(kind="bar",','by_size.nlargest(3).loc[["S","M","L"]].plot(kind="bar",')
    chapter.probe('01-plots','pandas-plot',code=chained,expected=True)
