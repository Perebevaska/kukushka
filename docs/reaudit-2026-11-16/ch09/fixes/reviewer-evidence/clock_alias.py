"""Small real-clock reproducer using the checker embedded in the chapter page."""
import contextlib
import io
import json
import math
import re
import sys
from pathlib import Path

page = Path(sys.argv[1])
lesson = json.loads(re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>', page.read_text(), re.S)[1])
task = next(t for t in lesson['tasks'] if t['id'] == 'best-of')
code = task['solution'].replace('import time', 'from time import perf_counter as now').replace('time.perf_counter()', 'now()')
records = []
for label, candidate in [('attribute', task['solution']), ('imported clock', code), ('constant', code.replace('return min(times)', 'return 0.0'))]:
    submitted = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(candidate, submitted)
    check = {'need':submitted.__getitem__, 'close':lambda a,b,tol: abs(a-b)<=tol}
    try:
        exec(task['check'], check)
    except Exception as problem:
        msg = str(problem)
    else:
        msg = 'accepted'
    records.append(dict(label=label, candidate=candidate, verdict=msg))
print(json.dumps(records,ensure_ascii=False,indent=2))
