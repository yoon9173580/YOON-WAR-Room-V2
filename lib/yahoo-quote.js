/**
 * Shared Yahoo Finance quote logic.
 *
 * Used by api/quote.js, api/fetch-all.js, api/gme-price.js and
 * api/kospi-quote.js so market-data fetching lives in one place instead of
 * four slightly different copies (which is how /api/quote and
 * /api/kospi-quote ended up disagreeing on the KOSPI value).
 */

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

// The index itself first; KODEX ETFs are a fallback proxy only, tagged as
// such so callers/UI can tell the difference between the real KOSPI level
// and a KRW ETF share price.
const KOSPI_INDEX_SYMBOL = '^KS11';
const KOSPI_PROXY_SYMBOLS = ['069500.KS', '122630.KS', 'EWY'];

async function fetchWithTimeout(url, options = {}, limitMs = 5000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Fetch Timeout')), limitMs))
  ]);
}

/**
 * Fetch a single symbol's quote from Yahoo's chart endpoint.
 *
 * @param {string} symbol
 * @param {{extendedHours?: boolean}} opts - set extendedHours:false for
 *   instruments with no real pre/post session (indices, KRX proxies).
 *   Yahoo reports marketState:"POST" for KRX outside its own regular
 *   session even though KRX has no extended session, which previously
 *   zeroed the daily change once the POST-branch price override kicked in.
 * @throws on network failure / missing data - callers decide fallback.
 */
async function fetchYahooQuote(symbol, opts = {}) {
  const { extendedHours = true } = opts;
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1m&range=1d&includePrePost=true`;
  const res = await fetchWithTimeout(url, { headers: { 'User-Agent': UA } }, 5000);

  if (!res || !res.ok) {
    const err = new Error(`Yahoo chart ${symbol}: HTTP ${res ? res.status : 'no response'}`);
    err.status = res ? res.status : 502;
    throw err;
  }

  const data = await res.json();
  const result = data && data.chart && data.chart.result && data.chart.result[0];
  if (!result) {
    const err = new Error(`Yahoo chart ${symbol}: empty result`);
    err.status = 502;
    throw err;
  }

  const meta = result.meta;
  const price = meta.regularMarketPrice;
  if (price == null) {
    const err = new Error(`Yahoo chart ${symbol}: no price in response`);
    err.status = 502;
    throw err;
  }

  const prev = meta.previousClose || meta.chartPreviousClose || price;
  const change = price - prev;
  const pct = prev > 0 ? (change / prev) * 100 : 0;

  const out = {
    symbol,
    regularMarketPrice: price,
    regularMarketChange: change,
    regularMarketChangePercent: pct,
    marketState: meta.marketState || 'REGULAR'
  };

  if (!extendedHours) {
    out.marketState = 'REGULAR';
    return out;
  }

  const timestamps = result.timestamp || [];
  const closes = (result.indicators && result.indicators.quote && result.indicators.quote[0] && result.indicators.quote[0].close) || [];

  let preMarketPrice = meta.preMarketPrice || null;
  let postMarketPrice = meta.postMarketPrice || null;

  let regStart = 0, regEnd = 0;
  if (meta.currentTradingPeriod && meta.currentTradingPeriod.regular) {
    regStart = meta.currentTradingPeriod.regular.start;
    regEnd = meta.currentTradingPeriod.regular.end;
  }

  if (!postMarketPrice && regEnd > 0) {
    for (let i = timestamps.length - 1; i >= 0; i--) {
      if (timestamps[i] >= regEnd && closes[i] != null) { postMarketPrice = closes[i]; break; }
    }
  }
  if (!preMarketPrice && regStart > 0) {
    for (let i = timestamps.length - 1; i >= 0; i--) {
      if (timestamps[i] < regStart && closes[i] != null) { preMarketPrice = closes[i]; break; }
    }
  }

  const ms = meta.marketState || 'CLOSED';

  const postChange = postMarketPrice ? postMarketPrice - price : 0;
  const postPct = price > 0 ? (postChange / price) * 100 : 0;
  const preChange = preMarketPrice ? preMarketPrice - prev : 0;
  const prePct = prev > 0 ? (preChange / prev) * 100 : 0;

  out.preMarketPrice = preMarketPrice;
  out.preMarketChange = preChange;
  out.preMarketChangePercent = prePct;
  out.postMarketPrice = postMarketPrice;
  out.postMarketChange = postChange;
  out.postMarketChangePercent = postPct;
  out.marketState = ms;

  if (ms === 'CLOSED' || ms === 'POST') {
    if (postMarketPrice) {
      out.regularMarketPrice = postMarketPrice;
      out.regularMarketChange = postChange;
      out.regularMarketChangePercent = postPct;
    }
  } else if (ms === 'PRE' && preMarketPrice) {
    out.regularMarketPrice = preMarketPrice;
    out.regularMarketChange = preChange;
    out.regularMarketChangePercent = prePct;
  }

  return out;
}

/**
 * Resolve the KOSPI index. Tries the real index symbol first; falls back to
 * KODEX ETF proxies (tagged isProxy/proxySymbol) only if the index itself
 * is unavailable. Returns null if every source fails - callers decide
 * whether to try a non-Yahoo fallback or omit the symbol.
 */
async function fetchKOSPI() {
  try {
    const q = await fetchYahooQuote(KOSPI_INDEX_SYMBOL, { extendedHours: false });
    if (q && q.regularMarketPrice > 0) {
      return Object.assign(q, { symbol: KOSPI_INDEX_SYMBOL, source: 'yahoo:^KS11' });
    }
  } catch (e) { /* fall through to proxies */ }

  for (const proxySymbol of KOSPI_PROXY_SYMBOLS) {
    try {
      const q = await fetchYahooQuote(proxySymbol, { extendedHours: false });
      if (q && q.regularMarketPrice > 0) {
        return Object.assign(q, {
          symbol: KOSPI_INDEX_SYMBOL,
          isProxy: true,
          proxySymbol,
          source: `proxy:${proxySymbol}`
        });
      }
    } catch (e) { /* try next proxy */ }
  }

  return null;
}

async function fetchCrypto() {
  try {
    const res = await fetchWithTimeout('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true', {}, 3000);
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.bitcoin && data.bitcoin.usd) {
        return { p: data.bitcoin.usd, pct: data.bitcoin.usd_24h_change || 0 };
      }
    }
  } catch (e) { }

  try {
    const res = await fetchWithTimeout('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', {}, 3000);
    if (res && res.ok) {
      const data = await res.json();
      return { p: parseFloat(data.lastPrice), pct: parseFloat(data.priceChangePercent) };
    }
  } catch (e) { }

  return { p: null, pct: null };
}

async function fetchFearGreed() {
  try {
    const res = await fetchWithTimeout('https://production.dataviz.cnn.io/index/fearandgreed/graphdata', {
      headers: {
        'User-Agent': UA,
        'Referer': 'https://edition.cnn.com/markets/fear-and-greed',
        'Accept': 'application/json'
      }
    }, 3000);
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.fear_and_greed && data.fear_and_greed.score) {
        return Math.round(data.fear_and_greed.score).toString();
      }
    }
  } catch (e) { }

  try {
    const res = await fetchWithTimeout('https://api.alternative.me/fng/?limit=1', {}, 3000);
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.data && data.data[0]) return data.data[0].value;
    }
  } catch (e) { }

  return '--';
}

module.exports = {
  fetchWithTimeout,
  fetchYahooQuote,
  fetchKOSPI,
  fetchCrypto,
  fetchFearGreed,
  KOSPI_INDEX_SYMBOL,
  KOSPI_PROXY_SYMBOLS
};
