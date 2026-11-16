from pathlib import Path
import html,json,re,sys
ch,ls,tid,level=sys.argv[1:]
work=Path('/tmp/ku-audit')/ch
page=Path('site',ch,ls+'.html').read_text()
data=json.loads(re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>',page,re.S)[1])
t=next(x for x in data['tasks'] if x['id']==tid)
field='solution' if level=='solution' else 'hints'
if field=='solution': print(t[field])
else: print(html.unescape(re.sub('<[^>]+>','',t[field][int(level)-1])))
submitted = [json.loads(l) for l in (work/'submissions.jsonl').read_text().splitlines() if l.strip()] if (work/'submissions.jsonl').exists() else []
before = sum((a['lesson'],a['id'])==(ls,tid) for a in submitted)
with (work/'help.jsonl').open('a') as f: print(json.dumps({'lesson':ls,'id':tid,'help':level,'after_attempt':before}),file=f)
