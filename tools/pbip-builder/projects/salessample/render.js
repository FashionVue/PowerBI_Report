// Renders page backgrounds (SVG -> 2x JPEG/PNG) and composition previews from layout.json (written by build_report.py).
// Usage: node render_backgrounds.js <layout.json> <lucide icons dir> <out render dir> <out previews dir>
// Needs the playwright package with Chromium; baked text uses Inter (OFL), the closest installed match to Segoe UI.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const [layoutPath, iconDir, outDir, prevDir] = process.argv.slice(2);
const L = JSON.parse(fs.readFileSync(layoutPath, "utf8"));
let C = null;
const FONT = "Inter, 'Segoe UI', sans-serif";

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function icon(name, cx, cy, size, color) {
  const raw = fs.readFileSync(path.join(iconDir, `${name}.svg`), "utf8");
  const inner = raw.replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>[\s\S]*$/, "");
  const s = size / 24;
  return `<g transform="translate(${cx - size / 2} ${cy - size / 2}) scale(${s})" fill="none" stroke="${color}" stroke-width="${1.75}" stroke-linecap="round" stroke-linejoin="round">${inner}</g>`;
}

function text(x, y, str, { size = 12, weight = 400, color = C.text, spacing = 0, anchor = "start" } = {}) {
  return `<text x="${x}" y="${y}" font-family="${FONT}" font-size="${size}" font-weight="${weight}" fill="${color}" letter-spacing="${spacing}" text-anchor="${anchor}">${esc(str)}</text>`;
}

