/**
 * Google Sign-In endpoint for mobile.html.
 *
 * GET                       -> { clientId }                bootstrap for the sign-in button
 * GET  Bearer <session>     -> { valid, email }             session restore on page reload
 * POST { credential }       -> { token, email }             exchange a Google ID token for a session
 */

const { verifyGoogleCredential, signSession, verifySession, isEmailAllowed, checkRateLimit, getClientIp, getBearerToken } = require('../lib/auth');

module.exports = async function handler(req, res) {
  try {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') return res.status(200).end();

    if (req.method === 'GET') {
      const token = getBearerToken(req);
      if (token) {
        const session = verifySession(token);
        if (!session.valid) return res.status(401).json({ valid: false, error: session.reason });
        return res.status(200).json({ valid: true, email: session.email });
      }

      const clientId = process.env.GOOGLE_CLIENT_ID || null;
      return res.status(200).json({ clientId });
    }

    if (req.method === 'POST') {
      if (!checkRateLimit(`auth:${getClientIp(req)}`, 20, 15 * 60 * 1000)) {
        return res.status(429).json({ error: 'Too many attempts, try again later' });
      }

      const credential = req.body && req.body.credential;
      if (!credential) {
        return res.status(400).json({ error: 'missing_credential' });
      }

      let email;
      try {
        email = await verifyGoogleCredential(credential);
      } catch (e) {
        const code = e.code || 'invalid_credential';
        const status = code === 'not_configured' ? 503 : 401;
        return res.status(status).json({ error: code });
      }

      if (!isEmailAllowed(email)) {
        return res.status(403).json({ error: 'Account not authorized' });
      }

      let token;
      try {
        token = signSession(email);
      } catch (e) {
        return res.status(503).json({ error: 'not_configured' });
      }

      return res.status(200).json({ token, email });
    }

    return res.status(405).json({ error: 'Method not allowed' });

  } catch (error) {
    console.error('[auth] Handler Error:', error);
    return res.status(500).json({ error: String(error.message || error) });
  }
};
