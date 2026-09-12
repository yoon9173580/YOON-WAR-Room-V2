const { fetchYahooQuote, fetchKOSPI, fetchCrypto, fetchFearGreed, fetchWithTimeout } = require('../lib/yahoo-quote');
const { fetchKOSPIFromFinnhub } = require('../lib/kospi');

async function resolveSymbol(sym) {
  if (sym === '^KS11' || sym === 'KOSPI') {
    const kospi = await fetchKOSPI();
    if (kospi) return kospi;

    const fh = await fetchKOSPIFromFinnhub().catch(() => null);
    if (fh) return fh;

    throw new Error('KOSPI unavailable from all sources');
  }

  try {
    return await fetchYahooQuote(sym);
  } catch (yahooErr) {
    const token = process.env.FINNHUB_TOKEN;
    if (token && !sym.includes('C000')) {
      const fhRes = await fetchWithTimeout(`https://finnhub.io/api/v1/quote?symbol=${sym}&token=${token}`, {}, 3000).catch(() => null);
      if (fhRes && fhRes.ok) {
        const fhJson = await fhRes.json();
        if (fhJson && fhJson.c) {
          return { symbol: sym, regularMarketPrice: fhJson.c, regularMarketChange: fhJson.d || 0, regularMarketChangePercent: fhJson.dp || 0, marketState: 'REGULAR' };
        }
      }
    }
    throw yahooErr;
  }
}

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') return res.status(200).end();

    const { symbols } = req.query;
    const symbolArray = (symbols || '').split(',').map(s => s.trim()).filter(Boolean);
    if (symbolArray.length === 0) {
      return res.status(400).json({ error: 'Missing symbols parameter' });
    }

    const settled = await Promise.allSettled(symbolArray.map(resolveSymbol));
    const stocksResult = settled.filter(r => r.status === 'fulfilled').map(r => r.value);
    const failedSymbols = symbolArray.filter((_, i) => settled[i].status === 'rejected');

    if (stocksResult.length === 0) {
      return res.status(502).json({ error: 'All upstream quote sources failed', symbols: symbolArray });
    }

    const [cryptoResult, fearGreedResult] = await Promise.all([
      fetchCrypto().catch(() => ({ p: null, pct: null })),
      fetchFearGreed().catch(() => '--')
    ]);

    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');
    return res.status(200).json({
      quoteResponse: { result: stocksResult },
      crypto: cryptoResult,
      fear_greed: fearGreedResult,
      failedSymbols
    });

  } catch (error) {
    console.error('[quote] Handler Error:', error);
    return res.status(500).json({ error: String(error.message || error) });
  }
};
