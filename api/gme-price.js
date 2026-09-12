/**
 * GME current price API for enhanced_index.html (updatePriceDisplay /
 * updatePipelineValues). Public - no auth needed, Yahoo prices aren't secret.
 * Endpoint: /api/gme-price
 */

const { fetchYahooQuote } = require('../lib/yahoo-quote');

// enhanced_index.html's pipeline math is baselined against $25.00
// (see its CS-cost / ST3 / ST4 / GME-sell calculations). Overridable via
// env in case that baseline ever changes.
const BASE_PRICE = Number(process.env.GME_BASE_PRICE) || 25.00;

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

    const quote = await fetchYahooQuote('GME').catch(() => null);
    if (!quote) {
      return res.status(502).json({ error: 'Unable to fetch GME price' });
    }

    const price = quote.regularMarketPrice;

    res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=30');
    return res.status(200).json({
      price,
      price_ratio: price / BASE_PRICE,
      base_price: BASE_PRICE,
      market_open: isMarketOpen(),
      timestamp: new Date().toLocaleString()
    });

  } catch (error) {
    console.error('[gme-price] Handler Error:', error);
    return res.status(500).json({ error: String(error.message || error) });
  }
};
