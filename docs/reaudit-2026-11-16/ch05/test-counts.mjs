import fs from 'node:fs';
import crypto from 'node:crypto';
const source = 'content/ch05/test.md';
const text = fs.readFileSync(source, 'utf8');
const questions = [...text.matchAll(/::: quiz ([^\n]+)\n([\s\S]*?)\n:::/g)].map((b, i) => {
  const opts = [...b[2].matchAll(/^- \[([x ])\] (.*)\n  > (.*)/gm)];
  const lengths = opts.map(x => [...x[2]].length);
  const correct = opts.findIndex(x => x[1] === 'x');
  if (opts.length !== 4 || opts.filter(x => x[1] === 'x').length !== 1 || opts.some(x => !x[3].trim())) throw Error('Malformed question ' + (i + 1));
  return {id: `test/quiz/${i+1}`, lesson:b[1], options:opts.length, explanations:opts.length, lengths,
    correct_longest:lengths[correct] === Math.max(...lengths),
    correct_unique_longest:lengths[correct] > Math.max(...lengths.filter((_,j)=>j!==correct)),
    correct_shortest:lengths[correct] === Math.min(...lengths)};
});
const runtime = fs.readFileSync('site/assets/lesson.js', 'utf8');
if (!runtime.includes('pct = Math.round(100 * ok / qs.length)') || !runtime.includes("pct >= 80 ? 'good'")) throw Error('Scoring implementation changed');
const thresholds = Array.from({length:14},(_,ok)=>({ok,pct:Math.round(100*ok/13),passed:Math.round(100*ok/13)>=80}));
const result = {source_sha256:crypto.createHash('sha256').update(text).digest('hex'), questions,
 total_questions:questions.length,total_options:questions.reduce((n,x)=>n+x.options,0),total_explanations:questions.reduce((n,x)=>n+x.explanations,0),
 unique_longest_correct:questions.filter(x=>x.correct_unique_longest).length,
 longest_correct_including_ties:questions.filter(x=>x.correct_longest).length,
 thresholds,minimum_to_pass:thresholds.find(x=>x.passed).ok};
fs.writeFileSync('docs/reaudit-2026-11-16/ch05/test-metrics.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({questions:result.total_questions,options:result.total_options,explanations:result.total_explanations,longest:result.longest_correct_including_ties,unique_longest:result.unique_longest_correct,minimum_to_pass:result.minimum_to_pass,near_threshold:thresholds.slice(10,12)}));
