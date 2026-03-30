const FINNHUB_KEY = process.env.FINNHUB_TOKEN || '';

async function fetchWithTimeout(url, options = {}, limitMs = 3000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Fetch Timeout')), limitMs))
  ]);
}

async function fetchCrypto() {
  try {
    const cgRes = await fetchWithTimeout('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true', {}, 3000);
    if (cgRes && cgRes.ok) {
      const cg = await cgRes.json();
      if (cg && cg.bitcoin && cg.bitcoin.usd) {
        return { p: cg.bitcoin.usd, pct: cg.bitcoin.usd_24h_change || 0 };
      }
    }
  } catch (e) { }

  try {
    const binData = await fetchWithTimeout('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', {}, 3000);
    if (binData && binData.ok) {
      const bd = await binData.json();
      return { p: parseFloat(bd.lastPrice), pct: parseFloat(bd.priceChangePercent) };
    }
  } catch (err2) { }

  return { p: 0, pct: 0 };
}

async function fetchFearGreed() {
  try {
    const cnnRes = await fetchWithTimeout('https://production.dataviz.cnn.io/index/fearandgreed/graphdata', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://edition.cnn.com/markets/fear-and-greed',
        'Accept': 'application/json'
      }
    }, 3000);
    if (cnnRes && cnnRes.ok) {
      const cnnData = await cnnRes.json();
      if (cnnData && cnnData.fear_and_greed && cnnData.fear_and_greed.score) {
        return Math.round(cnnData.fear_and_greed.score).toString();
      }
    }
  } catch (e) { }

  try {
    const fng = await fetchWithTimeout('https://api.alternative.me/fng/?limit=1', {}, 3000);
    if (fng && fng.ok) {
      const fngD = await fng.json();
      if (fngD && fngD.data && fngD.data[0]) return fngD.data[0].value;
    }
  } catch (err) { }
  return "--";
}

async function fetchYahooNative(sym) {
  try {
    const res = await fetchWithTimeout(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1m&range=1d&includePrePost=true`, { headers: { 'User-Agent': 'Mozilla/5.0' } }, 3000);
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.chart && data.chart.result && data.chart.result.length > 0) {
        const result = data.chart.result[0];
        const meta = result.meta;
        const timestamps = result.timestamp || [];
        const closes = (result.indicators.quote && result.indicators.quote.length > 0 && result.indicators.quote[0].close) ? result.indicators.quote[0].close : [];

        const price = meta.regularMarketPrice;
        const prev = meta.previousClose || meta.chartPreviousClose || price;
        const change = price - prev;
        const pct = prev > 0 ? (change / prev) * 100 : 0;

        let preMarketPrice = null;
        let postMarketPrice = null;

        let regStart = 0; let regEnd = 0;
        if (meta.currentTradingPeriod && meta.currentTradingPeriod.regular) {
          regStart = meta.currentTradingPeriod.regular.start;
          regEnd = meta.currentTradingPeriod.regular.end;
        }

        let lastTs = timestamps.length > 0 ? timestamps[timestamps.length - 1] : 0;
        let ms = "CLOSED";
        if (lastTs >= regEnd && regEnd > 0) ms = "POST";
        else if (lastTs < regStart && regStart > 0) ms = "PRE";
        else ms = "REGULAR";

        for (let i = timestamps.length - 1; i >= 0; i--) {
          if (timestamps[i] >= regEnd && closes[i] != null) { postMarketPrice = closes[i]; break; }
        }
        for (let i = timestamps.length - 1; i >= 0; i--) {
          if (timestamps[i] < regStart && closes[i] != null) { preMarketPrice = closes[i]; break; }
        }

        const postChange = postMarketPrice ? postMarketPrice - price : 0;
        const postPct = price > 0 ? (postChange / price) * 100 : 0;

        const preChange = preMarketPrice ? preMarketPrice - prev : 0;
        const prePct = prev > 0 ? (preChange / prev) * 100 : 0;

        return {
          symbol: sym,
          regularMarketPrice: price,
          regularMarketChange: change,
          regularMarketChangePercent: pct,
          preMarketPrice: preMarketPrice,
          preMarketChange: preChange,
          preMarketChangePercent: prePct,
          postMarketPrice: postMarketPrice,
          postMarketChange: postChange,
          postMarketChangePercent: postPct,
          marketState: ms
        };
      }
    }
  } catch (e) { }
  return null;
}

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const { symbols } = req.query;
    if (!symbols) return res.status(400).json({ error: 'Missing symbols parameter' });

    let stocksResult = [];
    let cryptoResult = { p: 0, pct: 0 };
    let fearGreedResult = "--";

    try {
      const symbolArray = symbols.split(',').map(s => s.trim()).filter(Boolean);
      if (symbolArray.length > 0) {
        const fetchPromises = symbolArray.map(async (sym) => {
          // 1. Core Native Fetch
          let q = await fetchYahooNative(sym);
          if (q) return q;

          // 2. Finnhub Redundancy
          if (FINNHUB_KEY && !sym.includes('C000')) {
            try {
              const fh = await fetchWithTimeout(`https://finnhub.io/api/v1/quote?symbol=${sym}&token=${FINNHUB_KEY}`, {}, 3000);
              if (fh && fh.ok) {
                const fhJson = await fh.json();
                if (fhJson && fhJson.c) {
                  return { symbol: sym, regularMarketPrice: fhJson.c, regularMarketChange: fhJson.d || 0, regularMarketChangePercent: fhJson.dp || 0 };
                }
              }
            } catch (fherr) { }
          }
          return null;
        });
        const resArray = await Promise.all(fetchPromises);
        stocksResult = resArray.filter(Boolean);
      }
    } catch (eStocks) {
      console.error("Stocks error", eStocks);
    }

    try { cryptoResult = await fetchCrypto(); } catch (eCrypt) { }
    try { fearGreedResult = await fetchFearGreed(); } catch (eFear) { }

    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');

    return res.status(200).json({
      quoteResponse: { result: stocksResult },
      crypto: cryptoResult,
      fear_greed: fearGreedResult,
      debug: "OK NATIVE"
    });

  } catch (error) {
    console.error('API Orchestration Catastrophic Error:', error);
    return res.status(200).json({ error: String(error.message || error) });
  }
};
