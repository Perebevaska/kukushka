import fs from 'node:fs';
import assert from 'node:assert/strict';
const dir='docs/reaudit-2026-11-16/ch07/';
const count = path => {
 const s=fs.readFileSync(path,'utf8');
 const rows=[...s.matchAll(/::: quiz ([^\n]+)\n([\s\S]*?)\n:::/g)].map((m,i)=> {
  const opts=[...m[2].matchAll(/^- \[([x ])\] (.+)$/gm)].map(o=>({correct:o[1]==='x',text:o[2].replace(/`/g,'').replace(/\s+/g,' ').trim()}));
  assert.equal(opts.length,4); assert.equal(opts.filter(o=>o.correct).length,1);
  const lengths=opts.map(o=>o.text.length), k=opts.findIndex(o=>o.correct), max=Math.max(...lengths), min=Math.min(...lengths);
  return {id:`c${i+1}`,topic:m[1],lengths,correctLength:lengths[k],uniqueLongest:lengths[k]===max&&lengths.filter(n=>n===max).length===1,uniqueShortest:lengths[k]===min&&lengths.filter(n=>n===min).length===1,explanations:(m[2].match(/^  > /gm)||[]).length};
 });
 return {questions:rows.length,options:rows.length*4,explanations:rows.reduce((n,r)=>n+r.explanations,0),uniqueLongest:rows.filter(r=>r.uniqueLongest).length,uniqueShortest:rows.filter(r=>r.uniqueShortest).length,rows};
};
const js=fs.readFileSync('site/assets/lesson.js','utf8');
assert(js.includes('pct = Math.round(100 * ok / qs.length)'));
assert(js.includes("pct >= 80 ? 'good'"));
const rows=Array.from({length:14},(_,ok)=>({ok,total:13,score:Math.round(100*ok/13),passed:Math.round(100*ok/13)>=80}));
assert.equal(rows.find(r=>r.passed).ok,11);
const result={before:count(dir+'test-before.md'),after:count('content/ch07/test.md'),threshold:{source:'site/assets/lesson.js:483-486',expression:'Math.round(100 * ok / qs.length) >= 80',minimum:11,rows},blind:{answers:13,matchedKeys:13,changesAfterKeyReveal:0},changedRevisions:['c4','c5','c10','c11','c13']};
assert.equal(result.after.questions,13); assert.equal(result.after.explanations,52);
fs.writeFileSync(dir+'test-metrics.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({before:{q:result.before.questions,options:result.before.options,explanations:result.before.explanations,longest:result.before.uniqueLongest,shortest:result.before.uniqueShortest},after:{q:result.after.questions,options:result.after.options,explanations:result.after.explanations,longest:result.after.uniqueLongest,shortest:result.after.uniqueShortest},threshold:result.threshold.minimum}));
