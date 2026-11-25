// usage: node perm.mjs <dossier version> ; mode streaming contre le faux serveur (port 18951) :
// 1) setPermissionMode sur 4 modes et affiche la valeur résolue ou le rejet ; 2) prompt '/sonde' avec un hook PreSkillShellCommand en callback SDK qui refuse.
const dir = process.argv[2];
const { query } = await import(`${dir}/node_modules/@anthropic-ai/claude-agent-sdk/sdk.mjs`);
const env = { PATH: '/opt/node22/bin:/usr/bin:/bin', HOME: '/tmp/veille-work-2026-11-25/sdk/home', ANTHROPIC_BASE_URL: 'http://127.0.0.1:18951', ANTHROPIC_API_KEY: 'fausse-cle-test', CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1' };
let done; const gate = new Promise(r => done = r);
async function* input() { yield { type: 'user', message: { role: 'user', content: '/sonde' }, parent_tool_use_id: null }; await gate; }
const hookCalls = [];
const q = query({ prompt: input(), options: { env, cwd: '/tmp/veille-work-2026-11-25/cc/proj', model: 'claude-opus-4-8', settingSources: ['project'],
  hooks: { PreSkillShellCommand: [{ hooks: [async (inp) => { hookCalls.push({ ev: inp.hook_event_name, cmd: inp.tool_input?.command, name: inp.command_name });
    return { hookSpecificOutput: { hookEventName: 'PreSkillShellCommand', permissionDecision: 'deny', permissionDecisionReason: 'REFUS-SDK-VEILLE' } }; }] }] } } });
for (const m of ['plan', 'acceptEdits', 'bypassPermissions', 'bogus']) {
  try { const r = await q.setPermissionMode(m); console.log(`setPermissionMode(${m}) -> résolu ${JSON.stringify(r)}`); }
  catch (e) { console.log(`setPermissionMode(${m}) -> rejeté: ${String(e.message).slice(0, 160)}`); }
}
for await (const msg of q) {
  if (msg.type === 'result') { console.log(`result: subtype=${msg.subtype} result=${JSON.stringify(msg.result)}`); done(); break; }
}
console.log('appels du hook SDK:', JSON.stringify(hookCalls));
