// Test the published score boundary and persisted answers in isolated contexts.
const fs = require('node:fs');
const {chromium} = require('/Users/dmitriikormin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
let browser;
(async () => {
  browser = await chromium.launch({headless: true});
  const keys = JSON.parse(fs.readFileSync('/private/tmp/kuch09round/keys-retest.json'));
  const rows = [];
  for (const n of [12, 13]) {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto('http://127.0.0.1:55579/ch09/test.html');
    const details = page.locator('details.test-questions');
    if (!await details.evaluate(e => e.open)) await details.locator('summary').click();
    const questions = page.locator('.quiz-c');
    if (await questions.count() !== 16) throw Error('Expected 16 questions');
    for (let i = 0; i < 16; i++) {
      const key = keys['test/quiz/' + (i + 1)];
      const right = key.original_order[key.answer - 1] - 1;
      const choice = i < n ? right : (right + 1) % 4;
      await questions.nth(i).locator('.qopt[data-i="' + choice + '"]').click();
    }
    const score = await page.locator('#test-result').innerText();
    if (!score.includes(n + ' из 16') || score.includes('глава усвоена') !== (n === 13)) throw Error(score);
    await page.reload();
    const reload = await page.locator('#test-result').innerText();
    if (reload !== score) throw Error('Score changed after reload');
    await page.locator('#test-result').screenshot({path: 'docs/reaudit-2026-11-16/ch09/technical/test-ui-' + n + '.png'});
    rows.push({correct: n, total: 16, passed: n === 13, score, reload_identical: true});
    await context.close();
  }
  fs.writeFileSync('docs/reaudit-2026-11-16/ch09/technical/test-ui.json', JSON.stringify(rows, null, 2) + '\n');
  console.log(JSON.stringify(rows));
  await browser.close();
})().catch(async e => { console.error(e); process.exitCode = 1; if (browser) await browser.close(); });
