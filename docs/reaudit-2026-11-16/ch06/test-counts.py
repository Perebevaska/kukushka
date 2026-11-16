from pathlib import Path
import importlib.util,json,re,sys
root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('course_build',root/'tools/build.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
course=m.yaml.safe_load((root/'content/course.yaml').read_text()); ch=next(c for c in course['chapters'] if c['id']=='ch06')
extra=m.parse_chapter_extra(ch)['test']
assert extra['n']==15
assert re.findall('data-q="([^"]+)"',extra['html'])==[f'c{i}' for i in range(1,16)]
res={}
for name,path in [('before',Path(__file__).with_name('test-source-before.md')),('after',root/'content/ch06/test.md')]:
 s=path.read_text(); rows=[]
 for i,q in enumerate(re.findall(r'^::: quiz[^\n]*\n(.*?)^:::',s,re.M|re.S),1):
  options=re.findall(r'^- \[([ x])\] (.*)$',q,re.M); explanations=re.findall(r'^  > (.*)$',q,re.M)
  assert len(options)==len(explanations)==4 and sum(k=='x' for k,t in options)==1
  lens=[len(t) for _,t in options]; correct=next(j for j,(k,t) in enumerate(options) if k=='x')
  rows.append(dict(id=f'c{i}',lengths=lens,correct_length=lens[correct],correct_longest=lens[correct]==max(lens),unique_longest=lens.count(max(lens))==1 and lens[correct]==max(lens),explanations=len(explanations)))
 res[name]=dict(questions=len(rows),options=4*len(rows),explanations=sum(r['explanations'] for r in rows),correct_longest=sum(r['correct_longest'] for r in rows),correct_unique_longest=sum(r['unique_longest'] for r in rows),rows=rows)
res['threshold']=[dict(correct=n,percent=round(100*n/15),pass_sidebar=n/15>=.8,pass_page=int(100*n/15+.5)>=80) for n in range(16)]
res['render_check']='parse_chapter_extra only; no site build or browser'
Path(__file__).with_name('test-counts.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='rows'} if isinstance(v,dict) else v for k,v in res.items() if k!='threshold'},ensure_ascii=False))
