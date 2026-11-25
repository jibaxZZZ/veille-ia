// Vérifie le changement de type annoncé : tenir la promesse de setPermissionMode comme Promise<void>.
import { query } from '@anthropic-ai/claude-agent-sdk';
const q = query({ prompt: 'x' });
const p: Promise<void> = q.setPermissionMode('plan');
const r = await q.setPermissionMode('plan');
const m: string | undefined = r?.mode;
export { p, m };
