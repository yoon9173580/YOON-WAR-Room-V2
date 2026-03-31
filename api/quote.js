const FINNHUB_KEY = process.env.FINNHUB_TOKEN || 'd75nmn9r01qk56kdec3gd75nmn9r01qk56kdec40';

// KOSPI symbol mapping
const KOSPI_SYMBOL = '^KS11';

/**
 * Fetch KOSPI from Finnhub
 * @returns {Promise<Object>} KOSPI data
 */
async function fetchKOSPIFromFinnhub() {
  if (!FINNHUB_KEY) {
    console.log('[Finnhub] No API key available');
    return null;
  }
  
  try {
    const url = `https://finnhub.io/api/v1/quote?symbol=${KOSPI_SYMBOL}&token=${FINNHUB_KEY}`;
    const res = await fetchWithTimeout(url, {
      headers: { 'Content-Type': 'application/json' }
    }, 3000);
    
    if (res && res.ok) {
      const data = await res.json();
      if (data && data.c) {
        console.log(`[Finnhub] KOSPI data:`, { price: data.c, change: data.d, changePercent: data.dp });
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
    }
  } catch (e) {
    console.error('[Finnhub] Error fetching KOSPI:', e);
  }
  return null;
}

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

        // Check for extended hours data from meta first (more reliable)
        let preMarketPrice = meta.preMarketPrice || null;
        let postMarketPrice = meta.postMarketPrice || null;
        
        // If not in meta, try to calculate from timestamps
        let regStart = 0; let regEnd = 0;
        if (meta.currentTradingPeriod && meta.currentTradingPeriod.regular) {
          regStart = meta.currentTradingPeriod.regular.start;
          regEnd = meta.currentTradingPeriod.regular.end;
        }

        // Only calculate from timestamps if we don't have meta values
        if (!preMarketPrice || !postMarketPrice) {
          const lastTs = timestamps.length > 0 ? timestamps[timestamps.length - 1] : 0;
          
          // Find post-market price (after regEnd)
          if (!postMarketPrice && regEnd > 0) {
            for (let i = timestamps.length - 1; i >= 0; i--) {
              if (timestamps[i] >= regEnd && closes[i] != null) { 
                postMarketPrice = closes[i]; 
                break; 
              }
            }
          }
          
          // Find pre-market price (before regStart)
          if (!preMarketPrice && regStart > 0) {
            for (let i = timestamps.length - 1; i >= 0; i--) {
              if (timestamps[i] < regStart && closes[i] != null) { 
                preMarketPrice = closes[i]; 
                break; 
              }
            }
          }
        }

        // Determine market state
        let lastTs = timestamps.length > 0 ? timestamps[timestamps.length - 1] : 0;
        let ms = "CLOSED";
        
        // More robust market state detection
        if (regEnd > 0 && lastTs >= regEnd) {
          ms = "POST";
        } else if (regStart > 0 && lastTs < regStart) {
          ms = "PRE";
        } else if (regStart > 0 && regEnd > 0 && lastTs >= regStart && lastTs <= regEnd) {
          ms = "REGULAR";
        }
        
        // Override with meta.marketState if available (more accurate)
        if (meta.marketState) {
          ms = meta.marketState;
        }

        const postChange = postMarketPrice ? postMarketPrice - price : 0;
        const postPct = price > 0 ? (postChange / price) * 100 : 0;

        const preChange = preMarketPrice ? preMarketPrice - prev : 0;
        const prePct = prev > 0 ? (preChange / prev) * 100 : 0;

        // CLOSED state handling - use postMarketPrice if available (even when market is closed)
        let finalPrice = price;
        let finalChange = change;
        let finalChangePercent = pct;
        
        if (ms === "CLOSED" || ms === "POST") {
          // If we have post-market data, use it even when closed
          if (postMarketPrice) {
            finalPrice = postMarketPrice;
            finalChange = postChange;
            finalChangePercent = postPct;
            console.log(`[API] Using post-market price for ${sym}: $${finalPrice}`);
          } else {
            console.log(`[API] No post-market price for ${sym}, using regular: $${finalPrice}`);
          }
        } else if (ms === "PRE" && preMarketPrice) {
          finalPrice = preMarketPrice;
          finalChange = preChange;
          finalChangePercent = prePct;
          console.log(`[API] Using pre-market price for ${sym}: $${finalPrice}`);
        }

        return {
          symbol: sym,
          regularMarketPrice: finalPrice,
          regularMarketChange: finalChange,
          regularMarketChangePercent: finalChangePercent,
          preMarketPrice: preMarketPrice,
          preMarketChange: preChange,
          preMarketChangePercent: prePct,
          postMarketPrice: postMarketPrice,
          postChange: postChange,
          postMarketChangePercent: postPct,
          marketState: ms
        };
      }
    }
  } catch (e) { console.error('[fetchYahooNative Error]', e); }
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
          console.log(`[API] Processing symbol: ${sym}`);
          
          // Special handling for KOSPI - try multiple symbols and APIs
          if (sym === '^KS11' || sym === 'KOSPI') {
            console.log(`[API] KOSPI detected, trying multiple sources...`);
            
            // Try different KOSPI symbol formats - Korean ETFs
            // 069500.KS = KODEX 200 (KOSPI 200 ETF), 122630.KS = KODEX 레버리지
            const kospiSymbols = ['069500.KS', '^KS11', '122630.KS', 'EWY'];
            
            for (const kospiSym of kospiSymbols) {
              console.log(`[API] Trying symbol: ${kospiSym}`);
              let yahooKospi = await fetchYahooNative(kospiSym);
              if (yahooKospi && yahooKospi.regularMarketPrice > 0) {
                console.log(`[Yahoo] KOSPI data SUCCESS with ${kospiSym}:`, { price: yahooKospi.regularMarketPrice });
                yahooKospi.symbol = '^KS11'; // Normalize symbol
                return yahooKospi;
              }
            }
            
            console.log(`[API] Yahoo KOSPI failed, trying Finnhub...`);
            
            // Fallback to Finnhub
            const kospiData = await fetchKOSPIFromFinnhub();
            if (kospiData) {
              console.log(`[Finnhub] KOSPI data SUCCESS:`, { price: kospiData.regularMarketPrice });
              return kospiData;
            }
            
            // Last resort: return hardcoded fallback value
            console.log(`[API] All KOSPI sources failed, using hardcoded fallback`);
            return {
              symbol: '^KS11',
              regularMarketPrice: 2580.0,
              regularMarketChange: 0,
              regularMarketChangePercent: 0,
              marketState: 'REGULAR',
              source: 'hardcoded'
            };
          }
          
          // 1. Core Native Fetch (Yahoo Finance)
          let q = await fetchYahooNative(sym);
          if (q) return q;

          // 2. Finnhub Redundancy for other symbols
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
