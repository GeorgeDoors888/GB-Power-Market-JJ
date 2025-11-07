// Vercel Serverless Function proxy for Railway Codex
// Using Node.js runtime for process.env support
import type { VercelRequest, VercelResponse } from '@vercel/node';

const ALLOW = new Set<string>([
    '/health',
    '/query_bigquery_get', // GET with ?sql=
    '/query_bigquery',     // POST { sql: ... }
    '/run_stack_check'     // GET (your secured checker)
]);

function bad(res: VercelResponse, error: string, status = 400) {
    return res.status(status).json({ ok: false, error });
}

// OPTIONAL: basic SQL guard
function guardSelectOnly(sql: string) {
    const s = sql.trim().toLowerCase();
    if (!s.startsWith('select')) throw new Error('only SELECT statements allowed');
    if (s.includes(';')) throw new Error('multiple statements not allowed');
    if (sql.length > 5000) throw new Error('SQL too long');
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
    try {
        // Enable CORS
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', 'application/json');

        const RAILWAY_BASE = process.env.RAILWAY_BASE;
        const CODEX_TOKEN = process.env.CODEX_TOKEN;

        if (!RAILWAY_BASE) return bad(res, 'RAILWAY_BASE not set on proxy', 500);

        const path = (req.query.path as string) || '';
        if (!ALLOW.has(path)) return bad(res, 'path not allowed', 403);

        // Build target URL
        const targetUrl = new URL(RAILWAY_BASE + path);

        // Pass through GET query params (except 'path')
        if (req.method === 'GET') {
            for (const [key, value] of Object.entries(req.query)) {
                if (key !== 'path' && value) {
                    targetUrl.searchParams.set(key, String(value));
                }
            }
            // SQL guard for GET
            const sql = targetUrl.searchParams.get('sql') || '';
            if (sql && path === '/query_bigquery_get') {
                try {
                    guardSelectOnly(sql);
                } catch (e: any) {
                    return bad(res, e.message, 400);
                }
            }
        }

        // Prepare request to Railway
        const fetchOptions: RequestInit = {
            method: req.method,
            headers: {
                'content-type': (req.headers['content-type'] || 'application/json') as string,
                'authorization': `Bearer ${CODEX_TOKEN ?? ''}`,
            },
        };

        // Forward body for POST
        if (req.method === 'POST') {
            const bodyText = JSON.stringify(req.body);
            // SQL guard for POST
            if (path === '/query_bigquery' && req.body?.sql) {
                try {
                    guardSelectOnly(String(req.body.sql));
                } catch (e: any) {
                    return bad(res, e.message, 400);
                }
            }
            if (bodyText.length > 200_000) return bad(res, 'payload too large', 413);
            fetchOptions.body = bodyText;
        }

        const response = await fetch(targetUrl.toString(), fetchOptions);
        const text = await response.text();
        
        return res.status(response.status).send(text);
    } catch (e: any) {
        return bad(res, `error: ${e?.message || String(e)}`, 500);
    }
}
