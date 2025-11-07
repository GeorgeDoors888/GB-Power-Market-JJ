// Vercel Edge Runtime proxy for Railway Codex - optimized for ChatGPT
export const config = {
  runtime: 'edge',
};

const ALLOW = new Set<string>([
    '/health',
    '/query_bigquery_get',
    '/query_bigquery',
    '/run_stack_check'
]);

export default async function handler(req: Request) {
    try {
        const url = new URL(req.url);
        const path = url.searchParams.get('path') || '';
        
        if (!ALLOW.has(path)) {
            return new Response(JSON.stringify({ ok: false, error: 'path not allowed' }), {
                status: 403,
                headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
            });
        }

        // Environment variables in Edge Runtime
        const RAILWAY_BASE = process.env.RAILWAY_BASE;
        const CODEX_TOKEN = process.env.CODEX_TOKEN;

        if (!RAILWAY_BASE) {
            return new Response(JSON.stringify({ ok: false, error: 'RAILWAY_BASE not configured' }), {
                status: 500,
                headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
            });
        }

        // Build target URL
        const targetUrl = new URL(RAILWAY_BASE + path);
        
        // Copy query params except 'path'
        for (const [key, value] of url.searchParams.entries()) {
            if (key !== 'path') {
                targetUrl.searchParams.set(key, value);
            }
        }

        // Prepare headers
        const headers: Record<string, string> = {
            'Content-Type': req.headers.get('Content-Type') || 'application/json',
            'Authorization': `Bearer ${CODEX_TOKEN}`,
        };

        // Make request to Railway
        const railwayResponse = await fetch(targetUrl.toString(), {
            method: req.method,
            headers,
            body: req.method !== 'GET' ? await req.text() : undefined,
        });

        const responseText = await railwayResponse.text();

        return new Response(responseText, {
            status: railwayResponse.status,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            }
        });

    } catch (e: any) {
        return new Response(JSON.stringify({ 
            ok: false, 
            error: e.message || String(e)
        }), {
            status: 500,
            headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
        });
    }
}