function card(x, y, w, h, r = 16) {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${C.panel}" filter="url(#shadow)"/>` +
    `<rect x="${x + 0.5}" y="${y + 0.5}" width="${w - 1}" height="${h - 1}" rx="${r - 0.5}" fill="url(#panelSheen)" stroke="${C.border}" stroke-width="1"/>`;
}

function pageSvg(p) {
  C = L.palettes[p.mode];
  const out = [];
  out.push(`<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">`);
  out.push(`<defs>
    <radialGradient id="glowGold" cx="1700" cy="-80" r="900" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="${C.s1}" stop-opacity="${C.glow}"/><stop offset="1" stop-color="${C.s1}" stop-opacity="0"/></radialGradient>
    <radialGradient id="glowSteel" cx="300" cy="1180" r="900" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="${C.s2}" stop-opacity="${C.glow * 0.7}"/><stop offset="1" stop-color="${C.s2}" stop-opacity="0"/></radialGradient>
    <linearGradient id="panelSheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${p.mode === 'dark' ? '#FFFFFF' : '#FFFFFF'}" stop-opacity="${p.mode === 'dark' ? 0.025 : 0}"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>
    <linearGradient id="goldLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="${C.s1}" stop-opacity="0"/><stop offset="0.5" stop-color="${C.accentText}" stop-opacity="0.9"/><stop offset="1" stop-color="${C.s1}" stop-opacity="0"/></linearGradient>
    <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${C.accentText}"/><stop offset="1" stop-color="${C.s1}"/></linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="160%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="${p.mode === 'dark' ? '#000000' : '#6B5B3E'}" flood-opacity="${p.mode === 'dark' ? 0.35 : 0.10}"/></filter>
  </defs>`);
  // canvas
  out.push(`<rect width="1920" height="1080" fill="${C.canvas}"/>`);
  out.push(`<rect width="1920" height="1080" fill="url(#glowGold)"/><rect width="1920" height="1080" fill="url(#glowSteel)"/>`);
  // navigation rail
  out.push(`<rect x="0" y="0" width="96" height="1080" fill="${C.rail}"/><rect x="96" y="0" width="1" height="1080" fill="${C.border}"/>`);
  out.push(`<rect x="24" y="32" width="48" height="48" rx="12" fill="none" stroke="url(#brand)" stroke-width="1.5"/>`);
  out.push(`<path d="M48 42 L58 56 L48 70 L38 56 Z" fill="none" stroke="url(#brand)" stroke-width="1.5" stroke-linejoin="round"/>`);
  out.push(`<path d="M38 56 H58" stroke="url(#brand)" stroke-width="1.2"/>`);
  out.push(`<rect x="28" y="104" width="40" height="1" fill="${C.border}"/>`);
  L.nav.forEach((n, i) => {
    const active = i === p.active;
    if (active) {
      out.push(`<rect x="12" y="${n.y}" width="72" height="72" rx="14" fill="${C.s1}" fill-opacity="0.13"/>`);
      out.push(`<rect x="0" y="${n.y + 18}" width="3" height="36" rx="1.5" fill="${C.s1}"/>`);
    }
    out.push(icon(n.icon, 48, n.y + 28, 24, active ? C.accentText : C.text2));
    out.push(text(48, n.y + 58, n.label, { size: 10, weight: active ? 600 : 400, color: active ? C.accentText : C.text2, anchor: "middle" }));
  });
  // header
  out.push(text(128, 66, p.title, { size: 32, weight: 600, spacing: -0.3 }));
  out.push(`<text x="128" y="94" font-family="${FONT}" font-size="15" letter-spacing="0.2"><tspan fill="${C.accentText}">FashionVue · Executive Performance</tspan><tspan fill="${C.text2}">   ·   All amounts in SAR</tspan></text>`);
  for (const c of p.controls || []) {
    out.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="12" fill="${C.panel}" stroke="${C.border}"/>`);
    out.push(text(c.x + 16, c.y + 21, c.label, { size: 10, weight: 600, color: C.text2, spacing: 1.4 }));
    if (c.kind === "mode") {
      const dark = p.mode === "dark";
      out.push(`<rect x="${c.x + 12}" y="${c.y + 34}" width="88" height="28" rx="14" fill="${C.panel2}" stroke="${C.border}"/>`);
      out.push(`<rect x="${dark ? c.x + 58 : c.x + 14}" y="${c.y + 36}" width="40" height="24" rx="12" fill="${C.s1}" fill-opacity="0.22"/>`);
      out.push(icon("sun", c.x + 34, c.y + 48, 16, dark ? C.text2 : C.accentText));
      out.push(icon("moon", c.x + 78, c.y + 48, 16, dark ? C.accentText : C.text2));
    }
  }
  out.push(`<rect x="128" y="119" width="1752" height="1" fill="${C.border}"/>`);
  out.push(`<rect x="128" y="119" width="240" height="1" fill="url(#goldLine)"/>`);
  // KPI tiles
  for (const t of p.tiles) {
    out.push(card(t.x, t.y, t.w, t.h));
    out.push(`<rect x="${t.x + 24}" y="${t.y}" width="${t.w - 48}" height="1" fill="url(#goldLine)" opacity="0.6"/>`);
    out.push(`<rect x="${t.x + 20}" y="${t.y + 20}" width="40" height="40" rx="10" fill="${C.s1}" fill-opacity="0.14"/>`);
    out.push(icon(t.icon, t.x + 40, t.y + 40, 20, C.accentText));
    out.push(text(t.x + 72, t.y + 45, t.label, { size: 12, weight: 600, color: C.text2, spacing: 1.3 }));
    out.push(`<rect x="${t.x + 20}" y="${t.y + 150}" width="${t.w - 40}" height="1" fill="${C.border}" opacity="0.7"/>`);
    if (t.caption) out.push(text(t.x + t.w / 2, t.y + 136, t.caption, { size: 12, color: C.text2, anchor: "middle" }));
  }
  // panels
  for (const q of p.panels) {
    out.push(card(q.x, q.y, q.w, q.h));
    out.push(`<rect x="${q.x + 24}" y="${q.y + 23}" width="3" height="20" rx="1.5" fill="${C.s1}"/>`);
    out.push(text(q.x + 36, q.y + 39, q.title, { size: 18, weight: 600, spacing: -0.1 }));
    out.push(text(q.x + 36, q.y + 63, q.subtitle, { size: 13, color: C.text2 }));
  }
  for (const b of p.bullets || []) {
    out.push(`<rect x="${b.x}" y="${b.y}" width="20" height="20" rx="6" fill="${C.s1}" fill-opacity="0.14"/>`);
    out.push(icon("lightbulb", b.x + 10, b.y + 10, 13, C.accentText));
    if (b.text) out.push(text(b.x + 28, b.y + 15, b.text, { size: 13, weight: 700, color: C.text }));
  }
  out.push(`</svg>`);
  return out.join("\n");
}

function previewOverlay(p) {
  const hues = { cardVisual: 45, slicer: 200, actionButton: 280 };
  return p.visuals.map((v, i) => {
    const h = /^Nav/.test(v.label) ? 280 : /slicer/i.test(v.label) ? 200 : / value$| vs PY$|Compared/.test(v.label) ? 45 : 160;
    return `<rect x="${v.x}" y="${v.y}" width="${v.w}" height="${v.h}" fill="hsla(${h},80%,60%,0.22)" stroke="hsla(${h},90%,65%,0.95)" stroke-width="1.5" stroke-dasharray="5 3"/>` +
      `<text x="${v.x + 4}" y="${v.y + 13}" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#FFFFFF" stroke="#000" stroke-width="2.5" paint-order="stroke">${esc(v.label)} ${v.w}x${v.h}</text>`;
  }).join("\n");
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(prevDir, { recursive: true });
  const browser = await chromium.launch();
  for (const [scale, withOverlay] of [[2, false], [1, true]]) {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
    const page = await ctx.newPage();
    for (const p of L.pages) {
      let svg = pageSvg(p);
      if (withOverlay) svg = svg.replace("</svg>", previewOverlay(p) + "\n</svg>");
      if (!withOverlay) fs.writeFileSync(path.join(outDir, p.bg.replace(/\.(png|jpg)$/, ".svg")), svg);
      await page.setContent(`<html><body style="margin:0;background:#000">${svg}</body></html>`);
      await page.evaluate(() => document.fonts.ready);
      const file = withOverlay ? path.join(prevDir, `preview-${p.key}-${p.mode}.png`) : path.join(outDir, p.bg);
      await page.screenshot(Object.assign({ path: file, clip: { x: 0, y: 0, width: 1920, height: 1080 } }, file.endsWith(".jpg") ? { type: "jpeg", quality: 90 } : {}));
      console.log("wrote", file, fs.statSync(file).size);
    }
    await ctx.close();
  }
  await browser.close();
})();
