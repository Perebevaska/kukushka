/* Resolve only local public HTML/JS/styles. No course server, Python runtime or user storage. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const site = path.resolve('site');
const base = 'http://127.0.0.1:55585/';
const report = {tests:[],routes:[],inputs:{}};
const testHTML = fs.readFileSync(path.join(site,'ch15/test.html'),'utf8');
const keys = Object.fromEntries([...testHTML.matchAll(/class="quiz-c" data-q="(c\d+)"([\s\S]*?)<\/ul>/g)].map(m=>[m[1],[...m[2].matchAll(/<li>\s*(?:<p>)?\s*\[([x ])\]/g)].map(v=>v[1]).indexOf('x')]));
assert.equal(Object.keys(keys).length,17);
assert.ok(Object.values(keys).every(v=>v>=0));
const core = ['c1','c2','c3','c16','c17'];
const extras = Object.keys(keys).filter(k=>!core.includes(k));
const sections = ['бриф','что-сдаём','критерии-приёмки','чек-лист-ревью','readme-для-портфолио','итог-для-руководителя-b2b','перенос-на-выездной-сервис'];
for (const f of ['ch15/test.html','ch15/01-artifact.html','ch15/06-final-project.html','assets/course.js','assets/core.js','assets/lesson.js','assets/app.css']) {
 report.inputs[f] = crypto.createHash('sha256').update(fs.readFileSync(path.join(site,f))).digest('hex');
}
async function isolate(browser){
 const context = await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'});
 await context.route('**/*',async route=>{
  const u = new URL(route.request().url());
  const rel = u.pathname.slice(1);
  if(u.origin===new URL(base).origin && route.request().method()==='GET' && /^(ch15\/(test|01-artifact|02-service|05-project|06-final-project)\.html|assets\/(core\.js|lesson\.js|course\.js|app\.css|vendor\/codemirror\/[a-z.]+))$/.test(rel) && fs.existsSync(path.join(site,rel))) {
   const response = await route.fetch();
   const body = await response.body();
   assert.equal(response.status(),200,rel);
   assert.ok(body.equals(fs.readFileSync(path.join(site,rel))),rel+' on HTTP server differs from final site');
   return route.fulfill({response,body});
  }
  return route.fulfill({status:404,body:''});
 });
 return context;
}
async function marked(page){
 return page.locator('.quiz-c[data-answered]').evaluateAll(items=>items.map(i=>[i.dataset.q,i.dataset.answered]));
}
async function score(page){
 return {text:await page.locator('#test-result').innerText(),marks:await marked(page),indicator:await page.locator('[data-ctest="ch15"]').first().getAttribute('data-done')};
}
async function select(page,ids,right){
 for(const [i,id] of ids.entries()){
  const index = i<right ? keys[id] : (keys[id]+1)%4;
  await page.locator('.quiz-c[data-q="'+id+'"] .qopt[data-i="'+index+'"]').click();
 }
}
(async()=>{
 const browser = await chromium.launch();
 try {
  for (const [mainRight,totalRight] of [[3,14],[4,13]]){
   const ctx = await isolate(browser), p=await ctx.newPage();
   await p.goto(base+'ch15/test.html');
   await p.locator('.quiz-c .qopt').first().waitFor({state:'attached'});
   const toggle=p.locator('[data-core-only]').first();
   await toggle.check();
   await p.locator('.test-questions summary').click();
   await select(p,core,mainRight);
   const main = await score(p);
   await toggle.uncheck();
   const switched = await score(p);
   assert.deepEqual(switched.marks,main.marks);
   await p.reload();
   await p.locator('.quiz-c[data-answered]').first().waitFor({state:'attached'});
   const reload = await score(p);
   assert.deepEqual(reload.marks,main.marks);
   const fullModePersists = !await toggle.isChecked();
   await select(p,extras,totalRight-mainRight);
   const full = await score(p);
   await toggle.check();
   await p.reload();
   await p.waitForFunction(()=>document.querySelectorAll('.quiz-c[data-answered]').length===17);
   const back=await score(p);
   assert.deepEqual(back.marks,full.marks);
   assert.equal(main.indicator,mainRight===4?'all':'part');
   assert.equal(reload.indicator,'part');
   assert.equal(full.indicator,totalRight===14?'all':'part');
   assert.equal(back.indicator,mainRight===4?'all':'part');
   assert.match(main.text,new RegExp(mainRight+' из 5'));
   assert.match(full.text,new RegExp('Полный (?:путь|маршрут).*'+totalRight+' из 17'));
   report.tests.push({mainRight,totalRight,main,switchedIncompleteFull:reload,full,fullModePersists,backToMainPersists:await toggle.isChecked(),afterReturn:back});
   await ctx.close();
  }
  for (const [route,target] of [['main','06-final-project'],['full','02-service']]){
   const ctx = await isolate(browser),p=await ctx.newPage();
   await p.goto(base+'ch15/01-artifact.html');
   await p.locator('.lnav-list').first().waitFor();
   if(route==='main'){
    await p.getByRole('button',{name:'Все главы курса →'}).click();
    await p.locator('[data-core-only]').first().check();
    await p.getByRole('button',{name:'← Разделы урока'}).click();
   }
   const choice=p.locator('article.theory p').filter({hasText:'Куда дальше?'});
   const sec=await choice.getAttribute('data-pg');
   await p.locator('.lnav a[href="#'+sec+'"]').click();
   assert.ok(await choice.isVisible());
   await choice.locator('a[href="'+target+'.html"]').click();
   assert.equal(new URL(p.url()).pathname,'/ch15/'+target+'.html');
   const result={route,section:sec,destination:new URL(p.url()).pathname,sections:[]};
   if(route==='main'){
    await p.locator('.lnav-list').first().waitFor();
    for (const id of sections){
     await p.locator('.lnav a[href="#'+id+'"]').click();
     assert.ok(await p.locator('h2[id="'+id+'"]').isVisible());
     const content=await p.locator('article.theory [data-pg="'+id+'"]:visible').allTextContents();
     result.sections.push({id,excerpt:content.join(' ').slice(0,320)});
    }
    await p.locator('.lnav a[href="#что-сдаём"]').click();
    const links=await p.locator('article.theory [data-pg="что-сдаём"] a:visible').evaluateAll(els=>els.map(e=>e.getAttribute('href')));
    result.tools=links;
    for(const f of ['../notebooks/project-template.ipynb','../notebooks/requirements.txt','../notebooks/check_notebook.py']) assert.ok(links.includes(f) && fs.existsSync(path.resolve(site,'ch15',f)));
    result.attemptedOrSolvedTasks=await p.evaluate(()=>Object.values(window.DSC.Progress.state.tasks).filter(t=>t.att||t.solved||t.help).length);
    assert.equal(result.attemptedOrSolvedTasks,0);
   }
   await p.waitForLoadState('networkidle');
   report.routes.push(result);
   await ctx.close();
  }
  const ctx=await isolate(browser), p=await ctx.newPage();
  await p.goto(base+'ch15/test.html');
  await p.locator('.qopt').first().waitFor({state:'attached'});
  const initial=['ch15/test#c7-content-v4','ch15/test#c2-balanced-v3','ch15/05-project#c1','ch15/06-final-project#c2','ch15/06-final-project#c1'];
  await p.evaluate(keys=>{
   const P=window.DSC.Progress;
   for(const k of keys) P.state.quiz[k]={ok:true,a:0,t:new Date().toISOString()};
   P.save();
  },initial);
  await p.reload();
  await p.locator('.qopt').first().waitFor({state:'attached'});
  assert.equal(await p.locator('.quiz-c[data-q="c7"]').getAttribute('data-answered'),null);
  assert.notEqual(await p.locator('.quiz-c[data-q="c2"]').getAttribute('data-answered'),null);
  await select(p,['c7'],1);
  assert.ok(await p.evaluate(()=>Object.hasOwn(window.DSC.Progress.state.quiz,'ch15/test#c7-content-v5')));
  const embedded=[];
  for(const [lesson,id,stable] of [['05-project','c1',''],['06-final-project','c2','c1']]){
   await p.goto(base+'ch15/'+lesson+'.html');
   const q=p.locator('.quiz-c[data-q="'+id+'-content-v2"]');
   await q.locator('.qopt').first().waitFor({state:'attached'});
   assert.equal(await q.getAttribute('data-answered'),null);
   if(stable) assert.notEqual(await p.locator('.quiz-c[data-q="'+stable+'"]').getAttribute('data-answered'),null);
   const pg=await q.evaluate(n=>n.closest('[data-pg]').dataset.pg);
   await p.locator('.lnav a[href="#'+pg+'"]').click();
   await q.locator('.qopt').first().click();
   const k='ch15/'+lesson+'#'+id+'-content-v2';
   assert.ok(await p.evaluate(k=>Object.hasOwn(window.DSC.Progress.state.quiz,k),k));
   embedded.push(k);
  }
  const savedKeys=await p.evaluate(()=>Object.keys(window.DSC.Progress.state.quiz).sort());
  assert.ok(initial.every(k=>savedKeys.includes(k)));
  report.revisionCheck={previous:initial,embedded,savedKeys};
  await ctx.close();
  fs.writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
