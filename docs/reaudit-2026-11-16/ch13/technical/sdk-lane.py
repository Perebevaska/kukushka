"""Exercise the actual chapter snippets on fixtures. No server or SDK dependency."""
import argparse
import ast
import io
import json
import re
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace as N

cli = argparse.ArgumentParser()
cli.add_argument('course_root', type=Path)
cli.add_argument('--require-pass', action='store_true')
opt = cli.parse_args()
lesson = (opt.course_root / 'content/ch13/04c-llm.md').read_text()
harness = (opt.course_root / 'site/assets/harness.py').read_text()
blocks = re.findall(r'^```python(?: [^\n]+)?\n(.*?)^```', lesson, re.M | re.S)
# Use a complete code block whenever possible. Definitions can be extracted
# separately since a real SDK client would initiate a paid network call.
def block_with(marker):
    return next(block for block in blocks if marker in block)
def code_of_fn(src, name):
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(src, node)
def extract_module(src):
    return next(n.value.value for n in ast.parse(src).body
                if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '')=='_LOCAL_LLM_SRC')
browser = {}
exec(extract_module(harness),browser)
topics = ['кофе','еда','обслуживание','доставка','цена','атмосфера']
scope = dict(json=json,TOPICS=topics,MODEL='offline fixture',PROMPT='fixture')
exec(code_of_fn(block_with('def label(text)'), 'label'),scope)
exec(code_of_fn(block_with('bad = {"sentiment": None'), 'parse'),scope)
local = block_with('from openai import OpenAI')
local_receipt = local[local.index('choice = '):]
demo = block_with('ans = json.loads(raw[')
demo_loop = next(n for n in ast.parse(demo).body if isinstance(n,ast.For))
demo_code = ast.get_source_segment(demo, demo_loop)
ok = json.dumps({'sentiment':'positive','topic':'еда'},ensure_ascii=False)
wrong_type = json.dumps({'sentiment':'positive','topic':['еда']},ensure_ascii=False)
cases = []
def run(name, expected, op):
    try:
        observed = op()
    except Exception as exc:
        observed = f'{type(exc).__name__}: {exc}'
    cases.append({'case':name, 'expected':expected, 'observed':observed, 'match':observed == expected})
def cloud_result(reason, blocks):
    scope['client'] = N(messages=N(create=lambda **_: N(stop_reason=reason,content=blocks)))
    return scope['parse'](scope['label']('fixture'))['ok']
for name, stop, content, wanted in (
        ('valid','end_turn',[N(type='thinking'), N(type='text',text=ok)],True),
        ('empty blocks','end_turn',[],False),
        ('blank','end_turn',[N(type='text',text=' ')],False),
        ('no text block','end_turn',[N(type='thinking')],False),
        ('refusal','refusal',[N(type='text',text=ok)],False),
        ('truncated','max_tokens',[N(type='text',text=ok)],False)):
    run('Claude '+name,wanted,lambda:cloud_result(stop,content))
def obj(choices):
    return [N(finish_reason=c['finish_reason'],message=N(**c['message'])) for c in choices]
choices_cases = [('empty choices',[],False)]
for name, reason, content, wanted in (
        ('valid','stop',ok,True),('null','stop',None,False),('whitespace','stop','  ',False),
        ('length','length',ok,False),('filter','content_filter',ok,False),
        ('wrong type in JSON','stop',wrong_type,False)):
    choices_cases.append((name,[{'finish_reason':reason,'message':{'content':content}}],wanted))
def native_result(choices):
    ns={'resp':N(choices=obj(choices))}
    output=io.StringIO()
    with redirect_stdout(output):
        exec(local_receipt, ns)
    raw=output.getvalue().strip()
    return scope['parse'](raw)['ok']
def raw_browser(choices):
    browser['_request']=lambda *args, **kwargs:{'choices':choices}
    return browser['ask']('отзыв',model='fixture')
def widget(choices):
    # A malformed first record must leave room for the next record in this
    # very loop to render, so run them through the same list.
    good=[{'finish_reason':'stop','message':{'content':ok}}]
    queue=iter([choices,good])
    fake=N(ask=lambda *args, **kwargs: raw_browser(next(queue)))
    ns=dict(local_llm=fake, json=json, reviews=['первый','следующий'], PROMPT='', TOPICS=set(topics))
    output=io.StringIO()
    with redirect_stdout(output):
        exec(demo_code,ns)
    return [line.startswith('✓') for line in output.getvalue().splitlines()]
for name,choices,wanted in choices_cases:
    run('Python Chat Completions '+name,wanted,lambda:native_result(choices))
    run('browser ask + batch '+name,[wanted,True],lambda:widget(choices))
pairs = [(s,t) for s in ('positive','negative') for t in topics]
for sentiment,topic in pairs:
    def roundtrip():
        return scope['parse'](json.dumps(dict(sentiment=sentiment,topic=topic),ensure_ascii=False))['ok']
    run(f'parse {sentiment} {topic}',True,roundtrip)
print(json.dumps(cases,ensure_ascii=False,indent=2))
if opt.require_pass:
    assert all(r['match'] for r in cases), [r for r in cases if not r['match']]
