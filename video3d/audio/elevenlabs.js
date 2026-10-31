// Gera a narração de cada cena com a API do ElevenLabs (text-to-speech com
// timestamps). Salva output/audio/<cena>.mp3 e <cena>.json com o tempo de cada
// palavra, usado pelo render para sincronizar as legendas e a duração das cenas.
//   ELEVENLABS_API_KEY=... node audio/elevenlabs.js roteiro/x.json
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const API = 'https://api.elevenlabs.io/v1';

function words(alignment) {
  const { characters: ch, character_start_times_seconds: st, character_end_times_seconds: en } = alignment;
  const out = [];
  let cur = null;
  ch.forEach((c, i) => {
    if (/\s/.test(c)) {
      if (cur) out.push(cur);
      cur = null;
    } else if (!cur) cur = { w: c, t0: st[i], t1: en[i] };
    else {
      cur.w += c;
      cur.t1 = en[i];
    }
  });
  if (cur) out.push(cur);
  return out;
}

async function main() {
  const roteiroPath = process.argv[2];
  const key = process.env.ELEVENLABS_API_KEY;
  if (!roteiroPath) throw new Error('uso: node audio/elevenlabs.js <roteiro.json>');
  if (!key) throw new Error('defina a variável de ambiente ELEVENLABS_API_KEY');
  const roteiro = JSON.parse(fs.readFileSync(roteiroPath, 'utf8'));
  const a = roteiro.audio;
  const voz = process.env.ELEVENLABS_VOICE_ID || a.vozId;
  const dir = path.join(__dirname, '..', 'output', 'audio');
  fs.mkdirSync(dir, { recursive: true });

  for (const cena of roteiro.cenas) {
    if (!cena.narracao) continue;
    const res = await fetch(`${API}/text-to-speech/${voz}/with-timestamps?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: { 'xi-api-key': key, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: cena.narracao,
        model_id: a.modelo,
        language_code: 'pt',
        voice_settings: { stability: a.estabilidade, similarity_boost: a.similaridade, style: a.estilo, use_speaker_boost: true },
      }),
    });
    if (!res.ok) throw new Error(`ElevenLabs ${res.status} na cena ${cena.id}: ${await res.text()}`);
    const data = await res.json();
    const mp3 = path.join(dir, `${cena.id}.mp3`);
    fs.writeFileSync(mp3, Buffer.from(data.audio_base64, 'base64'));
    const dur = parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3]).toString());
    fs.writeFileSync(path.join(dir, `${cena.id}.json`), JSON.stringify({ duracao: dur, palavras: words(data.alignment) }, null, 1));
    console.log(`${cena.id}: ${dur.toFixed(2)} s`);
  }
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
