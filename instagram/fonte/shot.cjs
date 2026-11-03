const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  for (const [f, w, h, out] of [['post.html', 1080, 1350, 'post.png'], ['capa.html', 1080, 1920, 'capa.png']]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto('file://' + __dirname + '/' + f);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(600);
    await p.screenshot({ path: __dirname + '/' + out });
  }
  await b.close();
})();
