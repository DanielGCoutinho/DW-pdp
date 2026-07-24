// Netlify Function: serves a generated PDP page stored in Supabase Storage
// with a proper text/html content-type.
//
// Supabase's Storage CDN deliberately serves publicly-hosted HTML as
// text/plain with a locked-down CSP (to stop public buckets being used for
// stored-XSS/phishing) -- that's a platform security policy, not something
// fixable via upload headers. This function sidesteps it by fetching the
// raw bytes server-side and re-wrapping them in a fresh HTTP response with
// the content-type Netlify (not Supabase) controls.
//
// Routed from /pages/<sku>.html via the redirect in netlify.toml -- Netlify
// only falls through to that redirect when no matching static file exists,
// so a real committed file like /pages/dwst60436.html keeps being served
// directly, unaffected.

const SUPABASE_URL = 'https://cyxhcnrfabtxusbzaokj.supabase.co';

exports.handler = async function (event) {
  const raw = (event.queryStringParameters && event.queryStringParameters.sku) || '';
  const sku = raw.toLowerCase().replace(/\.html$/, '').replace(/[^a-z0-9_-]/g, '');
  if (!sku) {
    return { statusCode: 400, body: 'Missing sku parameter.' };
  }

  const upstreamUrl = `${SUPABASE_URL}/storage/v1/object/public/pages/${sku}.html`;

  let upstreamRes;
  try {
    upstreamRes = await fetch(upstreamUrl);
  } catch (err) {
    return { statusCode: 502, body: 'Failed to reach storage backend: ' + err.message };
  }

  if (!upstreamRes.ok) {
    return {
      statusCode: upstreamRes.status === 404 ? 404 : 502,
      body: upstreamRes.status === 404 ? 'Page not found for SKU: ' + sku : 'Storage backend error.',
    };
  }

  const html = await upstreamRes.text();

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
    body: html,
  };
};
