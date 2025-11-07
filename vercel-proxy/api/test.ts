// Minimal test edge function
export const config = { runtime: 'edge' };

export default async function handler(req: Request) {
    return new Response(JSON.stringify({
        ok: true,
        message: 'Test endpoint working',
        url: req.url
    }), {
        status: 200,
        headers: { 'content-type': 'application/json' }
    });
}
