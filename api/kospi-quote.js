// KOSPI-only endpoint, kept for diagnostics/verification against /api/quote
// (both should always report the same value - see lib/yahoo-quote.js).

const { fetchKOSPI } = require('../lib/yahoo-quote');
const { fetchKOSPIFromFinnhub } = require('../lib/kospi');

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') return res.status(200).end();

    let data = await fetchKOSPI();
    if (!data) {
      data = await fetchKOSPIFromFinnhub();
    }

    if (!data) {
      return res.status(502).json({ error: 'Could not fetch KOSPI data from any source', symbol: '^KS11' });
    }

    res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');
    return res.status(200).json(Object.assign({ timestamp: Date.now() }, data));

  } catch (error) {
    console.error('[kospi-quote] Handler Error:', error);
    return res.status(500).json({ error: String(error.message || error), symbol: '^KS11' });
  }
};
