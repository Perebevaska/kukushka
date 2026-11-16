"""Expected BEFORE execution: for s with values equal to positions and t=30,
rolling(24, center=True) uses positions 18..41 inclusive:
12 past values (18..29), current 30, 11 future (31..41).
Feedback currently claims 12 future. No execution performed by quiz critic.
"""
import pandas as pd
s=pd.Series(range(80), dtype=float)
seen=[]
s.rolling(24, center=True).apply(lambda w: seen.append(tuple(w.index)) or w.mean(),raw=False)
assert tuple(range(18,42)) in seen
assert s.rolling(24,center=True).mean().iloc[30] == 29.5
print('PASS: t=30, window=18..41, future=31..41 (11 values)')
