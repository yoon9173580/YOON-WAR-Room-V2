// Finnhub fallback for KOSPI and other Asian market indices.
// Used only when Yahoo Finance (the primary source, see yahoo-quote.js)
// fails entirely. Moved out of api/ - Vercel routes every api/*.js as a
// serverless function expecting a default handler export, but this module
// exports plain helpers, which made GET /api/kospi crash with a 500.

const FINNHUB_BASE_URL = 'https://finnhub.io/api/v1';
const KOSPI_SYMBOL = '^KS11';

function getToken() {
  return process.env.FINNHUB_TOKEN || null;
}

/**
 * Fetch KOSPI index data from Finnhub.
 * @returns {Promise<Object|null>}
 */
async function fetchKOSPIFromFinnhub() {
  const token = getToken();
  if (!token) return null;

  try {
    const url = `${FINNHUB_BASE_URL}/quote?symbol=${KOSPI_SYMBOL}&token=${token}`;
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } });
    if (!response.ok) throw new Error(`Finnhub API error: ${response.status}`);

    const data = await response.json();
    if (data && data.c) {
      return {
        symbol: KOSPI_SYMBOL,
        regularMarketPrice: data.c,
        regularMarketChange: data.d || 0,
        regularMarketChangePercent: data.dp || 0,
        high: data.h,
        low: data.l,
        open: data.o,
        previousClose: data.pc,
        marketState: 'REGULAR',
        source: 'finnhub'
      };
    }
    return null;
  } catch (error) {
    console.error('[Finnhub] Error fetching KOSPI:', error);
    return null;
  }
}

/**
 * Fetch multiple Asian market indices.
 * @returns {Promise<Array>}
 */
async function fetchAsianMarkets() {
  const token = getToken();
  if (!token) return [];

  const symbols = [
    { symbol: '^KS11', name: 'KOSPI' },
    { symbol: '^N225', name: 'Nikkei 225' },
    { symbol: '^HSI', name: 'Hang Seng' },
    { symbol: '^SSEC', name: 'Shanghai Composite' }
  ];

  const results = [];
  for (const { symbol, name } of symbols) {
    try {
      const url = `${FINNHUB_BASE_URL}/quote?symbol=${symbol}&token=${token}`;
      const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } });
      if (response.ok) {
        const data = await response.json();
        if (data && data.c) {
          results.push({
            symbol,
            name,
            regularMarketPrice: data.c,
            regularMarketChange: data.d || 0,
            regularMarketChangePercent: data.dp || 0,
            marketState: 'REGULAR',
            source: 'finnhub'
          });
        }
      }
    } catch (error) {
      console.error(`[Finnhub] Error fetching ${symbol}:`, error);
    }
  }
  return results;
}

module.exports = {
  fetchKOSPIFromFinnhub,
  fetchAsianMarkets,
  KOSPI_SYMBOL
};
