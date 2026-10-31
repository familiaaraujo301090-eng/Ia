// Renderizador headless: abre o motor (engine/) no Chromium via Playwright,
// avança o tempo quadro a quadro e envia os JPEGs direto para o ffmpeg.
//   node render.js roteiro/x.json            -> output/<nome>.mp4
//   node render.js roteiro/x.json --sheets   -> output/sheets/*.png
//   node render.js roteiro/x.json --preview  -> output/preview/*.jpg (1 por cena)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = __dirname;
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.json': 'application/json' };

function serve() {
  const server = http.createServer((req, res) => {
    const file = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((r) => server.listen(0, '127.0.0.1', () => r(server)));
}

const decode = (dataUrl) => Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');

async function main() {
  const [roteiroPath, mode] = process.argv.slice(2);
  if (!roteiroPath) throw new Error('uso: node render.js <roteiro.json> [--sheets|--preview]');
  const roteiro = JSON.parse(fs.readFileSync(path.resolve(roteiroPath), 'utf8'));
  const name = path.basename(roteiroPath, '.json');
  const server = await serve();
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 400, height: 400 } });
  page.on('console', (m) => console.log('[browser]', m.text()));
  page.on('pageerror', (e) => console.error('[browser error]', e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/engine/index.html`);
  await page.waitForFunction(() => window.ready === true);
  const info = await page.evaluate((r) => window.setup(r), roteiro);
  console.log(`roteiro "${roteiro.titulo}": ${info.total.toFixed(1)} s, chegada em x=${info.finishX.toFixed(1)}`);

  const outDir = path.join(ROOT, 'output');
  if (mode === '--sheets') {
    fs.mkdirSync(path.join(outDir, 'sheets'), { recursive: true });
    for (const s of ['personagem', 'cenario', 'storyboard']) {
      const file = path.join(outDir, 'sheets', `${name}_${s}.png`);
      fs.writeFileSync(file, decode(await page.evaluate((n) => window.sheet(n), s)));
      console.log('sheet ->', path.relative(ROOT, file));
    }
  } else if (mode === '--preview') {
    fs.mkdirSync(path.join(outDir, 'preview'), { recursive: true });
    for (const [id, a, b] of info.cenas) {
      for (const k of [0.25, 0.7]) {
        const file = path.join(outDir, 'preview', `${id}_${k}.jpg`);
        fs.writeFileSync(file, decode(await page.evaluate((t) => window.frame(t), a + (b - a) * k)));
      }
    }
    console.log('preview -> output/preview');
  } else {
    const { fps } = roteiro.formato;
    const frames = Math.round(info.total * fps);
    const file = path.join(outDir, `${name}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', file], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < frames; i++) {
      const buf = decode(await page.evaluate((t) => window.frame(t), i / fps));
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if (i % 30 === 0) process.stdout.write(`\rquadro ${i}/${frames} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    console.log(`\nvídeo -> ${path.relative(ROOT, file)}`);
  }
  await browser.close();
  server.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
