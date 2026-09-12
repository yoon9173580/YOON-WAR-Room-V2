/**
 * Aggregate market data API for the mobile dashboard
 * Endpoint: /api/fetch-all
 * Returns a flat object keyed by lowercase ticker: { price, change }
 */

async function fetchWithTimeout(url, options = {}, limitMs = 5000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Fetch Timeout')), limitMs))
  ]);
}

async function fetchYahooQuote(symbol) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1m&range=1d`;
    const res = await fetchWithTimeout(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' }
    }, 5000);

    if (!res || !res.ok) return null;

    const data = await res.json();
    const meta = data?.chart?.result?.[0]?.meta;
    if (!meta || meta.regularMarketPrice == null) return null;

    const price = meta.regularMarketPrice;
    const prev = meta.previousClose || meta.chartPreviousClose || price;
    const change = prev > 0 ? ((price - prev) / prev) * 100 : 0;

    return { price, change };
  } catch (e) {
    console.error(`[fetch-all] Yahoo error for ${symbol}:`, e);
    return null;
  }
}

async function fetchBTC() {
  try {
    const res = await fetchWithTimeout('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true', {}, 5000);
    if (res && res.ok) {
      const data = await res.json();
      if (data?.bitcoin?.usd) {
        return { price: data.bitcoin.usd, change: data.bitcoin.usd_24h_change || 0 };
      }
    }
  } catch (e) { }

  try {
    const res = await fetchWithTimeout('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', {}, 5000);
    if (res && res.ok) {
      const data = await res.json();
      return { price: parseFloat(data.lastPrice), change: parseFloat(data.priceChangePercent) };
    }
  } catch (e) { }

  return { price: 0, change: 0 };
}

const SYMBOL_MAP = { gme: 'GME', aapl: 'AAPL', nvda: 'NVDA', tsla: 'TSLA', spy: 'SPY', vix: '^VIX' };

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const keys = Object.keys(SYMBOL_MAP);
    const [quotes, btc] = await Promise.all([
      Promise.all(keys.map(k => fetchYahooQuote(SYMBOL_MAP[k]))),
      fetchBTC()
    ]);

    const result = {};
    keys.forEach((k, i) => {
      result[k] = quotes[i] || { price: 0, change: 0 };
    });
    result.btc = btc;
    result.timestamp = new Date().toISOString();

    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');
    return res.status(200).json(result);

  } catch (error) {
    console.error('[fetch-all] Handler Error:', error);
    return res.status(200).json({ error: String(error.message || error) });
  }
};
