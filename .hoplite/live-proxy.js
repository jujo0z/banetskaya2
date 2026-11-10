// Reverse proxy: local port -> https://banetskaya.duckdns.org (for Hoplite preview panel)
const http = require('http');
const https = require('https');
const TARGET = 'banetskaya.duckdns.org';
const PORT = Number(process.env.PORT) || 8000;

http.createServer((req, res) => {
  const headers = { ...req.headers, host: TARGET };
  delete headers['accept-encoding'];
  if (headers.origin) headers.origin = `https://${TARGET}`;
  if (headers.referer) headers.referer = headers.referer.replace(/^https?:\/\/[^/]+/, `https://${TARGET}`);
  const up = https.request({ host: TARGET, port: 443, path: req.url, method: req.method, headers }, (r) => {
    const h = { ...r.headers };
    if (h.location) h.location = h.location.replace(`https://${TARGET}`, '');
    // Preview panel loads the site in a cross-site iframe (https); local checks use plain http.
    const https_ = req.headers['x-forwarded-proto'] === 'https';
    if (h['set-cookie']) h['set-cookie'] = h['set-cookie'].map((c) => {
      c = c.replace(/;\s*domain=[^;]+/i, '').replace(/;\s*samesite=[^;]+/i, '').replace(/;\s*secure/i, '');
      return https_ ? `${c}; SameSite=None; Secure; Partitioned` : `${c}; SameSite=Lax`;
    });
    res.writeHead(r.statusCode, h);
    r.pipe(res);
  });
  up.on('error', (e) => { res.writeHead(502); res.end(String(e)); });
  req.pipe(up);
}).listen(PORT, '0.0.0.0', () => console.log('proxy on', PORT));
