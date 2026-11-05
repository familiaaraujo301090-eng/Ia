import json
t = json.load(open('tempos.json'))
par = {}
for a, b, tx, p in t:
    par.setdefault(p, [a, b]); par[p][1] = b
plates = [{'t': 0.0 if p == 1 else round(par[p][0] - 0.3, 3)} for p in sorted(par)]
sents = [{'a': a, 'b': b, 'text': tx, 'p': p} for a, b, tx, p in t]
hit = next(s['a'] for s in sents if 'mais alto' in s['text']) - plates[2]['t']
dur = round(t[-1][1] + 1.8, 3)
open('timeline.js', 'w').write('window.TIMELINE = ' + json.dumps({'plates': plates, 'sents': sents, 'hit3': round(hit, 3), 'dur': dur}, ensure_ascii=False) + ';\n')
print(plates, hit, dur)
