const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('/Users/dmitriikormin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, 'frozen.json')));
const phase=process.argv[2]||'before';
const url=process.argv[3]||'http://127.0.0.1:55585/ch15/02-service.html';
(async()=>{
  const browser=await chromium.launch();
  const rows=[];
  async function visit(probes){
    const ctx=await browser.newContext(),page=await ctx.newPage();
    try {
      await page.goto(url);
      const full=page.getByRole('button',{name:'Весь урок на одной странице',exact:true});
      if(await full.count())await full.click();
      for(const [name,no] of probes){
        const card=page.locator('#task-handler'),editor=card.locator('.task-ui .CodeMirror').first();
        await editor.waitFor({state:'attached'});
        await editor.evaluate((el,code)=>el.CodeMirror.setValue(code),cases[no].code);
        if(await editor.evaluate(el=>el.CodeMirror.getValue())!==cases[no].code)throw Error('editor readback');
        const verdict=card.locator('.verdict').first();
        await verdict.evaluate(el=>{
          el.removeAttribute('data-finished');
          const observer=new MutationObserver(()=>{
            if(el.matches('.ok,.fail')){el.setAttribute('data-finished','1');observer.disconnect();}
          });
          observer.observe(el,{childList:true,attributes:true,attributeFilter:['class']});
        });
        await card.getByRole('button',{name:'Проверить',exact:true}).click();
        await card.locator('.verdict[data-finished]').waitFor({timeout:100000});
        rows.push({name,expected:cases[no].should_pass,pass:await verdict.evaluate(el=>el.matches('.ok')),
          message:await verdict.innerText(),output:await card.locator('.out').allTextContents()});
      }
    }finally{await ctx.close();}
  }
  try {
    if (process.argv[4]==='matrix') {
      await visit([['cold_literal_invalid',0]]);
      await visit([['cold_literal_fixed',1],['warm_literal_invalid',0],['warm_literal_fixed',1]]);
    } else if (process.argv[4]==='warm-fixed') {
      await visit([['warmup_with_correct_submission',1],['warm_literal_fixed',1]]);
    } else {
      await visit([['cold_literal_invalid',0]]);
      await visit([['cold_literal_fixed',1],['warm_literal_invalid',0]]);
    }
  }finally{
    fs.writeFileSync(path.join(__dirname,phase+'-cold-ui.json'),JSON.stringify({url,rows},null,2));
    await browser.close();
  }
})().catch(e=>{console.error(e);process.exit(1);});
