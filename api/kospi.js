// Finnhub API for KOSPI and other Asian market data
// Free tier: 60 calls/minute

const FINNHUB_API_KEY = process.env.FINNHUB_API_KEY || 'd75nmn9r01qk56kdec3gd75nmn9r01qk56kdec40';
const FINNHUB_BASE_URL = 'https://finnhub.io/api/v1';

// KOSPI Index Symbol for Finnhub
const KOSPI_SYMBOL = '^KS11';

/**
 * Fetch KOSPI index data from Finnhub
 * @returns {Promise<Object>} KOSPI price and change data
 */
async function fetchKOSPIFromFinnhub() {
  try {
    // Fetch quote data
    const quoteUrl = `${FINNHUB_BASE_URL}/quote?symbol=${KOSPI_SYMBOL}&token=${FINNHUB_API_KEY}`;
    const response = await fetch(quoteUrl, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Finnhub API error: ${response.status}`);
    }

    const data = await response.json();

    // Finnhub returns: c (current), d (change), dp (change percent), h (high), l (low), o (open), pc (previous close)
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
        marketState: 'REGULAR', // KOSPI only trades during regular hours
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
 * Fetch multiple Asian market indices
 * @returns {Promise<Array>} Array of market data objects
 */
async function fetchAsianMarkets() {
  const symbols = [
    { symbol: '^KS11', name: 'KOSPI' },
    { symbol: '^N225', name: 'Nikkei 225' },
    { symbol: '^HSI', name: 'Hang Seng' },
    { symbol: '^SSEC', name: 'Shanghai Composite' }
  ];

  const results = [];

  for (const { symbol, name } of symbols) {
    try {
      const url = `${FINNHUB_BASE_URL}/quote?symbol=${symbol}&token=${FINNHUB_API_KEY}`;
      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' }
      });

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
