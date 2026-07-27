// Netlify EDGE Function (Deno, not the Node/Lambda "functions" runtime) --
// serves a generated PDP page stored in Supabase Storage with a proper
// text/html content-type, streaming the body straight through.
//
// Why an edge function and not a regular (Lambda) function: classic Netlify
// Functions have a hard 6MB synchronous response-body cap. Generated pages
// (18 assets + inspiration references + real product photos) routinely
// exceed that now, and will only grow. Edge functions run on Deno Deploy at
// the edge and can stream the response body instead of buffering the whole
// thing as one in-memory string, so there's no equivalent cap here.
//
// Supabase's Storage CDN deliberately serves publicly-hosted HTML as
// text/plain with a locked-down CSP (to stop public buckets being used for
// stored-XSS/phishing) -- that's a platform security policy, not something
// fixable via upload headers. This function sidesteps it by re-wrapping the
// upstream body in a fresh Response with the content-type WE control.
//
// Routed via the `config.path` export below -- Netlify auto-discovers any
// file in netlify/edge-functions/. A real committed static file (if one
// ever exists again at site/pages/<sku>.html) is still served directly by
// Netlify's own static hosting when present; edge functions only run for
// requests that don't match an existing static file first? -- actually
// edge functions run BEFORE static file serving, so if this ever needs to
// coexist with a real static file again, add an early return/passthrough
// here. Today no page is static, so this always handles /pages/*.

const SUPABASE_URL = "https://cyxhcnrfabtxusbzaokj.supabase.co";

export default async (request, context) => {
  const url = new URL(request.url);
  const match = url.pathname.match(/\/pages\/([^/]+?)(?:\.html)?$/i);
  const raw = match ? match[1] : "";
  const sku = raw.toLowerCase().replace(/[^a-z0-9_-]/g, "");

  if (!sku) {
    return new Response("Missing sku in path: " + url.pathname, { status: 400 });
  }

  const upstreamUrl = `${SUPABASE_URL}/storage/v1/object/public/pages/${sku}.html`;

  let upstream;
  try {
    upstream = await fetch(upstreamUrl);
  } catch (err) {
    return new Response("Failed to reach storage backend: " + err.message, { status: 502 });
  }

  if (!upstream.ok) {
    const status = upstream.status === 404 ? 404 : 502;
    const body = upstream.status === 404 ? `Page not found for SKU: ${sku}` : "Storage backend error.";
    return new Response(body, { status });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=30",
    },
  });
};

export const config = { path: "/pages/*" };
