"""The baseline lesson's zero-bisection loop versus the empirical SLA contract."""
import json
from statistics import mean

minutes = [10.1, 10.2, 10.3]
late = lambda t: mean(v > t for v in minutes)
lo, hi = 0, 300
while hi-lo > .01:
    mid = (lo+hi)/2
    if (late(lo)-.1)*(late(mid)-.1) > 0:
        lo = mid
    else:
        hi = mid
rounded = round((lo+hi)/2)
first = next(t for t in range(301) if late(t)<=.1)
eps = 1e-8
print(json.dumps({"rounded_root":rounded,"late_rounded":late(rounded),
                  "first_integer":first,"late_first":late(first),
                  "first_Adam_abs_updates": [0.1*g/(abs(g)+eps) for g in [0,eps,1000*eps]]},indent=2))
