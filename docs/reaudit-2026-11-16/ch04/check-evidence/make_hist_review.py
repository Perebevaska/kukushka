"""New histogram representations and geometry errors, expected verdicts fixed before run."""
import json
from pathlib import Path
D=Path(__file__).parent
review=json.loads((D/'review-programs.json').read_text())
P=[]
def add(basis,name,change,expected):
 x=next(p for p in review if p['case']==basis)
 P.append(dict(x,case=name,code=change(x['code']),expected=expected))
five='alternative-explicit-edges';compare='alternative-reverse-group-order'
add(five,'five-min-stepfilled',lambda c:c.replace('bins=range','histtype="stepfilled", bins=range'),True)
add(five,'five-min-stairs',lambda c:c.replace('ax.hist(t, bins=range(0,121,5))','import numpy as np\ncounts,edges=np.histogram(t,bins=range(0,121,5))\nax.stairs(counts,edges)'),True)
add(five,'five-min-stairs-filled',lambda c:c.replace('ax.hist(t, bins=range(0,121,5))','import numpy as np\ncounts,edges=np.histogram(t,bins=range(0,121,5))\nax.stairs(counts,edges,fill=True)'),True)
add(five,'five-min-wrong-horizontal-stairs',lambda c:c.replace('ax.hist(t, bins=range(0,121,5))','import numpy as np\ncounts,edges=np.histogram(t,bins=range(0,121,5))\nax.stairs(counts,edges,orientation="horizontal")'),False)
add(five,'five-min-wrong-stairs-frequencies',lambda c:c.replace('ax.hist(t, bins=range(0,121,5))','import numpy as np\ncounts,edges=np.histogram(t,bins=range(0,121,5))\nax.stairs(counts[::-1],edges)'),False)
add(five,'five-min-rwidth',lambda c:c.replace('bins=range','rwidth=.8, bins=range'),True)
add(compare,'compare-step-outline',lambda c:c.replace('density=True','histtype="step", density=True'),True)
add(compare,'compare-rwidth',lambda c:c.replace('density=True','rwidth=.8, density=True'),True)
add('explicit-legend-artist-handles','compare-explicit-reordered-legend',lambda c:c.replace('ax.legend(handles, ["авто", "вело"])','ax.legend(handles[::-1], ["вело", "авто"])'),True)
add('explicit-legend-artist-handles','compare-stepfilled-explicit-handles',lambda c:c.replace('density=True','histtype="stepfilled", density=True'),True)
add(compare,'compare-legend-color-wrong',lambda c:c+'\nax.get_legend().legend_handles[0].set_facecolor("red")',False)
add(compare,'compare-second-hist-color-changed',lambda c:c+'\nfor patch in ax.containers[1].patches:patch.set_facecolor("red")',False)
add(five,'five-min-wrong-rwidth-shifted-bins',lambda c:c.replace('bins=range','rwidth=.8, bins=range')+'\nfor patch in ax.patches:patch.set_x(patch.get_x()+1)',False)
(D/'hist-review-programs.json').write_text(json.dumps(P,ensure_ascii=False,indent=2));print(len(P))
