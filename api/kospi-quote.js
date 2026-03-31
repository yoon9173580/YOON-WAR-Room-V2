// Vercel Serverless Function for KOSPI data
// This avoids CORS issues by proxying Finnhub API

const FINNHUB_API_KEY = process.env.FINNHUB_API_KEY || 'd75nmn9r01qk56kdec3gd75nmn9r01qk56kdec40';

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const response = await fetch(
      `https://finnhub.io/api/v1/quote?symbol=^KS11&token=${FINNHUB_API_KEY}`,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Finnhub API error: ${response.status}`);
    }

    const data = await response.json();

    // Check if we got valid data
    if (!data || !data.c) {
      return res.status(500).json({ 
        error: 'Invalid data from Finnhub',
        symbol: '^KS11'
      });
    }

    // Return formatted response matching Yahoo Finance format
    return res.status(200).json({
      symbol: '^KS11',
      regularMarketPrice: data.c,
      regularMarketChange: data.d || 0,
      regularMarketChangePercent: data.dp || 0,
      high: data.h,
      low: data.l,
      open: data.o,
      previousClose: data.pc,
      marketState: 'REGULAR',
      source: 'finnhub',
      timestamp: Date.now()
    });

  } catch (error) {
    console.error('[KOSPI API Error]', error);
    return res.status(500).json({
      error: error.message,
      symbol: '^KS11'
    });
  }
};
