// Vercel Serverless Function for KOSPI data
// Uses Yahoo Finance API (same as other stocks)

async function fetchYahooNative(sym) {
  try {
    const res = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1d&range=1d`, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.chart && data.chart.result && data.chart.result.length > 0) {
        const result = data.chart.result[0];
        const meta = result.meta;
        const price = meta.regularMarketPrice;
        const prev = meta.previousClose || meta.chartPreviousClose || price;
        const change = price - prev;
        const pct = prev > 0 ? (change / prev) * 100 : 0;
        return {
          symbol: sym,
          regularMarketPrice: price,
          regularMarketChange: change,
          regularMarketChangePercent: pct,
          marketState: meta.marketState || 'REGULAR'
        };
      }
    }
  } catch (e) {
    console.error('[Yahoo Error]', e);
  }
  return null;
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // Try different KOSPI symbols
    const symbols = ['^KS11', '^KOSPI', 'KS11.KS'];
    let data = null;
    
    for (const sym of symbols) {
      data = await fetchYahooNative(sym);
      if (data && data.regularMarketPrice > 0) {
        console.log(`[KOSPI] Found data with symbol: ${sym}`);
        data.symbol = '^KS11'; // Normalize symbol
        break;
      }
    }

    if (!data || data.regularMarketPrice <= 0) {
      return res.status(500).json({ 
        error: 'Could not fetch KOSPI data from Yahoo Finance',
        symbol: '^KS11'
      });
    }

    return res.status(200).json({
      symbol: '^KS11',
      regularMarketPrice: data.regularMarketPrice,
      regularMarketChange: data.regularMarketChange,
      regularMarketChangePercent: data.regularMarketChangePercent,
      marketState: data.marketState,
      source: 'yahoo',
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
