/**
 * Google Sheets API Proxy for ChatGPT Access
 * 
 * Enables ChatGPT to read and write to Google Sheets via Vercel Edge Function
 * 
 * Endpoints:
 * - GET  /api/sheets?action=read&sheet=Dashboard&range=A1:Z100
 * - POST /api/sheets?action=write&sheet=Dashboard&range=A1:B10
 * - GET  /api/sheets?action=get_sheets (list all sheets)
 * - GET  /api/sheets?action=health (health check)
 * 
 * Author: George Major
 * Date: 1 December 2025
 */

export const config = { runtime: 'edge' };

// Google Sheets configuration
const SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc';

// Environment helper for Edge runtime
declare const process: { env: Record<string, string | undefined> };

// Service account credentials (from inner-cinema-credentials.json)
// NOTE: In production, these should be stored as Vercel environment variables
function getServiceAccount() {
    return {
        type: "service_account",
        project_id: "inner-cinema-476211-u9",
        private_key_id: process.env.GOOGLE_PRIVATE_KEY_ID,
        private_key: process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
        client_email: process.env.GOOGLE_CLIENT_EMAIL,
        client_id: process.env.GOOGLE_CLIENT_ID,
        auth_uri: "https://accounts.google.com/o/oauth2/auth",
        token_uri: "https://oauth2.googleapis.com/token",
        auth_provider_x509_cert_url: "https://www.googleapis.com/oauth2/v1/certs",
    };
}

interface SheetReadRequest {
    action: 'read';
    sheet: string;
    range: string;
}

interface SheetWriteRequest {
    action: 'write';
    sheet: string;
    range: string;
    values: any[][];
}

interface SheetGetSheetsRequest {
    action: 'get_sheets';
}

interface SheetHealthRequest {
    action: 'health';
}

type SheetRequest = SheetReadRequest | SheetWriteRequest | SheetGetSheetsRequest | SheetHealthRequest;

/**
 * Generate JWT for Google API authentication
 */
async function generateJWT(): Promise<string> {
    const SERVICE_ACCOUNT = getServiceAccount();
    
    if (!SERVICE_ACCOUNT.private_key || !SERVICE_ACCOUNT.client_email) {
        throw new Error('Google service account credentials not configured');
    }

    const now = Math.floor(Date.now() / 1000);
    const claim = {
        iss: SERVICE_ACCOUNT.client_email,
        scope: 'https://www.googleapis.com/auth/spreadsheets',
        aud: 'https://oauth2.googleapis.com/token',
        exp: now + 3600,
        iat: now,
    };

    // Create JWT header
    const header = {
        alg: 'RS256',
        typ: 'JWT',
    };

    // Encode header and claim
    const encoder = new TextEncoder();
    const headerB64 = btoa(JSON.stringify(header)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const claimB64 = btoa(JSON.stringify(claim)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const message = `${headerB64}.${claimB64}`;

    // Sign with private key
    const privateKey = await crypto.subtle.importKey(
        'pkcs8',
        pemToBinary(SERVICE_ACCOUNT.private_key),
        {
            name: 'RSASSA-PKCS1-v1_5',
            hash: 'SHA-256',
        },
        false,
        ['sign']
    );

    const signature = await crypto.subtle.sign(
        'RSASSA-PKCS1-v1_5',
        privateKey,
        encoder.encode(message)
    );

    const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signature)))
        .replace(/=/g, '')
        .replace(/\+/g, '-')
        .replace(/\//g, '_');

    return `${message}.${signatureB64}`;
}

/**
 * Convert PEM private key to binary format
 */
function pemToBinary(pem: string): ArrayBuffer {
    const b64 = pem
        .replace(/-----BEGIN PRIVATE KEY-----/, '')
        .replace(/-----END PRIVATE KEY-----/, '')
        .replace(/\s/g, '');
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

/**
 * Get OAuth2 access token
 */
async function getAccessToken(): Promise<string> {
    const jwt = await generateJWT();

    const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            assertion: jwt,
        }),
    });

    if (!response.ok) {
        throw new Error(`Failed to get access token: ${response.statusText}`);
    }

    const data = await response.json();
    return data.access_token;
}

/**
 * Read data from Google Sheets
 */
