const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const ch = process.argv[2], site = path.resolve('site'), work = '/tmp/ku-audit/'+ch+'/';
if(!/^ch(0[2-9]|1[0-5])$/.test(ch)) throw Error('chapter');
const mapping=JSON.parse(fs.readFileSync(work+'choices.json'));
const read = f => fs.readFileSync(work+f, 'utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
async function main() {
  const server = http.createServer((req,res) => {
    const p = path.resolve(site,'.'+decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
    if(!['HEAD','GET'].includes(req.method) || !p.startsWith(site+path.sep) || !fs.statSync(p,{throwIfNoEntry:false})?.isFile()) {res.writeHead(404);res.end();return;}
    const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.wasm':'application/wasm','.json':'application/json','.svg':'image/svg+xml'};
    res.setHeader('Content-Type',mime[path.extname(p)] || 'application/octet-stream');
    if(req.method==='HEAD')res.end();else fs.createReadStream(p).pipe(res);
  });
  let browser;
  try {
    await new Promise((resolve,reject) => {server.on('error',reject);server.listen(0,'127.0.0.1',resolve);});
    browser=await chromium.launch({executablePath:process.env.CHROME_BIN || undefined,headless:true});
    const ctx=await browser.newContext();
    const base='http://127.0.0.1:'+server.address().port;
    await ctx.route('**/*', route=>route.request().url().startsWith(base+'/') ? route.continue() : route.abort());
    await ctx.addInitScript(()=>localStorage.setItem('dsc-onepage','1'));
    const page=await ctx.newPage(); page.setDefaultTimeout(14000);
    let inputs=read('submissions.jsonl'), qs=read('answers.jsonl');
    const order=fs.readFileSync(work+'student/order.txt','utf8').trim().split('\n').filter(l=>qs.some(x=>x.lesson===l)||inputs.some(x=>x.lesson===l));
    const results=[];
    for(const lesson of order){
      if(process.argv[3] && lesson!==process.argv[3]) continue;
      const batch=JSON.stringify([qs.filter(x=>x.lesson===lesson),inputs.filter(x=>x.lesson===lesson)]);
      const digest=require('node:crypto').createHash('sha256').update(batch).digest('hex');
      if(fs.existsSync(work+'replay-'+lesson+'.key') && fs.readFileSync(work+'replay-'+lesson+'.key','utf8')===digest)continue;
      await page.goto(base+'/'+ch+'/'+lesson+'.html');
      await page.waitForSelector('.task .bar, .quiz-opts', {state:'attached'});
      for(const q of qs.filter(x=>x.lesson===lesson)){
        const pred=q.kind==='predict', el=page.locator(pred?'.predict':'.quiz-c').nth(q.index-1);
        const choice=mapping[[lesson,q.kind,q.index].join('/')][q.choice-1];
        const opt=pred?el.locator('.popt').nth(choice-1):el.locator('.qopt[data-i="'+(choice-1)+'"]');
        await opt.evaluate(b=>b.click());
        results.push({...q,sourceChoice:choice,passed:await el.locator('.predict-res').evaluate(v=>v.classList.contains('ok'))});
      }
      for(const row of inputs.filter(x=>x.lesson===lesson)){
        const card=page.locator('#task-'+row.id);
        const uiCode=await card.evaluate((c,code)=>{
          const cm=c.querySelector('.CodeMirror');
          if(cm) cm.CodeMirror.setValue(code);
          else {
            const lines=code.split('\n').filter(l=>l.trim());
            const items=()=>[...c.querySelectorAll('.pline')];
            if(lines.length!==items().length)throw Error('Unrepresentable Parsons '+c.id);
            for(const [i,line] of lines.entries()){
              const ch02Compat=location.pathname.endsWith('/ch02/01-dataframe.html') && c.id==='task-p-sum' ||
                               location.pathname.endsWith('/ch02/02-select.html') && c.id==='task-p-loc';
              const form=s=>ch02Compat ? s.replace(/\s+/g,'').replaceAll("df.channel",'df["channel"]') : s.trim();
              let n=items().findIndex((e,j)=> j>=i && form(e.querySelector('code').textContent)===form(line));
              if(n===-1)throw Error('Unknown Parsons line '+c.id+' '+line);
              while(n>i)items()[n--].querySelector('[title="Выше"]').click();
              const ind=(line.length-line.trimStart().length)/4;
              const curr=Number(items()[i].style.getPropertyValue('--ind'));
              for(let k=0;k<Math.abs(ind-curr);k++)items()[i].querySelector(ind>curr?'[title="Больше отступ"]':'[title="Меньше отступ"]').click();
            }
          }
          c.querySelector('.verdict').className='verdict';
          c.querySelector('.bar .primary').click();
          return cm ? code : [...c.querySelectorAll('.pline')].map(e=>'    '.repeat(Number(e.style.getPropertyValue('--ind')))+e.querySelector('code').textContent).join('\n');
        },row.code);
        await page.waitForFunction(id=>{
          const c=document.getElementById('task-'+id);
          return c.querySelector('.verdict.ok,.verdict.fail,.out .error') && !c.querySelector('.out .status');
        }, row.id,{timeout:180000});
        const r=await card.evaluate(c=>({passed:!!c.querySelector('.verdict.ok'),message:c.querySelector('.out .error')?.textContent || c.querySelector('.verdict').textContent}));
        results.push({lesson,id:row.id,code:row.code,...(row.code.trim()!==uiCode.trim()?{uiCode}:{}),...r});
      }
      if(lesson==='exam-1'){
        await page.locator('#exam-finish button').first().evaluate(b=>b.click());
        await page.waitForSelector('#exam-finish .exam-score');
      }
      fs.writeFileSync(work+'browser-'+lesson+'.json',JSON.stringify(results.filter(x=>x.lesson===lesson)));
      fs.writeFileSync(work+'replay-'+lesson+'.key',digest);
      console.log(lesson, results.filter(x=>x.lesson===lesson).length);
    }
  } finally {if(browser)await browser.close();server.closeAllConnections();server.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1});
