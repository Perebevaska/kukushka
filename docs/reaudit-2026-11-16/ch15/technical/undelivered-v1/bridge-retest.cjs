const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('/Users/dmitriikormin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const w='/private/tmp/kuch15round', jobdir=w+'/jobs-retest', out=path.resolve('docs/reaudit-2026-11-16/ch15/fixes/student/retest'), phase=process.argv[2]||'initial', log=out+'/attempts.jsonl', keys=JSON.parse(fs.readFileSync(w+'/keys-retest.json'));
(async()=>{ const b=await chromium.launch({headless:true}),ctx=await b.newContext();let page=null,last=null;
async function grade(r){let id=r.question||r.lesson+'/'+r.task, lesson=id.split('/')[0];
 if(last!==lesson){if(page)await page.close();page=await ctx.newPage();await page.goto('http://127.0.0.1:55585/ch15/'+lesson+'.html');const one=page.getByRole('button',{name:'Весь урок на одной странице',exact:true});if(await one.count())await one.click();last=lesson;}
 if(lesson==='test'){const d=page.locator('details.test-questions');if(!await d.evaluate(e=>e.open))await d.locator('summary').click();}
 let passed,msg='',visibleOutput='',visiblePrompt='',visibleImages=[];
 if(r.action==='hint'){const card=page.locator('#task-'+r.task);await card.getByRole('button',{name:/^Подсказка [0-9]/}).first().click();return {hint:(await card.locator('.extras').innerText()).slice(-850)};}
 if(r.question){const [,kind,k]=id.split('/'),i=keys[id].original_order[r.choice-1]-1;
 const q=page.locator(kind==='predict'?'.predict':'.quiz-c').nth(Number(k)-1);
 visiblePrompt=await q.innerText();
 const opt=kind==='predict'?q.locator('.popt').nth(i):q.locator('.qopt[data-i="'+i+'"]');
 if(await opt.isDisabled())return {already_answered:true,screen:await q.locator('.predict-res').innerText()};
 await opt.click();passed=await opt.evaluate(e=>e.classList.contains('right'));msg=await q.locator('.predict-res').innerText();
 }else{
    const card=page.locator('#task-'+r.task);await card.locator('.task-ui').waitFor({state:'attached'});
    if(await card.getAttribute('data-kind')==='parsons'){
      await card.locator('.pline').first().waitFor({state:'attached'});
      const promptLines=await card.locator('.pline code').allTextContents();
      const requested=r.code.split('\n').filter(x=>x.trim());
      const tokenReader="import io,json,sys,tokenize\ndef scan(s):\n return [(t.type,t.string) for t in tokenize.generate_tokens(io.StringIO(s.strip()).readline) if t.type not in (tokenize.ENCODING,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.ENDMARKER)]\nprint(json.dumps([scan(s) for s in json.load(sys.stdin)]))";
      const exact=requested.every(line=>promptLines.includes(line.trim()));
      const parsed=exact?[]:JSON.parse(require('node:child_process').execFileSync('python3',['-c',tokenReader],{input:JSON.stringify([...promptLines,...requested]),encoding:'utf8'}));
      const canonical=exact?r.code:requested.map((line,i)=>{const index=promptLines.findIndex((_,j)=>JSON.stringify(parsed[j])===JSON.stringify(parsed[promptLines.length+i]));if(index<0)throw Error('Нет соответствующей строки Parsons: '+line);return line.match(/^\s*/)[0]+promptLines[index];}).join('\n');
      await card.evaluate((el,code)=>{
       const ls=code.split('\n').filter(x=>x.trim()),lines=()=>Array.from(el.querySelectorAll('.pline'));
       if(ls.length!==lines().length)throw Error('число строк для Parsons разное');
       for(let i=0;i<ls.length;i++){let j=lines().findIndex((n,k)=>k>=i&&n.querySelector('code').textContent===ls[i].trim());if(j<0)throw Error('нет строки '+ls[i]);while(j>i){lines()[j].querySelectorAll('button')[0].click();j--;}
        let d=Number(lines()[i].style.getPropertyValue('--ind'))-(ls[i].length-ls[i].trimStart().length)/4;
        if(!Number.isInteger(d))throw Error('отступ вне шага');while(d){lines()[i].querySelectorAll('button')[d>0?2:3].click();d+=d>0?-1:1;}}
      },canonical);
    }else{
     const cm=card.locator('.task-ui .CodeMirror').first();await cm.waitFor({state:'attached'});await cm.evaluate((e,c)=>e.CodeMirror.setValue(c),r.code); assert.equal(await cm.evaluate(e=>e.CodeMirror.getValue()),r.code);
    }
    const verdict=card.locator('.verdict').first();
    await verdict.evaluate(e=>{e.removeAttribute('data-audit-result');new MutationObserver(function(_m,ob){if(e.matches('.ok,.fail')){e.setAttribute('data-audit-result','ready');ob.disconnect();}}).observe(e,{childList:true,attributes:true,attributeFilter:['class']});});
    await card.getByRole('button',{name:'Проверить',exact:true}).click();await card.locator('.verdict[data-audit-result]').waitFor({timeout:90000});passed=await verdict.evaluate(e=>e.classList.contains('ok'));msg=(await verdict.innerText()).slice(0,2000);visibleOutput=await card.locator('.out').allTextContents();
    const publicImages=await card.locator('.out img').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('src')).filter(Boolean));
    for(let i=0;i<publicImages.length;i++){
      const src=publicImages[i];if(!src.startsWith('data:image/png;base64,'))continue;
      const folder=out+'/images';fs.mkdirSync(folder,{recursive:true});
      const filename=folder+'/'+id.replaceAll('/','-')+'-'+Date.now()+'-'+i+'.png';
      fs.writeFileSync(filename,Buffer.from(src.split(',')[1],'base64'));visibleImages.push(filename);
    }


 }
 const result={passed,feedback:msg,visible_output:visibleOutput,visible_prompt:visiblePrompt,visible_images:visibleImages};
 if(lesson==='test')result.score=await page.locator('#test-result').innerText();
 return result;
}
while(!fs.existsSync(w+'/stop-retest')){for(const f of fs.readdirSync(jobdir).filter(v=>v.endsWith('.job')).sort()){
const job=jobdir+'/'+f, rows=JSON.parse(fs.readFileSync(job)),answers=[];
for(const r of rows){let ans;try{ans=await grade(r);}catch(e){ans={browserError:String(e).slice(0,1800)}}
const id=r.question||r.lesson+'/'+r.task;
if(typeof ans.passed === 'boolean')fs.appendFileSync(log,JSON.stringify({at:new Date().toISOString(),id,...r,...ans})+'\n');answers.push({id,...ans});}
fs.writeFileSync(job+'.out.tmp',JSON.stringify(answers));fs.renameSync(job+'.out.tmp',job+'.out');fs.renameSync(job,job+'.done');}
await new Promise(s=>setTimeout(s,150));}await b.close();})().catch(e=>{console.error(e);process.exit(1)});
