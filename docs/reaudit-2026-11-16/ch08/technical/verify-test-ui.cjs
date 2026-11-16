const fs=require('node:fs');
const {chromium}=require('/Users/dmitriikormin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
let auditBrowser;
(async()=>{
 const b=auditBrowser=await chromium.launch({headless:true});
 const keys=JSON.parse(fs.readFileSync('/private/tmp/kuch08round/keys-retest.json','utf8'));
 const core=['c1','c2','c3','c5','c6','c12','c13','c14','c15'];const rows=[];
 for(const n of [7,8]){
  const c=await b.newContext(),p=await c.newPage();await p.goto('http://127.0.0.1:55578/ch08/test.html');
  if(!await p.locator('details.test-questions').evaluate(e=>e.open))await p.locator('details.test-questions summary').click();
  const qs=p.locator('.quiz-c');if(await qs.count()!==15)throw Error('Expected 15 questions');
  let j=0;
  for(let i=0;i<15;i++){
   const q=qs.nth(i),id=await q.getAttribute('data-q');if(!core.includes(id))continue;
   const k=keys['test/quiz/'+(i+1)],right=k.original_order[k.answer-1]-1;
   const pick=j++<n?right:(right+1)%4;await q.locator('.qopt[data-i="'+pick+'"]').click();
  }
  const before=await p.locator('#test-result').innerText();
  if(!before.includes(n+' из 9'))throw Error(before);
  if(before.includes('глава усвоена')!==(n===8))throw Error(before);
  await p.reload();const reload=await p.locator('#test-result').innerText();if(reload!==before)throw Error('Reload changed score');
  if(!await p.locator('details.test-questions').evaluate(e=>e.open))await p.locator('details.test-questions summary').click();
  for(let i=0;i<15;i++){
   const q=p.locator('.quiz-c').nth(i),id=await q.getAttribute('data-q');if(core.includes(id))continue;
   const k=keys['test/quiz/'+(i+1)],right=k.original_order[k.answer-1]-1;
   await q.locator('.qopt[data-i="'+((right+1)%4)+'"]').click();
  }
  const after=await p.locator('#test-result').innerText();
  if(!after.includes(n+' из 9')||after.includes('глава усвоена')!==(n===8))throw Error(after);
  await p.locator('#test-result').screenshot({path:'docs/reaudit-2026-11-16/ch08/technical/test-ui-core-'+n+'.png'});
  const artifact=await p.locator('a.next[href="../ch15/01-artifact.html"]').count();
  const project=await p.locator('.theory').count();
  const exit=p.locator('p.prose a[href="../ch15/06-final-project.html"]');if(await exit.count()!==1||artifact!==1)throw Error('Missing core exit');
  await exit.click();const target=await p.locator('h1').first().innerText();if(!p.url().endsWith('/ch15/06-final-project.html'))throw Error(p.url());
  rows.push({core_correct:n,core_total:9,extra_answered:6,extra_correct:0,before_optional:before,after_optional:after,reload_identical:true,core_exit_to_artifact:true,project_exit_title:target});
  await c.close();
 }
 fs.writeFileSync('docs/reaudit-2026-11-16/ch08/technical/test-ui.json',JSON.stringify(rows,null,2)+'\n');console.log(JSON.stringify(rows));await b.close();
})().catch(async e=>{console.error(e);process.exitCode=1;if(auditBrowser)await auditBrowser.close();});
