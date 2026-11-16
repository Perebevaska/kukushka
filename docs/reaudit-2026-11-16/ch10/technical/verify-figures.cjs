const fs = require('node:fs');
const {chromium} = require('/Users/dmitriikormin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
let browser;
(async () => {
  browser = await chromium.launch({headless: true});
  const page = await browser.newPage({viewport: {width: 1100, height: 900}});
  for (const name of ['adam-first', 'trend-trap']) {
    const lesson = name === 'adam-first' ? '02b-optimizers' : '05-project';
    await page.goto('http://127.0.0.1:55580/ch10/' + lesson + '.html');
    const fullLesson = page.getByRole('button', {name: 'Весь урок на одной странице', exact: true});
    if (await fullLesson.count()) await fullLesson.click();
    await page.locator('figure[data-fig="' + name + '"]').screenshot({path: 'docs/reaudit-2026-11-16/ch10/technical/figure-' + name + '.png'});
  }
  await browser.close();
  console.log('Rendered both updated figures.');
})().catch(async e => { console.error(e); process.exitCode = 1; if (browser) await browser.close(); });
