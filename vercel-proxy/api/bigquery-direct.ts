import { NextRequest, NextResponse } from 'next/server';
import { BigQuery } from '@google-cloud/bigquery';

export const config = {
  runtime: 'edge',
};

/**
 * Direct BigQuery Proxy for Google Sheets Apps Script
 * 
 * Queries inner-cinema-476211-u9.uk_energy_prod directly
 * Bypasses Railway backend that's configured for wrong project
 */
export default async function handler(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const sql = searchParams.get('sql');

    if (!sql) {
      return NextResponse.json(
        { success: false, error: 'Missing sql parameter' },
        { status: 400 }
      );
    }

    // Service account credentials from environment
    const credentials = JSON.parse(process.env.GOOGLE_CREDENTIALS || '{}');
    
    const bigquery = new BigQuery({
      projectId: 'inner-cinema-476211-u9',
      credentials,
    });

    const [rows] = await bigquery.query({
      query: sql,
      location: 'europe-west2',
    });

    return NextResponse.json({
      success: true,
      data: rows,
      row_count: rows.length,
      error: null,
      timestamp: new Date().toISOString(),
    });

  } catch (error: any) {
    console.error('BigQuery Error:', error);
    return NextResponse.json(
      {
        success: false,
        data: null,
        row_count: null,
        error: error.message || 'Query execution failed',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
