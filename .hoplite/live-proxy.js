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
    if (h['set-cookie']) h['set-cookie'] = h['set-cookie'].map((c) => c.replace(/;\s*domain=[^;]+/i, ''));
    res.writeHead(r.statusCode, h);
    r.pipe(res);
  });
  up.on('error', (e) => { res.writeHead(502); res.end(String(e)); });
  req.pipe(up);
}).listen(PORT, '0.0.0.0', () => console.log('proxy on', PORT));
