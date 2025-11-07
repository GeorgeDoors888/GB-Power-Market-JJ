// Vercel Serverless Function proxy for Railway Codex
// Using Node.js runtime instead of edge for better env var support

const ALLOW = new Set<string>([
    '/health',
    '/query_bigquery_get', // GET with ?sql=
    '/query_bigquery',     // POST { sql: ... }
    '/run_stack_check'     // GET (your secured checker)
]);

const JSONH = { 'content-type': 'application/json', 'access-control-allow-origin': '*' };

function bad(error: string, status = 400) {
    return new Response(JSON.stringify({ ok: false, error }), { status, headers: JSONH });
}

// OPTIONAL: basic SQL guard (uncomment to enforce)
function guardSelectOnly(sql: string) {
    const s = sql.trim().toLowerCase();
    if (!s.startsWith('select')) throw new Error('only SELECT statements allowed');
    if (s.includes(';')) throw new Error('multiple statements not allowed');
    if (sql.length > 5000) throw new Error('SQL too long');
}

export default async function handler(req: Request) {
    try {
        const RAILWAY_BASE = process.env.RAILWAY_BASE;
        const CODEX_TOKEN = process.env.CODEX_TOKEN;

        if (!RAILWAY_BASE) return bad('RAILWAY_BASE not set on proxy', 500);

        const incoming = new URL(req.url);
        const path = incoming.searchParams.get('path') || '';
        if (!ALLOW.has(path)) return bad('path not allowed', 403);

        // Build target URL
        const target = new URL(RAILWAY_BASE + path);

        // Pass through GET query params (except 'path')
        if (req.method === 'GET') {
            for (const [k, v] of incoming.searchParams.entries()) {
                if (k !== 'path') target.searchParams.set(k, v);
            }
            // OPTIONAL: SQL guard for GET
            const sql = target.searchParams.get('sql') || '';
            if (sql && path === '/query_bigquery_get') {
                try {
                    guardSelectOnly(sql);
                } catch (e: any) {
                    return bad(e.message, 400);
                }
            }
        }

        // Prepare request to Railway
        const init: RequestInit = {
            method: req.method,
            headers: {
                'content-type': req.headers.get('content-type') || 'application/json',
                'authorization': `Bearer ${CODEX_TOKEN ?? ''}`,
            },
        };

        // Forward body for POST
        if (req.method === 'POST') {
            const bodyText = await req.text();
            // OPTIONAL: SQL guard for POST
            if (path === '/query_bigquery') {
                try {
                    const body = JSON.parse(bodyText || '{}');
                    if (body?.sql) guardSelectOnly(String(body.sql));
                } catch (e: any) {
                    if (e.message.includes('SELECT')) return bad(e.message, 400);
                    // Ignore parse errors, let Railway handle them
                }
            }
            if (bodyText.length > 200_000) return bad('payload too large', 413);
            init.body = bodyText;
        }

        const r = await fetch(target.toString(), init);
        const text = await r.text();
        return new Response(text, { status: r.status, headers: { ...JSONH } });
    } catch (e: any) {
        return bad(`error: ${e?.message || String(e)}`, 500);
    }
}

// OPTIONAL: HMAC signing helper (uncomment to use)
// async function verifyHmac(sql: string, sig: string, key: string) {
//   if (!sig) return false;
//   const enc = new TextEncoder();
//   const cryptoKey = await crypto.subtle.importKey(
//     'raw', enc.encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
//   );
//   const mac = await crypto.subtle.sign('HMAC', cryptoKey, enc.encode(sql));
//   const macB64 = btoa(String.fromCharCode(...new Uint8Array(mac))).replace(/=+$/,'');
//   return macB64 === sig;
// }
