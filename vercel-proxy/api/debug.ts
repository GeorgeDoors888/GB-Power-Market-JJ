import type { VercelRequest, VercelResponse } from '@vercel/node';
import fetch from 'node-fetch';

export default async function handler(req: VercelRequest, res: VercelResponse) {
    try {
        const RAILWAY_BASE = process.env.RAILWAY_BASE;
        const CODEX_TOKEN = process.env.CODEX_TOKEN;

        // Return debug info
        return res.status(200).json({
            ok: true,
            hasRailwayBase: !!RAILWAY_BASE,
            hasCodexToken: !!CODEX_TOKEN,
            railwayBaseLength: RAILWAY_BASE?.length || 0,
            method: req.method,
            query: req.query,
            nodeVersion: process.version,
            fetchAvailable: typeof fetch !== 'undefined'
        });
    } catch (e: any) {
        return res.status(500).json({
            ok: false,
            error: e.message,
            stack: e.stack
        });
    }
}
