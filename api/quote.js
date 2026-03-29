let initError = null;
let yahooFinance;
try {
  yahooFinance = require('yahoo-finance2').default;
} catch (e) {
  initError = e.message || String(e);
}

const DATABENTO_KEY = 'db-3vQTNU4MucyxYXTsWUbGHSPJrUPf8';
const FINNHUB_KEY = process.env.FINNHUB_TOKEN || '';

// Safe fetch with manual timeout to avoid AbortSignal compatibility issues
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
  } catch (e) {}

  try {
    const binData = await fetchWithTimeout('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', {}, 3000);
    if (binData && binData.ok) {
      const bd = await binData.json();
      return { p: parseFloat(bd.lastPrice), pct: parseFloat(bd.priceChangePercent) };
    }
  } catch(err2) {}
  
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
  } catch(e) {}
  
  try {
    const fng = await fetchWithTimeout('https://api.alternative.me/fng/?limit=1', {}, 3000);
    if (fng && fng.ok) {
      const fngD = await fng.json();
      if (fngD && fngD.data && fngD.data[0]) return fngD.data[0].value;
    }
  } catch(err) {}
  return "--";
}

async function fetchDatabento(sym) {
    const target = sym.replace('^', '');
    try {
      const url = `https://hist.databento.com/v0/timeseries.get_range?dataset=DBEQ.BASIC&schema=ohlcv-1m&symbols=${target}&limit=1`;
      const res = await fetchWithTimeout(url, {
          headers: {
              'Authorization': 'Basic ' + Buffer.from(DATABENTO_KEY + ':').toString('base64')
          }
      }, 2000);
      if (res && res.ok) {
          const dbData = await res.json();
          // Fallback parsing would go here, leaving as null since format is unknown
          return null; 
      }
    } catch(e) {}
    return null;
}

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    if (initError) {
      return res.status(200).json({ error: "Init Error: " + initError });
    }

    const { symbols } = req.query;
    if (!symbols) return res.status(400).json({ error: 'Missing symbols parameter' });

    let stocksResult = [];
    let cryptoResult = { p: 0, pct: 0 };
    let fearGreedResult = "--";

    try {
        const symbolArray = symbols.split(',').map(s => s.trim()).filter(Boolean);
        if (symbolArray.length > 0) {
          try {
            const quoteData = await yahooFinance.quote(symbolArray);
            stocksResult = Array.isArray(quoteData) ? quoteData : [quoteData];
          } catch (bulkErr) {
            const fetchPromises = symbolArray.map(async (sym) => {
              try {
                return await yahooFinance.quote(sym);
              } catch (err) {
                if (FINNHUB_KEY && !sym.includes('C000')) {
                    try {
                        const fh = await fetchWithTimeout(`https://finnhub.io/api/v1/quote?symbol=${sym}&token=${FINNHUB_KEY}`, {}, 3000);
                        if (fh && fh.ok) {
                          const fhJson = await fh.json();
                          if(fhJson && fhJson.c) {
                              return { symbol: sym, regularMarketPrice: fhJson.c, regularMarketChange: fhJson.d || 0, regularMarketChangePercent: fhJson.dp || 0 };
                          }
                        }
                    } catch(fherr) {}
                }
                
                if (!sym.includes('C000')) {
                    const dbRes = await fetchDatabento(sym);
                    if(dbRes) return dbRes;
                }
                return null;
              }
            });
            const resArray = await Promise.all(fetchPromises);
            stocksResult = resArray.filter(Boolean);
          }
        }
    } catch (eStocks) {
        console.error("Stocks error", eStocks);
    }

    try {
      cryptoResult = await fetchCrypto();
    } catch (eCrypt) {}

    try {
      fearGreedResult = await fetchFearGreed();
    } catch (eFear) {}

    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');
    
    return res.status(200).json({
      quoteResponse: { result: stocksResult },
      crypto: cryptoResult,
      fear_greed: fearGreedResult,
      debug: "OK"
    });

  } catch (error) {
    console.error('API Orchestration Catastrophic Error:', error);
    // Force 200 return to avoid Vercel 500 override, so frontend can see error
    return res.status(200).json({ error: String(error.message || error) });
  }
};
