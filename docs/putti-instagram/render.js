// Lager karusell-PNG-er (1080 × 1350) og bilder til reelen (1080 × 1920, 30 bilder/s) fra ferdig.html.
// node docs/putti-instagram/render.js <ut-mappe> [--bare-karusell]
const {chromium} = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const out = process.argv[2];
  fs.mkdirSync(path.join(out, 'frames'), {recursive: true});
  const b = await chromium.launch();
  const file = 'file://' + path.resolve(__dirname, 'ferdig.html');

  const p1 = await b.newPage({viewport: {width: 1400, height: 1200}, deviceScaleFactor: 4.5});
  await p1.goto(file);
  await p1.evaluate(() => document.fonts.ready);
  console.log('Bricolage lastet:', await p1.evaluate(() => document.fonts.check('800 20px "Bricolage Grotesque"')));
  for (let k = 1; k <= 5; k++) {
    await (await p1.$('#s' + k)).screenshot({path: path.join(out, `putti-karusell-${k}.png`)});
  }
  await p1.close();
  if (process.argv.includes('--bare-karusell')) { await b.close(); return; }

  const p2 = await b.newPage({viewport: {width: 600, height: 600}, deviceScaleFactor: 4});
  await p2.goto(file);
  await p2.evaluate(() => document.fonts.ready);
  const reel = await p2.$('#reel');
  const len = await p2.evaluate(() => window.reelLength);
  const fps = 30;
  for (let f = 0; f < len * fps; f++) {
    await p2.evaluate(t => window.renderAt(t), f / fps);
    await reel.screenshot({path: path.join(out, 'frames', String(f).padStart(4, '0') + '.png')});
  }
  await b.close();
})();
