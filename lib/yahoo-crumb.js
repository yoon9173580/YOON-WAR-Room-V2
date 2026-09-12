/**
 * Yahoo Finance cookie+crumb handshake.
 *
 * Yahoo's options-chain endpoint (v7/finance/options) now rejects
 * unauthenticated requests with 401 "Invalid Crumb". A crumb is obtained by
 * first grabbing a session cookie from fc.yahoo.com, then exchanging it for
 * a crumb token; both are then attached to the real request.
 *
 * Cached at module scope for 10 minutes since the handshake is slow
 * (two round trips) and the crumb doesn't rotate that often.
 */

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
const TTL_MS = 10 * 60 * 1000;

let cache = null; // { cookie, crumb, expires }

function extractCookieHeader(res) {
  let cookies = [];
  if (typeof res.headers.getSetCookie === 'function') {
    cookies = res.headers.getSetCookie();
  } else {
    const single = res.headers.get('set-cookie');
    if (single) cookies = [single];
  }
  return cookies.map(c => c.split(';')[0]).join('; ');
}

async function handshake() {
  const cookieRes = await fetch('https://fc.yahoo.com', {
    redirect: 'manual',
    headers: { 'User-Agent': UA }
  });
  const cookieHeader = extractCookieHeader(cookieRes);
  if (!cookieHeader) {
    throw new Error('Yahoo crumb handshake: no cookie received');
  }

  const crumbRes = await fetch('https://query1.finance.yahoo.com/v1/test/getcrumb', {
    headers: { 'User-Agent': UA, 'Cookie': cookieHeader }
  });
  const crumb = (await crumbRes.text() || '').trim();
  if (!crumb || crumb.toLowerCase().includes('<html')) {
    throw new Error('Yahoo crumb handshake: invalid crumb response');
  }

  return { cookie: cookieHeader, crumb };
}

/**
 * @param {boolean} forceRefresh - bypass cache (used after a 401 to retry once)
 */
async function getYahooCrumb(forceRefresh = false) {
  if (!forceRefresh && cache && Date.now() < cache.expires) {
    return cache;
  }
  const { cookie, crumb } = await handshake();
  cache = { cookie, crumb, expires: Date.now() + TTL_MS };
  return cache;
}

module.exports = { getYahooCrumb };
