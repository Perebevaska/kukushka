"""Verify the files linked from chapter 3 and fingerprint the accepted release."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href', ''))


def downloads(page, name):
    path = SITE / 'ch03' / (page + '.html')
    parser = Links()
    parser.feed(path.read_text())
    urls = [url for url in parser.hrefs if url.endswith('/' + name)]
    assert urls, (page, name)
    assert all((path.parent / url).is_file() for url in urls)
    return sorted(set(urls))


def verify(export):
    baseline = json.loads((AUDIT / 'technical/baseline.json').read_text())
    bundle = json.loads(export.read_text())
    chapter = [r for r in bundle if r['lesson'].startswith('ch03/')]
    assert len([r for r in chapter if r['kind'] == 'task']) == 93
    urls = {p: {n: downloads(p, n) for n in names} for p, names in {
        'index': ['ch03-project-template.ipynb', 'check_notebook.py'],
        '09-project': ['ch03-project-template.ipynb', 'check_notebook.py'],
        '03b-excel': ['ch03-excel.ipynb']}.items()}
    student = SITE / 'notebooks'
    shared = json.loads((AUDIT.parent / 'ch02/technical/release.json').read_text())['files']
    for name in [key for key in shared if key.startswith('content/ch02/') or key.startswith('site/notebooks/')]:
        assert sha(ROOT / name) == shared[name], name
    chapter2_index = Links()
    chapter2_index.feed((SITE / 'ch02/index.html').read_text())
    assert '../notebooks/ch02-project-template.ipynb' in chapter2_index.hrefs
    sources = sorted((ROOT / 'content/ch03').glob('*.md')) + sorted((SITE / 'ch03').glob('*.html'))
    sources += [student / n for n in ['ch03-project-template.ipynb', 'extra/ch03-excel.ipynb', 'tasks/ch03.json', 'ch03-practice.ipynb', 'check_notebook.py']]
    sources += [ROOT / 'tools' / n for n in ['make_notebooks.py', 'build.py', 'gen_excel.py']]
    sources += sorted((ROOT / 'tools/checks').glob('ch03*.py'))
    inputs = sorted({n for r in chapter for n in r['files']})
    return {'base_commit':baseline['head'], 'base_ch03_tree':'f75c9f5a81b220f7cbdd52883f543147beed9604',
            'base_export_sha256':baseline['export_sha256'], 'export_sha256':sha(export),
            'export_types':{k:sum(r['kind']==k for r in chapter) for k in sorted({r['kind'] for r in chapter})},
            'downloads':urls, 'sources_and_published_files':{str(p.relative_to(ROOT)):sha(p) for p in sources},
            'data':{n:sha(SITE/'data'/n) for n in inputs},
            'accepted_ch02_sources_and_downloads_unchanged':True}


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1])), indent=2, ensure_ascii=False))
