"""One shared, versioned input for two independently authored business answers."""
from pathlib import Path
import hashlib
import json
import os
import platform

import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[5]
WORK = Path('/private/tmp/kuch15round/judge')
EXPORT = Path('/private/tmp/kuch15round/course.json')
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = json.loads(EXPORT.read_text())
    item = next(r for r in rows if r['lesson'] == 'ch15/06-final-project' and r['id'] == 'profit')
    namespace = {}
    os.chdir(WORK / 'data')
    exec(compile(item['setup'], '<current canonical setup>', 'exec'), namespace)
    test = namespace['test'][['client_id', 'city', 'revenue_90', 'revenue_trend', 'churn', 'p']]
    assert test.client_id.is_unique and test.notna().all().all()
    test.to_csv(WORK / 'shared-input.csv', index=False, float_format='%.17g')
    (HERE / 'canonical-setup.py').write_text(item['setup'])
    metadata = {
        'baseline': '740b115',
        'purpose': 'same data for two independent answers; not a learner submission',
        'snapshot': '2026-06-30',
        'observed_target_horizon': '2026-07-01 through 2026-09-30',
        'train_cutoffs': ['2025-09-30', '2025-12-31', '2026-03-31'],
        'rows': len(test),
        'export_sha256': digest(EXPORT),
        'setup_sha256': digest(HERE / 'canonical-setup.py'),
        'database_sha256': digest(WORK / 'data/office.db'),
        'input_sha256': digest(WORK / 'shared-input.csv'),
        'versions': {'python': platform.python_version(), 'pandas': pd.__version__, 'sklearn': sklearn.__version__},
    }
    (HERE / 'input-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata))


if __name__ == '__main__':
    main()
