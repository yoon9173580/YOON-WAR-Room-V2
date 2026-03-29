const yahooFinance = require('yahoo-finance2').default;

// User's provided Databento Key as Fallback
const DATABENTO_KEY = 'db-3vQTNU4MucyxYXTsWUbGHSPJrUPf8';
const FINNHUB_KEY = process.env.FINNHUB_TOKEN || '';

// ==========================================
// [1] CRYPTO LAYERED REDUNDANCY
// ==========================================
async function fetchCrypto() {
  try {
    // Primary: CoinGecko (Safe Backend Poll)
    const cgRes = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true', { signal: AbortSignal.timeout(3000) });
    if(cgRes.ok) {
      const cg = await cgRes.json();
      if(cg && cg.bitcoin && cg.bitcoin.usd) {
        return { p: cg.bitcoin.usd, pct: cg.bitcoin.usd_24h_change || 0 };
      }
    }
    throw new Error('CoinGecko Timeout or Down');
  } catch (e) {
    // Secondary Backup: Binance Public API Stream
    try {
      const binData = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', { signal: AbortSignal.timeout(3000) });
      if(binData.ok) {
        const bd = await binData.json();
        return { p: parseFloat(bd.lastPrice), pct: parseFloat(bd.priceChangePercent) };
      }
    } catch(err2) {
      console.error('CRYPTO ALL OUTAGES:', err2.message);
    }
  }
  return { p: 0, pct: 0 }; // Absolute fallback to prevent UI crash
}

// ==========================================
// [2] CNN FEAR & GREED + ALTERNATIVE PROXY
// ==========================================
async function fetchFearGreed() {
  try {
    // Primary: CNN Live Graphdata
    const fetchCNN = await fetch('https://production.dataviz.cnn.io/index/fearandgreed/graphdata', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://edition.cnn.com/markets/fear-and-greed',
        'Accept': 'application/json'
      },
      signal: AbortSignal.timeout(3000)
    });
    if(fetchCNN.ok) {
        const cnnData = await fetchCNN.json();
        if(cnnData.fear_and_greed && cnnData.fear_and_greed.score) {
            return Math.round(cnnData.fear_and_greed.score).toString();
        }
    }
  } catch(e) {}
  
  // Secondary Backup: alternative.me Crypto F&G
  try {
    const fng = await fetch('https://api.alternative.me/fng/?limit=1', { signal: AbortSignal.timeout(3000) });
    const fngD = await fng.json();
    return fngD.data[0].value;
  } catch(err) {}
  return "--";
}

// ==========================================
// [3] DATABENTO REST API FALLBACK STUB
// ==========================================
async function fetchDatabento(sym) {
    const target = sym.replace('^', '');
    try {
      const url = `https://hist.databento.com/v0/timeseries.get_range?dataset=DBEQ.BASIC&schema=ohlcv-1m&symbols=${target}&limit=1`;
      const res = await fetch(url, {
          headers: {
              'Authorization': 'Basic ' + Buffer.from(DATABENTO_KEY + ':').toString('base64')
          }, 
          signal: AbortSignal.timeout(2000)
      });
      if(res.ok) {
          const dbData = await res.json();
          // If valid data is pulled from Databento, mock Yahoo Schema:
          // Format handling depends heavily on Databento JSON shaping
          return null; 
      }
    } catch(e) {}
    return null;
}

// ==========================================
// MAIN VERCEL HANDLER EXPORT
// ==========================================
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  const { symbols } = req.query;
  if (!symbols) return res.status(400).json({ error: 'Missing symbols parameter' });

  try {
    // Concurrently fetch all data streams to maintain <2s latency response
    const [stocksResult, cryptoResult, fearGreedResult] = await Promise.allSettled([
        (async () => {
            const symbolArray = symbols.split(',').map(s => s.trim()).filter(Boolean);
            let rs = [];
            if (symbolArray.length > 0) {
              try {
                // Tier 1: Bulk Optimized Query
                const quoteData = await yahooFinance.quote(symbolArray);
                rs = Array.isArray(quoteData) ? quoteData : [quoteData];
              } catch (bulkErr) {
                console.warn('Bulk fetch failed:', bulkErr.message);
                
                // Tier 2: Individual Resurrecting Fetch Logic
                const fetchPromises = symbolArray.map(async (sym) => {
                  try {
                    return await yahooFinance.quote(sym);
                  } catch (err) {
                    
                    // Tier 3: Finnhub API Redundancy
                    if(FINNHUB_KEY && !sym.includes('C000')) {
                        try {
                            const fh = await fetch(`https://finnhub.io/api/v1/quote?symbol=${sym}&token=${FINNHUB_KEY}`).then(r=>r.json());
                            if(fh && fh.c) {
                                return { symbol: sym, regularMarketPrice: fh.c, regularMarketChange: fh.d || 0, regularMarketChangePercent: fh.dp || 0 };
                            }
                        } catch(fherr) {}
                    }
                    
                    // Tier 4: Databento Extreme Fallback
                    if(!sym.includes('C000')) {
                        const dbRes = await fetchDatabento(sym);
                        if(dbRes) return dbRes;
                    }
                    return null;
                  }
                });
                const resArray = await Promise.all(fetchPromises);
                rs = resArray.filter(Boolean);
              }
            }
            return rs;
        })(),
        fetchCrypto(),
        fetchFearGreed()
    ]);

    // Fast output caching to CDN Layer
    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');
    
    // Distribute compiled unified JSON payload combining all multi-API assets
    return res.status(200).json({
      quoteResponse: { result: stocksResult.status === 'fulfilled' ? stocksResult.value : [] },
      crypto: cryptoResult.status === 'fulfilled' ? cryptoResult.value : { p: 0, pct: 0 },
      fear_greed: fearGreedResult.status === 'fulfilled' ? fearGreedResult.value : "--"
    });

  } catch (error) {
    console.error('API Orchestration Catastrophic Error:', error);
    return res.status(502).json({ error: error.message });
  }
};