async function readSheet(
    accessToken: string,
    sheetName: string,
    range: string
): Promise<any[][]> {
    const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${sheetName}!${range}`;

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });

    if (!response.ok) {
        throw new Error(`Failed to read sheet: ${response.statusText}`);
    }

    const data = await response.json();
    return data.values || [];
}

/**
 * Write data to Google Sheets
 */
async function writeSheet(
    accessToken: string,
    sheetName: string,
    range: string,
    values: any[][]
): Promise<void> {
    const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${sheetName}!${range}?valueInputOption=RAW`;

    const response = await fetch(url, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ values }),
    });

    if (!response.ok) {
        throw new Error(`Failed to write sheet: ${response.statusText}`);
    }
}

/**
 * Get list of all sheets in the spreadsheet
 */
async function getSheetsList(accessToken: string): Promise<string[]> {
    const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}`;

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
        },
    });

    if (!response.ok) {
        throw new Error(`Failed to get sheets list: ${response.statusText}`);
    }

    const data = await response.json();
    return data.sheets.map((sheet: any) => sheet.properties.title);
}

/**
 * Main handler
 */
export default async function handler(req: Request): Promise<Response> {
    try {
        const url = new URL(req.url);
        const action = url.searchParams.get('action');

        // Health check
        if (action === 'health') {
            return new Response(
                JSON.stringify({
                    status: 'healthy',
                    spreadsheet_id: SPREADSHEET_ID,
                    actions: ['read', 'write', 'get_sheets', 'health'],
                    timestamp: new Date().toISOString(),
                }),
                {
                    status: 200,
                    headers: {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    },
                }
            );
        }

        // Validate action
        if (!action || !['read', 'write', 'get_sheets'].includes(action)) {
            return new Response(
                JSON.stringify({
                    error: 'Invalid action',
                    allowed_actions: ['read', 'write', 'get_sheets', 'health'],
                }),
                {
                    status: 400,
                    headers: { 'Content-Type': 'application/json' },
                }
            );
        }

        // Get access token
        const accessToken = await getAccessToken();

        // Handle different actions
        if (action === 'get_sheets') {
            const sheets = await getSheetsList(accessToken);
            return new Response(
                JSON.stringify({
                    spreadsheet_id: SPREADSHEET_ID,
                    sheets,
                    count: sheets.length,
                }),
                {
                    status: 200,
                    headers: {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    },
                }
            );
        }

        if (action === 'read') {
            const sheet = url.searchParams.get('sheet');
            const range = url.searchParams.get('range');

            if (!sheet || !range) {
                return new Response(
                    JSON.stringify({
                        error: 'Missing required parameters',
                        required: ['sheet', 'range'],
                    }),
                    {
                        status: 400,
                        headers: { 'Content-Type': 'application/json' },
                    }
                );
            }

            const values = await readSheet(accessToken, sheet, range);
            return new Response(
                JSON.stringify({
                    spreadsheet_id: SPREADSHEET_ID,
                    sheet,
                    range,
                    values,
                    row_count: values.length,
                }),
                {
                    status: 200,
                    headers: {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    },
                }
            );
        }

        if (action === 'write') {
            const sheet = url.searchParams.get('sheet');
            const range = url.searchParams.get('range');

            if (!sheet || !range) {
                return new Response(
                    JSON.stringify({
                        error: 'Missing required parameters',
                        required: ['sheet', 'range'],
                    }),
                    {
                        status: 400,
                        headers: { 'Content-Type': 'application/json' },
                    }
                );
            }

            if (req.method !== 'POST') {
                return new Response(
                    JSON.stringify({
                        error: 'Write action requires POST method',
                    }),
                    {
                        status: 405,
                        headers: { 'Content-Type': 'application/json' },
                    }
                );
            }

            const body = await req.json();
            const values = body.values;

            if (!values || !Array.isArray(values)) {
                return new Response(
                    JSON.stringify({
                        error: 'Missing or invalid values array in request body',
                    }),
                    {
                        status: 400,
                        headers: { 'Content-Type': 'application/json' },
                    }
                );
            }

            await writeSheet(accessToken, sheet, range, values);
            return new Response(
                JSON.stringify({
                    success: true,
                    spreadsheet_id: SPREADSHEET_ID,
                    sheet,
                    range,
                    rows_written: values.length,
                }),
                {
                    status: 200,
                    headers: {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    },
                }
            );
        }

        return new Response(
            JSON.stringify({ error: 'Unknown error' }),
            {
                status: 500,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    } catch (error: any) {
        console.error('Sheets API error:', error);
        return new Response(
            JSON.stringify({
                error: error.message,
                stack: error.stack,
            }),
            {
                status: 500,
                headers: { 'Content-Type': 'application/json' },
            }
        );
    }
}
