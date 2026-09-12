/**
 * GME Current Price API
 * Serverless equivalent of price_server.py's /api/gme-price route
 * Endpoint: /api/gme-price
 */

const BASE_PRICE = 25.00;

async function fetchWithTimeout(url, options = {}, limitMs = 5000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Fetch Timeout')), limitMs))
  ]);
}

async function getGMEPrice() {
  try {
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/GME';
    const res = await fetchWithTimeout(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' }
    }, 5000);

    if (res && res.ok) {
      const data = await res.json();
      const price = data?.chart?.result?.[0]?.meta?.regularMarketPrice;
      if (price) return price;
    }
  } catch (e) {
    console.error('[gme-price] Error fetching price:', e);
  }
  return BASE_PRICE;
}

function isMarketOpen() {
  const et = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }));
  const day = et.getDay();
  if (day === 0 || day === 6) return false;
  const minutes = et.getHours() * 60 + et.getMinutes();
  return minutes >= (9 * 60 + 30) && minutes <= (16 * 60);
}

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const price = await getGMEPrice();
    const now = new Date().toISOString();

    res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=30');
    return res.status(200).json({
      price: price,
      price_ratio: price / BASE_PRICE,
      timestamp: now,
      market_open: isMarketOpen(),
      last_update: now
    });

  } catch (error) {
    console.error('[gme-price] Handler Error:', error);
    return res.status(200).json({
      price: BASE_PRICE,
      price_ratio: 1.0,
      timestamp: new Date().toISOString(),
      market_open: false,
      last_update: null,
      error: String(error.message || error)
    });
  }
};
