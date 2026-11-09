// Gera um único HTML autocontido com o app + backend simulado no navegador.
// Uso: node scripts/build-demo.mjs [saida.html]   (padrão: dist/rumo-demo.html)
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const out = path.resolve(process.argv[2] || path.join(root, 'dist', 'rumo-demo.html'));
const modules = ['server/time.js', 'server/launchPlan.js', 'server/demo.js', 'demo/mock-api.js', 'public/js/util.js', 'public/js/app.js'];

function mustReplace(src, from, to) {
  if (!src.includes(from)) throw new Error(`Trecho não encontrado: ${from.slice(0, 60)}`);
  return src.replace(from, to);
}

function bundle(file) {
  let src = fs.readFileSync(path.join(root, file), 'utf8');
  const name = path.basename(file, '.js');
  src = src.replace(/^import \{([^}]+)\} from '([^']+)';$/gm, (_, names, from) => `const {${names}} = __m['${path.basename(from, '.js')}'];`);
  src = src.replace(/^import \* as (\w+) from '([^']+)';$/gm, (_, n, from) => `const ${n} = __m['${path.basename(from, '.js')}'];`);
  if (/^import /m.test(src)) throw new Error(`Import não suportado em ${file}`);
  const names = [];
  src = src.replace(/^export (async function|function|const) ([\w$]+)/gm, (_, kind, n) => { names.push(n); return `${kind} ${n}`; });
  return `// ---- ${file} ----\n(() => {\n${src}\n__m['${name}'] = { ${names.join(', ')} };\n})();\n`;
}

let js = `const process = { env: {} };\nconst __m = {};\n${modules.map(bundle).join('\n')}`;
// Ajustes só da versão de teste
js = mustReplace(js, "if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});", '');
js = mustReplace(js, '<a class="btn" href="/api/export">Baixar meus dados</a>', '');
js = mustReplace(js, '<input id="a-email" type="email" required autocomplete="email">', '<input id="a-email" type="email" required autocomplete="email" value="teste@rumo.app">');
js = mustReplace(js, '<input id="a-pass" type="password" required minlength="6" autocomplete="current-password">', '<input id="a-pass" type="password" required minlength="6" autocomplete="current-password" value="rumo123">');
js = mustReplace(js, '<div class="auth-tabs">',
  '<div class="banner" style="margin:14px 0 0">Versão de teste: a conta <b>teste@rumo.app</b> já está preenchida. É só tocar em <b>Entrar</b>. A IA responde com exemplos e seus dados ficam só neste navegador.</div><div class="auth-tabs">');
js = mustReplace(js, "IA em <b>modo demonstração</b>. Para respostas reais, configure <code>ANTHROPIC_API_KEY</code> no servidor (veja o README).",
  '<b>Versão de teste.</b> A IA responde com exemplos prontos. Na versão publicada com a chave da Anthropic, as respostas são personalizadas para você.');
js = js.replaceAll('href="#/entrar/criar"', 'href="#/entrar"'); // na versão de teste a conta já existe
if (js.includes('</script')) throw new Error('O bundle contém </script>');

const css = fs.readFileSync(path.join(root, 'public/css/app.css'), 'utf8');
const html = `<title>Rumo</title>
<meta name="description" content="Metas, agenda, ideias e legendas com IA.">
<style>
${css}
</style>
<div id="app"></div>
<div id="toast" role="status" aria-live="polite"></div>
<script>
${js}
</script>
`;
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, html);
console.log(`Gerado ${out} (${(html.length / 1024).toFixed(0)} KB)`);
