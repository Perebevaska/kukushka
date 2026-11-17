/* Browser score from the published HTML/JS. All requests terminate in this process. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const site = path.resolve('site');
const output = process.argv[2];
const core = ['c1', 'c2', 'c3', 'c16', 'c17'];
const html = fs.readFileSync(path.join(site, 'ch15/test.html'), 'utf8');
const keys = Object.fromEntries([...html.matchAll(/class="quiz-c" data-q="(c\d+)"([\s\S]*?)<\/ul>/g)].map(m => [m[1], [...m[2].matchAll(/<li>\s*(?:<p>)?\s*\[([x ])\]/g)].map(v => v[1]).indexOf('x')]));
if (Object.keys(keys).length !== 17 || Object.values(keys).includes(-1)) throw Error('Published quiz format changed');
(async () => {
 const browser = await chromium.launch();
 try {
  const cases = [];
  for (const [main, mistakes] of [[true,3], [false,4]]) {
   const ctx = await browser.newContext();
   await ctx.route('**/*', async route => {
    const url = new URL(route.request().url());
    const rel = url.pathname.slice(1);
    if (url.hostname !== 'course.invalid' || route.request().method() !== 'GET' ||
      !/^(ch15\/test\.html|assets\/(core\.js|lesson\.js|course\.js|app\.css))$/.test(rel)) {
      return route.fulfill({status:404, body:''});
    }
    await route.fulfill({path:path.join(site,rel)});
   });
   await ctx.addInitScript(v => localStorage.setItem('dsc-core-only', v ? '1' : '0'),main);
   const page = await ctx.newPage();
   await page.goto('http://course.invalid/ch15/test.html');
   await page.locator('.quiz-c .qopt').first().waitFor({state:'attached'});
   await page.locator('.test-questions summary').click();
   const snapshots = [];
   const snapshot = async stage => snapshots.push({stage, result:await page.locator('#test-result').innerText(), sidebar:await page.locator('[data-ctest="ch15"]').first().getAttribute('data-done')});
   const extra = Object.keys(keys).filter(q => !core.includes(q));
   const answer = async (q, correct) => {
    await page.locator('.quiz-c[data-q="'+q+'"] .qopt[data-i="'+(correct?keys[q]:(keys[q]+1)%4)+'"]').click();
   };
   const visible = await page.locator('.quiz-c:visible').count();
   await snapshot('initial');
   for (const q of core) await answer(q,true);
   await snapshot('all five core correct');
   for (const [idx,q] of extra.entries()) await answer(q,idx>=mistakes);
   await snapshot('all seventeen answered');
   cases.push({mode:await page.locator('body').evaluate(b=>b.classList.contains('core-only')?'core':'full'), visible, mistakes,snapshots});
   await ctx.close();
  }
  fs.writeFileSync(output, JSON.stringify(cases,null,2)+'\n');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
