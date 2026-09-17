import { build } from 'vite';
import react from '@vitejs/plugin-react';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const contentPath = path.join(root, 'src', 'content.json');
const filename = '公理層閱讀器-離線版.html';
const diagramPaths = new Map();
let content = await readFile(contentPath, 'utf8');
for (const match of content.matchAll(/\/assets\/diagrams\/[\w.-]+\.svg/g)) {
  const asset = match[0];
  if (!diagramPaths.has(asset)) {
    const bytes = await readFile(path.join(root, 'public', asset));
    diagramPaths.set(asset, `data:image/svg+xml;base64,${bytes.toString('base64')}`);
  }
}
content = content.replace(/\/assets\/diagrams\/[\w.-]+\.svg/g, asset => diagramPaths.get(asset));
const parsedContent = JSON.parse(content);
assert.equal(parsedContent.clauses.length, 63);

const result = await build({
  configFile: false,
  root,
  publicDir: false,
  logLevel: 'warn',
  plugins: [
    {
      name: 'embed-reader-diagrams',
      enforce: 'pre',
      load(id) {
        if (path.resolve(id.split('?')[0]) === contentPath) return content;
      },
    },
    react(),
  ],
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    write: false,
    minify: 'esbuild',
    sourcemap: false,
    cssCodeSplit: false,
    modulePreload: false,
    lib: {
      entry: path.join(root, 'src', 'main.jsx'),
      name: 'GeometryAxiomReader',
      formats: ['iife'],
      fileName: 'reader',
    },
  },
});

const output = (Array.isArray(result) ? result : [result]).flatMap(part => part.output);
const scripts = output.filter(part => part.type === 'chunk');
const styles = output.filter(part => part.type === 'asset' && part.fileName.endsWith('.css'));
assert.equal(scripts.length, 1, 'Offline file must have exactly one classic script.');
assert.equal(scripts[0].imports.length, 0, 'Offline script cannot import external modules.');
assert.equal(scripts[0].dynamicImports.length, 0, 'Offline script cannot lazy-load modules.');
assert(styles.length > 0, 'Missing bundled styles.');
const js = scripts[0].code;
const css = styles.map(part => String(part.source)).join('\n');
const cssUrls = [...css.matchAll(/url\(([^)]+)\)/g)].map(match => match[1].replace(/^["']|["']$/g, ''));
assert(cssUrls.length > 0, 'Expected embedded fonts.');
assert(cssUrls.every(url => url.startsWith('data:')), 'CSS contains an external asset.');
assert(!js.includes('/assets/diagrams/'), 'A diagram was not embedded.');

const html = `<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#14191e" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'" />
  <title>公理層閱讀器 · 幾何專案</title>
  <!-- Offline single-file edition: all fonts, diagrams, styles and scripts are embedded. -->
  <style>${css.replace(/<\/style/gi, '<\\/style')}</style>
</head>
<body>
  <div id="root"></div>
  <noscript>請在瀏覽器中允許 JavaScript，以使用離線閱讀器。</noscript>
  <script>${js.replace(/<\/script/gi, '<\\/script')}</script>
</body>
</html>
`;
assert(!/<script[^>]+\bsrc\s*=/i.test(html));
assert(!/<link[^>]+\bhref\s*=/i.test(html));
assert(!/<script[^>]+type=["']module/i.test(html));
const destination = path.join(root, filename);
await writeFile(destination, html, 'utf8');
console.log(JSON.stringify({
  file: destination,
  sizeBytes: Buffer.byteLength(html),
  clauses: parsedContent.clauses.length,
  examples: parsedContent.clauses.reduce((sum, clause) => sum + clause.examples.length, 0),
  embeddedDiagrams: diagramPaths.size,
  embeddedFontUrls: cssUrls.length,
  externalImports: 0,
}, null, 2));
