/**
 * Aggregate market data API for the mobile dashboard.
 * Endpoint: /api/fetch-all - requires a Bearer session token (see api/auth.js).
 *
 * Response: { gme, aapl, nvda, tsla, btc, spy, vix, kospi, fear_greed,
 *             timestamp, returned }
 * `change` on each symbol is a percent (mobile.html appends '%' directly).
 * A symbol whose fetch failed is omitted entirely rather than zero-filled,
 * so the UI can tell "flat" from "unknown".
 */

const { fetchYahooQuote, fetchKOSPI, fetchCrypto, fetchFearGreed } = require('../lib/yahoo-quote');
const { verifySession, getBearerToken } = require('../lib/auth');

const SYMBOL_MAP = { gme: 'GME', aapl: 'AAPL', nvda: 'NVDA', tsla: 'TSLA', spy: 'SPY', vix: '^VIX' };

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const session = verifySession(getBearerToken(req));
    if (!session.valid) {
      return res.status(401).json({ error: session.reason || 'unauthorized' });
    }

    const keys = Object.keys(SYMBOL_MAP);
    const [settled, kospi, btc, fearGreed] = await Promise.all([
      Promise.allSettled(keys.map(k => fetchYahooQuote(SYMBOL_MAP[k]))),
      fetchKOSPI().catch(() => null),
      fetchCrypto().catch(() => ({ p: null, pct: null })),
      fetchFearGreed().catch(() => '--')
    ]);

    const result = {};
    let returned = 0;

    keys.forEach((k, i) => {
      const r = settled[i];
      if (r.status === 'fulfilled') {
        result[k] = { price: r.value.regularMarketPrice, change: r.value.regularMarketChangePercent };
        returned++;
      }
    });

    if (kospi) {
      result.kospi = { price: kospi.regularMarketPrice, change: kospi.regularMarketChangePercent };
      returned++;
    }
    if (btc && btc.p != null) {
      result.btc = { price: btc.p, change: btc.pct };
      returned++;
    }

    result.fear_greed = fearGreed;
    result.timestamp = new Date().toISOString();
    result.returned = returned;

    if (returned === 0) {
      return res.status(502).json({ error: 'All upstream sources failed', timestamp: result.timestamp });
    }

    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');
    return res.status(200).json(result);

  } catch (error) {
    console.error('[fetch-all] Handler Error:', error);
    return res.status(500).json({ error: String(error.message || error) });
  }
};
