"""Freeze and verify current ch14 release plus chapter boundary; stdlib/read-only Git."""
from pathlib import Path
import collections,hashlib,json,re,subprocess,sys
R=Path('/Users/dmitriikormin/Documents/Projects/ds-course');D=R/'docs/reaudit-2026-11-16/ch14';W=Path('/private/tmp/kuch14round');baseline=json.loads((D/'technical/baseline.json').read_text());head=baseline['head'];export=Path(sys.argv[1]) if len(sys.argv)>1 else W/'final.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def old(p):return git('show',head+':'+str(p))
def h(b):return hashlib.sha256(b).hexdigest()
def normalize(b):
 b=re.sub(rb'([?&]v=)[0-9a-f]{10,64}(?=["\'& >])',rb'\1CACHE_TOKEN',b)
 return re.sub(rb'(data-v=["\'])[0-9a-f]{10,64}(?=["\'])',rb'\1CACHE_TOKEN',b)
assert head=='6adf0ebc1b1eceab13859827b615f9b92209d785';assert sha(export)=='bdce6f6b7ce042789cf94ffbe6a07b49a14845f41da0c6ad7f7460e2bfe8417d'
tracked=[p.decode() for p in git('ls-files','-z').split(b'\0') if p];changed=[p.decode() for p in git('diff','--name-only','-z',head).split(b'\0') if p]
source_changed=[p for p in changed if p.startswith('content/')];assert len(source_changed)==9 and all(p.startswith('content/ch14/') for p in source_changed),source_changed
outside_html=[];inside_html=[];global_ch14_generated=[]
for p in changed:
 if not p.endswith('.html') or not p.startswith('site/'):continue
 before=old(p);after=(R/p).read_bytes();record={'path':p,'before_sha256':h(before),'after_sha256':h(after),'cache_token_only':normalize(before)==normalize(after)}
 if p.startswith('site/ch14/'):inside_html.append(record)
 elif p=='site/cheatsheet.html':
  def outside_cheatsheet(b):return re.sub(rb'(?s)<h2 class="cs-ch">[^<]*14\.[^<]*</h2>.*?(?=<h2 class="cs-ch">[^<]*15\.)',b'CH14_GENERATED_SECTION',b)
  require_same=normalize(outside_cheatsheet(before))==normalize(outside_cheatsheet(after));assert require_same,'cheatsheet changes outsidech14';record['outside_ch14_cache_token_only']=True;global_ch14_generated.append(record)
 else:assert record['cache_token_only'],'nonch14HTML substantive '+p;outside_html.append(record)
# JSON assets are regenerated across course, but their nonchapter14 records must remain exact.
assets={}
for p,field in [('site/assets/course.js','id'),('site/assets/search.js','u')]:
 def payload(s):
  body=s.split('=',1)[1].strip();value,end=json.JSONDecoder().raw_decode(body);return value,body[end:]
 (a,tail0),(b,tail1)=payload(old(p).decode()),payload((R/p).read_text());assert tail0==tail1,'asset remaining assignments unchanged '+p
 af=[r for r in a if r.get(field)!='ch14' and not str(r.get(field,'')).startswith('ch14/')];bf=[r for r in b if r.get(field)!='ch14' and not str(r.get(field,'')).startswith('ch14/')];assert af==bf,'outsidech14 asset records '+p;assets[p]={'before_sha256':h(old(p)),'after_sha256':sha(R/p),'outside_ch14_records':len(af),'outside_ch14_exact_equal':True}
original=read(W/'course.json');current=read(export);assert [r for r in original if not r['lesson'].startswith('ch14/')]==[r for r in current if not r['lesson'].startswith('ch14/')],'outsidech14export changed';chapter=[r for r in current if r['lesson'].startswith('ch14/')];assert len(chapter)==98
(D/'technical/release-export.json').write_text(json.dumps(chapter,ensure_ascii=False,indent=2)+'\n')
# Every changed tracked file belongs to expected source, generated output or current audit docs.
allowed_generated={'site/assets/course.js','site/assets/search.js','site/notebooks/ch14-practice.ipynb','site/notebooks/tasks/ch14.json'}
unexpected=[p for p in changed if not(p.startswith('content/ch14/') or p.startswith('docs/reaudit-2026-11-16/ch14/') or p in allowed_generated or p.endswith('.html') and p.startswith('site/'))];assert not unexpected,unexpected
for p,v in baseline['data_sha256'].items():assert sha(R/'site/data'/p)==v==h(old(Path('site/data')/p)),'NPZ immutable against6ad '+p
paths={D/'technical/release-export.json',R/'content/course.yaml',R/'tools/build.py',R/'tools/make_notebooks.py',export}
paths.update((R/'content/ch14').glob('*.md'));paths.update((R/'site/ch14').glob('*.html'));paths.update((R/'site/assets').glob('*.js'));paths.update((R/'site/assets').glob('*.css'));paths.update((R/'site/assets').glob('*.py'))
paths.update(R/'site/data'/p for p in baseline['data_sha256']);paths.update(R/'content/figures'/(f['figure']+'.svg') for f in baseline['figures']);paths.update(R/'site/notebooks'/p for p in ['ch14-practice.ipynb','tasks/ch14.json','compare_showcase_features.py','requirements.txt','check_notebook.py'])
for page in (R/'site/ch14').glob('*.html'):
 for url in re.findall(r'(?:src|href)=["\']([^"\']+)',page.read_text()):
  if '/assets/' not in url:continue
  path=(page.parent/url.split('?')[0].split('#')[0]).resolve()
  if path.is_file():paths.add(path)
manifest={str(p.relative_to(R)) if p.is_relative_to(R) else str(p):sha(p) for p in sorted(paths) if p.is_file()}
reference={'baseline_head':head,'release_export_sha256':sha(export),'release_export_path':str(export),'files_sha256':manifest,'changed_content':source_changed,'HTML_inside_ch14':inside_html,'HTML_outside_ch14':outside_html,'outside_HTML_cache_token_only':True,'global_generated_ch14_only':global_ch14_generated,'assets':assets,'chapter_export_count':98,'chapter_export_kinds':dict(collections.Counter(r['kind'] for r in chapter)),'outside_export_exact_equal':True,'data_all4_immutable_against_baseline_HEAD':True,'changed_tracked_paths':changed,'unexpected_changed_paths':unexpected,'verification_scope':'stdlib hashes/JSON comparisons; no runtime, ML, Jupyter or browser execution; read-only Git show/diff'}
(D/'technical/release.json').write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'manifest_files':len(manifest),'changed_content':source_changed,'inside_HTML':len(inside_html),'outside_HTML_cache_only':len(outside_html),'global_cheatsheet_ch14_only':len(global_ch14_generated),'data_immutable':4,'export':sha(export),'outside_export_exact_equal':True},ensure_ascii=False,indent=2))
