/**
 * Google Sign-In verification + first-party session tokens.
 *
 * A verified Google ID token only proves "this person has a Google
 * account" - it says nothing about whether they should have access to this
 * dashboard. ALLOWED_EMAILS is the actual access control. If it isn't set,
 * every request is rejected rather than defaulting to open.
 *
 * The Google ID token itself is not reused as a session: it's short-lived
 * (~1h), verifying it requires a network round trip to Google's public
 * keys on every check, and revocation timing isn't under our control.
 * Instead we issue our own HMAC-signed token (AUTH_SECRET) with a longer
 * TTL, but re-check the allowlist on every verification - so removing an
 * email takes effect on the very next request even if their token is
 * still technically unexpired.
 */

const crypto = require('crypto');
const { OAuth2Client } = require('google-auth-library');

const SESSION_TTL_MS = 12 * 60 * 60 * 1000; // 12h

function getAllowedEmails() {
  return (process.env.ALLOWED_EMAILS || '')
    .split(',')
    .map(e => e.trim().toLowerCase())
    .filter(Boolean);
}

function isEmailAllowed(email) {
  const allowed = getAllowedEmails();
  if (allowed.length === 0) return false; // fail closed: unconfigured = nobody in
  return allowed.includes(String(email || '').trim().toLowerCase());
}

function signSession(email) {
  const secret = process.env.AUTH_SECRET;
  if (!secret) throw new Error('AUTH_SECRET not configured');
  const payload = { email, exp: Date.now() + SESSION_TTL_MS };
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${sig}`;
}

function verifySession(token) {
  const secret = process.env.AUTH_SECRET;
  if (!secret) return { valid: false, reason: 'not_configured' };
  if (!token || typeof token !== 'string' || !token.includes('.')) {
    return { valid: false, reason: 'missing' };
  }

  const [body, sig] = token.split('.');
  const expected = crypto.createHmac('sha256', secret).update(body).digest('base64url');

  const sigBuf = Buffer.from(sig || '', 'utf8');
  const expBuf = Buffer.from(expected, 'utf8');
  if (sigBuf.length !== expBuf.length || !crypto.timingSafeEqual(sigBuf, expBuf)) {
    return { valid: false, reason: 'bad_signature' };
  }

  let payload;
  try {
    payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
  } catch (e) {
    return { valid: false, reason: 'bad_payload' };
  }

  if (!payload.exp || Date.now() > payload.exp) {
    return { valid: false, reason: 'expired' };
  }
  if (!isEmailAllowed(payload.email)) {
    return { valid: false, reason: 'not_allowed' };
  }

  return { valid: true, email: payload.email };
}

let oauthClient = null;
function getOAuthClient() {
  if (!oauthClient) oauthClient = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);
  return oauthClient;
}

/**
 * Verifies a Google ID token's signature and audience.
 * @returns {Promise<string>} the verified, verified-owned email
 */
async function verifyGoogleCredential(credential) {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  if (!clientId) {
    throw Object.assign(new Error('Google sign-in not configured'), { code: 'not_configured' });
  }

  let ticket;
  try {
    ticket = await getOAuthClient().verifyIdToken({ idToken: credential, audience: clientId });
  } catch (e) {
    throw Object.assign(new Error('invalid_credential'), { code: 'invalid_credential' });
  }

  const payload = ticket.getPayload();
  if (!payload || !payload.email) {
    throw Object.assign(new Error('invalid_credential'), { code: 'invalid_credential' });
  }
  if (!payload.email_verified) {
    throw Object.assign(new Error('email_unverified'), { code: 'email_unverified' });
  }

  return payload.email;
}

// Simple in-memory rate limiter. Scoped to a single lambda instance, so it
// dilutes across concurrent instances - acceptable here because Google
// sign-in leaves nothing guessable to brute-force; it just caps abuse.
const rateBuckets = new Map();
function checkRateLimit(key, limit = 20, windowMs = 15 * 60 * 1000) {
  const now = Date.now();
  const recent = (rateBuckets.get(key) || []).filter(t => now - t < windowMs);
  recent.push(now);
  rateBuckets.set(key, recent);
  return recent.length <= limit;
}

function getClientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (fwd) return String(fwd).split(',')[0].trim();
  return (req.socket && req.socket.remoteAddress) || 'unknown';
}

function getBearerToken(req) {
  const header = req.headers['authorization'] || '';
  const match = /^Bearer\s+(.+)$/i.exec(header);
  return match ? match[1] : null;
}

module.exports = {
  isEmailAllowed,
  signSession,
  verifySession,
  verifyGoogleCredential,
  checkRateLimit,
  getClientIp,
  getBearerToken
};
