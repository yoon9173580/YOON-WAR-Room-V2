/**
 * Position sizes for mobile.html - previously hardcoded literals in the
 * page's CONFIG object, visible to anyone who opened view-source. Requires
 * a valid session (see api/auth.js); the numbers themselves live only in
 * the PORTFOLIO_CONFIG environment variable, never in the repo.
 */

const { verifySession, getBearerToken } = require('../lib/auth');

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const session = verifySession(getBearerToken(req));
    if (!session.valid) {
      return res.status(401).json({ error: session.reason || 'unauthorized' });
    }

    const raw = process.env.PORTFOLIO_CONFIG;
    if (!raw) {
      return res.status(503).json({ error: 'PORTFOLIO_CONFIG not configured' });
    }

    let config;
    try {
      config = JSON.parse(raw);
    } catch (e) {
      return res.status(500).json({ error: 'PORTFOLIO_CONFIG is not valid JSON' });
    }

    return res.status(200).json({
      bbbyqShares: Number(config.bbbyqShares) || 0,
      fidShares: Number(config.fidShares) || 0,
      drsShares: Number(config.drsShares) || 0,
      mooShares: Number(config.mooShares) || 0
    });

  } catch (error) {
    console.error('[portfolio] Handler Error:', error);
    return res.status(500).json({ error: String(error.message || error) });
  }
};
