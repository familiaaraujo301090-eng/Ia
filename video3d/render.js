// Renderizador headless: abre o motor (engine/) no Chromium via Playwright,
// avança o tempo quadro a quadro e envia os JPEGs direto para o ffmpeg.
//   node render.js roteiro/x.json            -> output/<nome>.mp4
//   node render.js roteiro/x.json --sheets   -> output/sheets/*.png
//   node render.js roteiro/x.json --preview  -> output/preview/*.jpg (2 por cena)
//   node render.js roteiro/x.json --mix      -> refaz só o áudio do vídeo final
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');
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

// Narração: usa o áudio do ElevenLabs (output/audio/<cena>.mp3 + .json) quando
// existe; senão estima o tempo de cada palavra. A cena cresce para caber a fala.
function prepararNarracao(roteiro, audioDir) {
  let narrada = false;
  for (const c of roteiro.cenas) {
    if (!c.narracao) continue;
    const meta = path.join(audioDir, `${c.id}.json`);
    let dur, palavras;
    if (fs.existsSync(meta) && fs.existsSync(path.join(audioDir, `${c.id}.mp3`))) {
      ({ duracao: dur, palavras } = JSON.parse(fs.readFileSync(meta, 'utf8')));
      c.audio = true;
      narrada = true;
    } else {
      const ws = c.narracao.split(/\s+/);
      const chars = ws.reduce((a, w) => a + w.length + 1, 0);
      dur = chars / 16;
      let t = 0;
      palavras = ws.map((w) => {
        const d = (dur * (w.length + 1)) / chars;
        const p = { w, t0: t, t1: t + d * 0.9 };
        t += d + (/[.,!?:]$/.test(w) ? 0.12 : 0);
        return p;
      });
      dur = t;
    }
    c.palavras = palavras;
    c.duracao = Math.max(c.duracao, dur + 0.25 + 0.4);
  }
  return narrada;
}

function mixarAudio(roteiro, info, audioDir, narrada, video, final) {
  const a = roteiro.audio || {};
  const byId = Object.fromEntries(info.cenas.map(([id, ini, fim]) => [id, { inicio: ini, fim }]));
  const chegada = roteiro.cenas.find((c) => c.acao === 'chegada');
  const fim = roteiro.cenas.find((c) => c.logoFinal);
  const timeline = {
    total: info.total,
    bpm: a.bpm || 124,
    cenas: info.cenas.map(([id, inicio, f]) => ({ id, inicio, fim: f })),
    fitaT: chegada ? byId[chegada.id].inicio + 0.28 * chegada.duracao : info.total - 5,
    logoT: fim ? byId[fim.id].inicio + 0.75 : info.total - 3,
  };
  fs.mkdirSync(audioDir, { recursive: true });
  const tl = path.join(audioDir, 'timeline.json');
  fs.writeFileSync(tl, JSON.stringify(timeline, null, 1));
  execFileSync('python3', [path.join(ROOT, 'audio', 'trilha.py'), '--info', tl, '--out', audioDir], { stdio: 'inherit' });

  const inputs = ['-i', video, '-i', path.join(audioDir, 'musica.wav'), '-i', path.join(audioDir, 'efeitos.wav')];
  const vozes = [];
  if (narrada) {
    roteiro.cenas.filter((c) => c.audio).forEach((c) => {
      inputs.push('-i', path.join(audioDir, `${c.id}.mp3`));
      vozes.push(Math.round((byId[c.id].inicio + 0.25) * 1000));
    });
  }
  let fc = `[1:a]volume=${narrada ? 0.55 : 0.9}[mus];[2:a]volume=1.0[sfx]`;
  if (vozes.length) {
    vozes.forEach((ms, i) => (fc += `;[${3 + i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay=${ms}|${ms},volume=1.6[v${i}]`));
    fc += `;${vozes.map((_, i) => `[v${i}]`).join('')}amix=inputs=${vozes.length}:normalize=0,asplit[voz][sc]`;
    fc += `;[mus][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[musd]`;
    fc += `;[musd][sfx][voz]amix=inputs=3:normalize=0[mix]`;
  } else {
    fc += `;[mus][sfx]amix=inputs=2:normalize=0[mix]`;
  }
  fc += `;[mix]loudnorm=I=-14:TP=-1.5:LRA=11[out]`;
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', fc, '-map', '0:v', '-map', '[out]',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-shortest', '-movflags', '+faststart', final], { stdio: 'inherit' });
}

const decode = (dataUrl) => Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');

async function main() {
  const [roteiroPath, mode] = process.argv.slice(2);
  if (!roteiroPath) throw new Error('uso: node render.js <roteiro.json> [--sheets|--preview]');
  const roteiro = JSON.parse(fs.readFileSync(path.resolve(roteiroPath), 'utf8'));
  const name = path.basename(roteiroPath, '.json');
  const audioDir = path.join(ROOT, 'output', 'audio');
  const narrada = prepararNarracao(roteiro, audioDir);
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
  } else if (mode === '--mix') {
    // só refaz o áudio sobre o vídeo já renderizado (ex.: depois de npm run audio, se a duração não mudou)
    const file = path.join(outDir, `${name}.mp4`);
    mixarAudio(roteiro, info, audioDir, narrada, file, path.join(outDir, `${name}_viral.mp4`));
    console.log('áudio remixado');
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
    console.log(`\nvídeo (sem som) -> ${path.relative(ROOT, file)}`);
    const final = path.join(outDir, `${name}_viral.mp4`);
    mixarAudio(roteiro, info, audioDir, narrada, file, final);
    console.log(`vídeo final com áudio -> ${path.relative(ROOT, final)}`);
  }
  await browser.close();
  server.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
