"""Regenerate only in a temporary directory. Check the historical packaged files."""
import csv
import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
import re

here = Path(__file__).resolve().parent
root = here.parents[3]
sys.path.insert(0, str(root / 'tools'))
import gen_data
import gen_ch07_tiers

with tempfile.TemporaryDirectory() as dest:
    gen_data.OUT = gen_ch07_tiers.DATA = Path(dest)
    gen_data.gen_chapter6(random.Random(6006))
    gen_data.gen_chapter7(random.Random(7007))
    gen_ch07_tiers.main()
    for f in sorted((here/'data-baseline').glob('*.csv')):
        assert (Path(dest)/f.name).read_bytes() == f.read_bytes() == (root/'site/data'/f.name).read_bytes()
        print(f.name,hashlib.sha256(f.read_bytes()).hexdigest())
    for name in ('catering_labels.csv', 'guests_churn_dates.csv'):
        assert (Path(dest)/name).read_bytes()==(root/'site/data'/name).read_bytes()
        with (Path(dest)/name).open() as f:
            rows = list(csv.DictReader(f))
        print('calendar companion',name, len(rows), rows[-1])

figs = []
for p in sorted((root/'content/ch07').glob('*.md')):
    names = re.findall('^::: figure (.+)$',p.read_text(),flags=re.M)
    for n in names:
        tree = ET.parse(root/'content/figures'/(n+'.svg'))
        assert tree.getroot().find('{http://www.w3.org/2000/svg}title') is not None
    figs += names
    print(p.stem,'figures',len(names), ','.join(names))
print('references, distinct SVG:',len(figs),len(set(figs)))
