/**
 * GME Implied Volatility API
 * Fetches GME options chain from Yahoo Finance and extracts IV data
 * Endpoint: /api/gme-iv
 */

async function fetchWithTimeout(url, options = {}, limitMs = 5000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Fetch Timeout')), limitMs))
  ]);
}

/**
 * Fetch GME options chain from Yahoo Finance
 * Returns the IV of the nearest ATM options
 */
async function fetchGMEOptionsIV() {
  try {
    // Yahoo Finance options endpoint - gets full options chain
    const url = 'https://query1.finance.yahoo.com/v7/finance/options/GME';
    const res = await fetchWithTimeout(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    }, 5000);

    if (!res || !res.ok) {
      console.error('[GME-IV] Yahoo options request failed:', res?.status);
      return null;
    }

    const data = await res.json();
    
    if (!data?.optionChain?.result?.[0]) {
      console.error('[GME-IV] No option chain data returned');
      return null;
    }

    const result = data.optionChain.result[0];
    const quote = result.quote;
    const currentPrice = quote?.regularMarketPrice || 0;
    const options = result.options?.[0];
    
    if (!options || !currentPrice) {
      console.error('[GME-IV] Missing options or price data');
      return null;
    }

    // Get expiration dates available
    const expirationDates = result.expirationDates || [];
    const currentExpiry = options.expirationDate;

    // Find ATM (At The Money) options - closest strike to current price
    const calls = options.calls || [];
    const puts = options.puts || [];

    // Calculate average IV from near-the-money options
    const ivData = calculateAverageIV(calls, puts, currentPrice);

    // Get IV percentile context
    const ivLevel = getIVLevel(ivData.avgIV);

    return {
      symbol: 'GME',
      currentPrice: currentPrice,
      iv: ivData.avgIV,                    // Average IV (decimal, e.g., 0.85 = 85%)
      ivPercent: (ivData.avgIV * 100).toFixed(1),  // IV as percentage string
      atmCallIV: ivData.atmCallIV,
      atmPutIV: ivData.atmPutIV,
      atmStrike: ivData.atmStrike,
      expiration: currentExpiry,
      expirationDate: new Date(currentExpiry * 1000).toISOString().split('T')[0],
      availableExpiries: expirationDates.length,
      ivLevel: ivLevel,                    // 'LOW', 'NORMAL', 'HIGH', 'EXTREME'
      totalCalls: calls.length,
      totalPuts: puts.length,
      timestamp: new Date().toISOString(),
      source: 'yahoo_options'
    };

  } catch (e) {
    console.error('[GME-IV] Error fetching options data:', e);
    return null;
  }
}

/**
 * Calculate average IV from near-the-money options
 */
function calculateAverageIV(calls, puts, currentPrice) {
  // Find the strike closest to current price
  let closestStrike = 0;
  let closestDiff = Infinity;

  for (const call of calls) {
    const diff = Math.abs(call.strike - currentPrice);
    if (diff < closestDiff) {
      closestDiff = diff;
      closestStrike = call.strike;
    }
  }

  // Get ATM call IV
  const atmCall = calls.find(c => c.strike === closestStrike);
  const atmPut = puts.find(p => p.strike === closestStrike);

  let atmCallIV = atmCall?.impliedVolatility || 0;
  let atmPutIV = atmPut?.impliedVolatility || 0;

  // Also gather nearby strikes for a more robust IV estimate
  const nearbyIVs = [];
  const strikeRange = currentPrice * 0.1; // 10% range around ATM

  for (const call of calls) {
    if (Math.abs(call.strike - currentPrice) <= strikeRange && call.impliedVolatility > 0) {
      nearbyIVs.push(call.impliedVolatility);
    }
  }
  for (const put of puts) {
    if (Math.abs(put.strike - currentPrice) <= strikeRange && put.impliedVolatility > 0) {
      nearbyIVs.push(put.impliedVolatility);
    }
  }

  // Average IV: prefer ATM, fall back to nearby average
  let avgIV = 0;
  if (atmCallIV > 0 && atmPutIV > 0) {
    avgIV = (atmCallIV + atmPutIV) / 2;
  } else if (atmCallIV > 0) {
    avgIV = atmCallIV;
  } else if (atmPutIV > 0) {
    avgIV = atmPutIV;
  } else if (nearbyIVs.length > 0) {
    avgIV = nearbyIVs.reduce((a, b) => a + b, 0) / nearbyIVs.length;
  }

  return {
    avgIV,
    atmCallIV,
    atmPutIV,
    atmStrike: closestStrike,
    nearbyCount: nearbyIVs.length
  };
}

/**
 * Classify IV level for display context
 * GME typical ranges: 40-60% normal, 60-100% elevated, 100%+ extreme
 */
function getIVLevel(iv) {
  const ivPct = iv * 100;
  if (ivPct < 40) return 'LOW';
  if (ivPct < 65) return 'NORMAL';
  if (ivPct < 100) return 'HIGH';
  return 'EXTREME';
}

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const ivData = await fetchGMEOptionsIV();

    if (ivData) {
      // Cache for 60 seconds - IV doesn't change as frequently as price
      res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');
      return res.status(200).json(ivData);
    }

    // Fallback response if fetch fails
    return res.status(200).json({
      symbol: 'GME',
      iv: 0,
      ivPercent: '--',
      ivLevel: 'UNKNOWN',
      error: 'Unable to fetch IV data',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('[GME-IV] Handler Error:', error);
    return res.status(200).json({
      symbol: 'GME',
      iv: 0,
      ivPercent: '--',
      ivLevel: 'UNKNOWN',
      error: String(error.message || error),
      timestamp: new Date().toISOString()
    });
  }
};
