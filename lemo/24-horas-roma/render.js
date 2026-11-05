// node render.js <saida> [t0 t1 passo] : renderiza quadros JPEG via Chromium sem cabeça
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const out = process.argv[2] || 'frames';
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', (e) => { console.error('ERRO NA PÁGINA:', e.message); process.exit(1); });
  await p.goto('http://127.0.0.1:8765/index.html');
  await p.waitForFunction(() => window.READY === true, null, { timeout: 600000 });
  const dur = await p.evaluate(() => window.DUR);
  fs.writeFileSync('events.json', JSON.stringify(await p.evaluate(() => ({ dur: window.DUR, ev: window.EV }))));
  const fps = 24;
  const list = process.argv[3] ? process.argv.slice(3).map(Number) : null;
  const times = list && list.length ? list : Array.from({ length: Math.ceil(dur * fps) }, (_, i) => i / fps);
  const t0 = Date.now();
  for (let k = 0; k < times.length; k++) {
    await p.evaluate((t) => window.render(t), times[k]);
    const name = list ? `t${times[k].toFixed(2)}.jpg` : `${String(k).padStart(5, '0')}.jpg`;
    await p.screenshot({ path: path.join(out, name), type: 'jpeg', quality: 92 });
    if (k % 100 === 0) console.log(k, '/', times.length, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await b.close();
})();
