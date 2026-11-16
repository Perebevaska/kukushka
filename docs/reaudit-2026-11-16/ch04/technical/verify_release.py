"""Check the chapter download, published lessons, figures, and previous chapters' templates."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs).get('href', ''))


def verify(export):
    base = json.loads((AUDIT / 'technical/baseline.json').read_text())
    records = [r for r in json.loads(export.read_text()) if r['lesson'].startswith('ch04/')]
    kinds = {k:sum(r['kind'] == k for r in records) for k in sorted({r['kind'] for r in records})}
    assert kinds['task'] == 112
    assets = SITE / 'notebooks'
    chapter_links = {}
    for name in ('index','09-project'):
        page = SITE / 'ch04' / (name + '.html')
        links = Links()
        links.feed(page.read_text())
        for file in ('ch04-project-template.ipynb', 'check_notebook.py'):
            assert '../notebooks/' + file in links.hrefs and (assets / file).is_file()
        chapter_links[name]=[link for link in links.hrefs if link.endswith(('project-template.ipynb','check_notebook.py'))]
    old = json.loads((AUDIT.parent / 'ch03/technical/release.json').read_text())['sources_and_published_files']
    assert all(digest(ROOT / f)==h for f,h in old.items() if f.startswith('content/ch03/') or f.startswith('site/notebooks/'))
    assert digest(assets / 'ch02-project-template.ipynb') == json.loads((AUDIT.parent / 'ch02/technical/release.json').read_text())['files']['site/notebooks/ch02-project-template.ipynb']
    lessons=sorted((ROOT / 'content/ch04').glob('*.md'))
    figures=sorted(set(re.findall(r'(?m)^::: figure ([\w-]+)', '\n'.join(p.read_text() for p in lessons))))
    files=lessons + sorted((SITE / 'ch04').glob('*.html'))
    files += [ROOT / 'content/figures' / (name+'.svg') for name in figures]
    files += [assets / name for name in ('ch04-project-template.ipynb','ch04-practice.ipynb','tasks/ch04.json','check_notebook.py')]
    files += [ROOT / 'tools' / name for name in ('build.py','make_notebooks.py')]
    files += sorted((ROOT / 'tools/checks').glob('ch04*.py'))
    data = sorted({f for r in records for f in r['files']})
    print(json.dumps({'base_commit':base['head'], 'base_tree':base['chapter_tree'],
                      'base_export_sha256':base['export_sha256'], 'export_sha256':digest(export),
                      'export_types':kinds,'download_links':chapter_links,'figure_count':len(figures),
                      'sources_and_published_files':{str(p.relative_to(ROOT)):digest(p) for p in files},
                      'data':{f:digest(SITE/'data'/f) for f in data}},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
