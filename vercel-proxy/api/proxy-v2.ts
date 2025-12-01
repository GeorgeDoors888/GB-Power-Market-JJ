export const config = { runtime: 'edge' };

export default async function handler(req: Request): Promise<Response> {
    const RAILWAY_BASE = 'https://jibber-jabber-production.up.railway.app';
    const CODEX_TOKEN = 'codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA';

    try {
        const url = new URL(req.url);
        const path = url.searchParams.get('path') || '';

        const ALLOW = ['/health', '/query_bigquery_get', '/query_bigquery', '/run_stack_check', 
                       '/sheets_health', '/sheets_list', '/sheets_read', '/sheets_write'];
        if (!ALLOW.includes(path)) {
            return new Response(JSON.stringify({ ok: false, error: 'path not allowed' }), {
                status: 403,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const targetUrl = new URL(RAILWAY_BASE + path);
        for (const [key, value] of url.searchParams.entries()) {
            if (key !== 'path') targetUrl.searchParams.set(key, value);
        }

        const response = await fetch(targetUrl.toString(), {
            method: req.method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CODEX_TOKEN}`,
            },
            body: req.method !== 'GET' ? await req.text() : undefined,
        });

        return new Response(await response.text(), {
            status: response.status,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });
    } catch (e: any) {
        return new Response(JSON.stringify({ ok: false, error: e.message }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}
