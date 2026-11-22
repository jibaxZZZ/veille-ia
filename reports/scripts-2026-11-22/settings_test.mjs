// usage: node settings_test.mjs <dossier version> <cas> ; cas = badjson | badfield | badfile | ok
import { createRequire } from 'module';
const [dir, cas] = process.argv.slice(2);
const require = createRequire(dir + "/package.json");
const { query } = await import(dir + '/sdk.mjs');
const pkg = require(dir + '/package.json');
console.log('claude-agent-sdk', pkg.version, '| cas:', cas);
const settings = cas.startsWith('str:') ? cas.slice(4) : { badjson: '{"permissions": {"allow": [', badfield: { permissions: { defaultMode: 'pas-un-mode' } }, badfile: undefined, ok: { permissions: { allow: [] } } }[cas];
const opts = { model: 'claude-opus-4-8', maxTurns: 1, cwd: process.env.PROJ, settingSources: ['project'] };
if (settings !== undefined) opts.settings = settings;
const t0 = Date.now();
try {
  for await (const m of query({ prompt: 'dis bonjour', options: opts })) {
    if (m.type === 'system' && m.subtype !== 'init') console.log('system/' + m.subtype, (process.env.FULL ? JSON.stringify(m) : JSON.stringify(m).slice(0, 300)));
    if (m.type === 'assistant') console.log('assistant:', m.message.content.map(c => c.text).join(''));
    if (m.type === 'result') console.log('result:', m.subtype, JSON.stringify(m.result ?? m.errors ?? '').slice(0, 160));
  }
  console.log('fin normale en', Date.now() - t0, 'ms');
} catch (e) { console.log('EXCEPTION:', e.constructor.name, String(e.message).slice(0, 240), '| après', Date.now() - t0, 'ms'); }
