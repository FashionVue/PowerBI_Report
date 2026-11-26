// Renders the right-to-left VehicleSales page backgrounds (SVG -> 2x JPEG) and labelled previews from layout.json.
// Usage: node render.js <layout.json> <lucide icons dir> <out render dir> <out previews dir>
// Needs Tajawal installed for Chromium (fonts/*.ttf -> ~/.fonts, then fc-cache -f).
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const [layoutPath, iconDir, outDir, prevDir] = process.argv.slice(2);
const L = JSON.parse(fs.readFileSync(layoutPath, "utf8"));
const FONT = "Tajawal, sans-serif";
let C = null;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function icon(name, cx, cy, size, color, sw = 1.75) {
  let file = path.join(iconDir, `${name}.svg`);
  if (!fs.existsSync(file)) file = path.join(iconDir, "circle.svg");
  const inner = fs.readFileSync(file, "utf8").replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>[\s\S]*$/, "");
  return `<g transform="translate(${cx - size / 2} ${cy - size / 2}) scale(${size / 24})" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${inner}</g>`;
}

// Arabic text: direction rtl + text-anchor start puts the right edge of the text at x
function ar(x, y, str, { size = 14, weight = 400, color = C.text, align = "right", spacing = 0, opacity = 1 } = {}) {
  const anchor = align === "right" ? "start" : align === "center" ? "middle" : "end";
  return `<text x="${x}" y="${y}" direction="rtl" font-family="${FONT}" font-size="${size}" font-weight="${weight}" fill="${color}" text-anchor="${anchor}" letter-spacing="${spacing}" opacity="${opacity}">${esc(str)}</text>`;
}
function en(x, y, str, { size = 14, weight = 400, color = C.text, anchor = "start", spacing = 0 } = {}) {
  return `<text x="${x}" y="${y}" direction="ltr" font-family="${FONT}" font-size="${size}" font-weight="${weight}" fill="${color}" text-anchor="${anchor}" letter-spacing="${spacing}">${esc(str)}</text>`;
}

// panel with an angled cut at the top-left corner (speed motif) and small radii elsewhere
function shape(x, y, w, h, cut = 18, r = 6) {
  return `M ${x + cut} ${y} H ${x + w - r} Q ${x + w} ${y} ${x + w} ${y + r} V ${y + h - r} Q ${x + w} ${y + h} ${x + w - r} ${y + h} H ${x + r} Q ${x} ${y + h} ${x} ${y + h - r} V ${y + cut} Z`;
}
function panelBox(x, y, w, h, accent = true) {
  let s = `<path d="${shape(x, y, w, h)}" fill="${C.panel}" filter="url(#shadow)"/>`;
  s += `<path d="${shape(x + 0.5, y + 0.5, w - 1, h - 1)}" fill="none" stroke="${C.border}" stroke-width="1"/>`;
  if (accent) s += `<rect x="${x + w - 140}" y="${y}" width="116" height="2" fill="${C.s1}"/>`;
  return s;
}

function header(p) {
  const o = [];
  o.push(ar(1792, 66, p.title, { size: 34, weight: 800 }));
  o.push(`<text x="1792" y="98" direction="rtl" font-family="${FONT}" font-size="15" text-anchor="start"><tspan fill="${C.accentText}" font-weight="700">مجموعة مسار الأفق للسيارات</tspan><tspan fill="${C.text2}">  ·  تقرير الأداء التنفيذي  ·  المبالغ بالريال السعودي</tspan></text>`);
  // speed lines next to the title block
  for (let i = 0; i < 5; i++) o.push(`<line x1="${880 + i * 14}" y1="96" x2="${910 + i * 14}" y2="40" stroke="${C.s1}" stroke-opacity="${0.12 + i * 0.05}" stroke-width="2"/>`);
  for (const c of p.controls || []) {
    o.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="6" fill="${C.panel}" stroke="${C.border}"/>`);
    o.push(ar(c.x + c.w - 14, c.y + 22, c.label, { size: 12, weight: 700, color: C.text2 }));
    if (c.kind === "mode") {
      const dark = p.mode === "dark";
      o.push(`<rect x="${c.x + 12}" y="${c.y + 34}" width="88" height="28" rx="14" fill="${C.panel2}" stroke="${C.border}"/>`);
      o.push(`<rect x="${dark ? c.x + 58 : c.x + 14}" y="${c.y + 36}" width="40" height="24" rx="12" fill="${C.s1}" fill-opacity="0.25"/>`);
      o.push(icon("sun", c.x + 34, c.y + 48, 16, dark ? C.text2 : C.accentText));
      o.push(icon("moon", c.x + 78, c.y + 48, 16, dark ? C.accentText : C.text2));
    }
  }
  if (p.key !== "cover") o.push(`<rect x="40" y="119" width="1752" height="1" fill="${C.border}"/><rect x="1552" y="118" width="240" height="2" fill="${C.s1}"/>`);
  return o.join("\n");
}

function rail(p) {
  const o = [`<rect x="1824" y="0" width="96" height="1080" fill="${C.rail}"/><rect x="1823" y="0" width="1" height="1080" fill="${C.border}"/>`];
  // brand mark: two chevrons forming a road arrow
  o.push(`<path d="M1872 30 L1896 58 L1886 58 L1872 42 L1858 58 L1848 58 Z" fill="${C.s1}"/><path d="M1872 52 L1890 74 L1880 74 L1872 64 L1864 74 L1854 74 Z" fill="${C.s2}"/>`);
  o.push(`<rect x="1852" y="96" width="40" height="1" fill="${C.border}"/>`);
  L.nav.forEach((n, i) => {
    const active = i === p.active;
    if (active) o.push(`<rect x="1836" y="${n.y}" width="72" height="72" rx="6" fill="${C.s1}" fill-opacity="0.14"/><rect x="1916" y="${n.y + 16}" width="4" height="40" fill="${C.s1}"/>`);
    o.push(icon(n.icon, 1872, n.y + 28, 24, active ? C.accentText : C.text2));
    o.push(ar(1872, n.y + 60, n.label, { size: 12, weight: active ? 700 : 500, color: active ? C.accentText : C.text2, align: "center" }));
  });
  return o.join("\n");
}

function body(p) {
  const o = [];
  for (const t of p.tiles) {
    if (t.hero) {
      o.push(`<rect x="${t.x}" y="${t.y}" width="${t.w}" height="${t.h}" rx="6" fill="${C.panel2}" stroke="${C.border}"/><rect x="${t.x + t.w - 4}" y="${t.y + 16}" width="4" height="${t.h - 32}" fill="${C.s1}"/>`);
      o.push(ar(t.x + t.w / 2, t.y + 128, t.label, { size: 15, weight: 500, color: C.text2, align: "center" }));
      continue;
    }
    o.push(panelBox(t.x, t.y, t.w, t.h));
    o.push(`<rect x="${t.x + t.w - 60}" y="${t.y + 20}" width="40" height="40" rx="8" fill="${C.s1}" fill-opacity="0.15"/>`);
    o.push(icon(t.icon, t.x + t.w - 40, t.y + 40, 20, C.accentText));
    o.push(ar(t.x + t.w - 72, t.y + 47, t.label, { size: 16, weight: 700, color: C.text2 }));
    o.push(`<rect x="${t.x + 20}" y="${t.y + 150}" width="${t.w - 40}" height="1" fill="${C.border}"/>`);
    if (t.caption) o.push(ar(t.x + t.w / 2, t.y + 138, t.caption, { size: 13, color: C.text2, align: "center" }));
  }
  for (const q of p.panels) {
    o.push(panelBox(q.x, q.y, q.w, q.h));
    o.push(`<rect x="${q.x + q.w - 27}" y="${q.y + 24}" width="3" height="20" fill="${C.s1}"/>`);
    o.push(ar(q.x + q.w - 36, q.y + 41, q.title, { size: 20, weight: 700 }));
    o.push(ar(q.x + q.w - 36, q.y + 65, q.subtitle, { size: 14, color: C.text2 }));
  }
  for (const b of p.bullets) {
    o.push(`<rect x="${b.x}" y="${b.y}" width="22" height="22" rx="5" fill="${C.s1}" fill-opacity="0.16"/>`);
    if (b.num) o.push(en(b.x + 11, b.y + 16, String(b.num), { size: 13, weight: 800, color: C.accentText, anchor: "middle" }));
    else o.push(icon("lightbulb", b.x + 11, b.y + 11, 14, C.accentText));
    if (b.text) o.push(ar(b.x - 10, b.y + 16, b.text, { size: 15, weight: 700 }));
  }
  return o.join("\n");
}

function cover(p) {
  const o = [];
  const h = p.extra.hero, t = p.extra.toc;
  o.push(`<path d="${shape(h.x, h.y, h.w, h.h, 40, 8)}" fill="${C.panel}" filter="url(#shadow)"/>`);
  o.push(`<path d="${shape(h.x, h.y, h.w, h.h, 40, 8)}" fill="url(#heroGlow)"/>`);
  for (let i = 0; i < 9; i++) o.push(`<line x1="${h.x + 60 + i * 26}" y1="${h.y + 560}" x2="${h.x + 220 + i * 26}" y2="${h.y + 40}" stroke="${C.s1}" stroke-opacity="${0.05 + i * 0.025}" stroke-width="3"/>`);
  o.push(icon("car-front", h.x + 230, h.y + 420, 300, C.s1, 0.6).replace("<g ", '<g opacity="0.10" '));
  o.push(`<rect x="${h.x + h.w - 56}" y="${h.y + 72}" width="6" height="150" fill="${C.s1}"/>`);
  o.push(ar(h.x + h.w - 76, h.y + 118, "تقرير أداء المبيعات", { size: 56, weight: 800 }));
  o.push(ar(h.x + h.w - 76, h.y + 192, "وخدمات ما بعد البيع", { size: 56, weight: 800, color: C.accentText }));
  o.push(ar(h.x + h.w - 76, h.y + 262, "مجموعة مسار الأفق للسيارات", { size: 28, weight: 700, color: C.text2 }));
  o.push(en(h.x + h.w - 76, h.y + 296, "Masar Horizon Motors", { size: 18, weight: 500, color: C.text2, anchor: "end", spacing: 2 }));
  o.push(`<rect x="${h.x + h.w - 76 - 200}" y="${h.y + 330}" width="200" height="44" rx="22" fill="${C.s1}" fill-opacity="0.16" stroke="${C.s1}"/>`);
  o.push(en(h.x + h.w - 176, h.y + 360, "2023 – 2025", { size: 22, weight: 700, color: C.accentText, anchor: "middle" }));
  const lines = ["يقدّم هذا التقرير صورة شاملة عن أداء المبيعات والأهداف والمخزون والتمويل",
                 "وخدمات ما بعد البيع في فروع المجموعة خلال ثلاث سنوات، مع مؤشرات وتوصيات",
                 "مكتوبة آلياً من البيانات لدعم قرارات الإدارة التنفيذية."];
  lines.forEach((l, i) => o.push(ar(h.x + h.w - 76, h.y + 440 + i * 36, l, { size: 20, color: C.text })));
  o.push(ar(h.x + h.w - 32, 780, "أرقام رئيسية 2023-2025", { size: 18, weight: 700, color: C.text2 }));
  // table of contents
  o.push(panelBox(t.x, t.y, t.w, t.h));
  o.push(`<rect x="${t.x + t.w - 27}" y="${t.y + 30}" width="3" height="24" fill="${C.s1}"/>`);
  o.push(ar(t.x + t.w - 36, t.y + 52, "المحتويات", { size: 26, weight: 800 }));
  o.push(ar(t.x + t.w - 36, t.y + 80, "اضغط على أي قسم للانتقال إليه", { size: 14, color: C.text2 }));
  const desc = ["المؤشرات الرئيسية مقابل العام السابق والهدف", "تحقيق الأهداف والخصومات والموسمية", "أداء الطرازات وعمر المخزون والتحول الكهربائي",
                "مسار البيع ومصادر العملاء والتمويل", "الإيرادات والرضا وزمن الإنجاز", "النتائج والتوصيات والخطوات التالية"];
  L.toc.forEach((item, i) => {
    const y = 236 + i * 128;
    o.push(`<rect x="${t.x + 24}" y="${y}" width="${t.w - 48}" height="112" rx="6" fill="${C.panel2}" stroke="${C.border}"/>`);
    o.push(en(t.x + t.w - 48, y + 66, String(i + 1).padStart(2, "0"), { size: 34, weight: 800, color: C.s1, anchor: "end" }));
    o.push(ar(t.x + t.w - 112, y + 50, item.title, { size: 22, weight: 700 }));
    o.push(ar(t.x + t.w - 112, y + 82, desc[i], { size: 14, color: C.text2 }));
    o.push(icon(item.icon, t.x + 72, y + 56, 28, C.accentText));
    o.push(icon("chevron-left", t.x + 120, y + 56, 20, C.text2));
  });
  return o.join("\n");
}

function conclusionExtra(p) {
  const n = p.extra.next, o = [panelBox(n.x, n.y, n.w, n.h)];
  o.push(`<rect x="${n.x + n.w - 27}" y="${n.y + 24}" width="3" height="20" fill="${C.s1}"/>`);
  o.push(ar(n.x + n.w - 36, n.y + 41, "الخطوات التالية", { size: 20, weight: 700 }));
  o.push(ar(n.x + n.w - 36, n.y + 65, "خطة تنفيذ مقترحة على ثلاث مراحل", { size: 14, color: C.text2 }));
  const cols = [["خلال 30 يوماً", ["اعتماد سقف للخصم في كل فرع ومراجعته أسبوعياً", "متابعة فورية للعملاء المحتملين من سناب شات"]],
                ["خلال 90 يوماً", ["إطلاق برنامج إحالة بمكافآت للعملاء الحاليين", "خطة تصريف للمخزون الذي تجاوز 90 يوماً"]],
                ["خلال 6 أشهر", ["توسيع تشكيلة الطرازات الصينية والهجينة", "رفع طاقة مراكز الصيانة لخفض زمن الإنجاز"]]];
  const cw = (n.w - 48 - 2 * 24) / 3;
  cols.forEach(([title, items], i) => {
    const x = n.x + n.w - 24 - (i + 1) * cw - i * 24, y = n.y + 92;
    o.push(`<rect x="${x}" y="${y}" width="${cw}" height="168" rx="6" fill="${C.panel2}" stroke="${C.border}"/><rect x="${x + cw - 4}" y="${y + 16}" width="4" height="136" fill="${[C.s1, C.s2, C.s3][i]}"/>`);
    o.push(ar(x + cw - 24, y + 38, title, { size: 18, weight: 800, color: [C.accentText, C.s2, C.s3][i] }));
    items.forEach((it, j) => {
      o.push(`<circle cx="${x + cw - 28}" cy="${y + 78 + j * 44}" r="4" fill="${C.text2}"/>`);
      o.push(ar(x + cw - 42, y + 84 + j * 44, it, { size: 15, color: C.text }));
    });
  });
  o.push(`<rect x="${n.x + 24}" y="${n.y + n.h - 72}" width="240" height="48" rx="24" fill="${C.s1}" fill-opacity="0.16" stroke="${C.s1}"/>`);
  o.push(icon("arrow-right", n.x + 60, n.y + n.h - 48, 18, C.accentText));
  o.push(ar(n.x + 236, n.y + n.h - 42, "العودة إلى المقدمة", { size: 16, weight: 700, color: C.accentText }));
  return o.join("\n");
}

function pageSvg(p) {
  C = L.palettes[p.mode];
  const o = [`<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">`];
  o.push(`<defs>
    <pattern id="bp" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0 H0 V32" fill="none" stroke="${C.blueprint}" stroke-opacity="${C.bpOpacity}" stroke-width="1"/></pattern>
    <radialGradient id="glow" cx="1500" cy="-120" r="980" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="${C.s1}" stop-opacity="0.12"/><stop offset="1" stop-color="${C.s1}" stop-opacity="0"/></radialGradient>
    <linearGradient id="heroGlow" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${C.s1}" stop-opacity="0.16"/><stop offset="0.6" stop-color="${C.s1}" stop-opacity="0"/></linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000" flood-opacity="${p.mode === "dark" ? 0.4 : 0.08}"/></filter>
  </defs>`);
  o.push(`<rect width="1920" height="1080" fill="${C.canvas}"/><rect width="1920" height="1080" fill="url(#bp)"/><rect width="1920" height="1080" fill="url(#glow)"/>`);
  o.push(rail(p));
  o.push(header(p));
  if (p.key === "cover") o.push(cover(p));
  o.push(body(p));
  if (p.key === "conclusion") o.push(conclusionExtra(p));
  o.push(`</svg>`);
  return o.join("\n");
}

function overlay(p) {
  return p.visuals.map((v) => {
    const h = /^Nav|^TOC|toggle|cover/i.test(v.label) ? 280 : /slicer/i.test(v.label) ? 200 : /القيمة|التغير|سنوات|Insight|Recommendation|cover/.test(v.label) ? 45 : 160;
    return `<rect x="${v.x}" y="${v.y}" width="${v.w}" height="${v.h}" fill="hsla(${h},80%,60%,0.22)" stroke="hsla(${h},90%,65%,0.95)" stroke-width="1.5" stroke-dasharray="5 3"/>` +
      `<text x="${v.x + 4}" y="${v.y + 13}" font-family="Tajawal, sans-serif" font-size="11" font-weight="700" fill="#fff" stroke="#000" stroke-width="2.5" paint-order="stroke">${esc(v.label)} ${v.w}x${v.h}</text>`;
  }).join("\n");
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true }); fs.mkdirSync(prevDir, { recursive: true });
  const browser = await chromium.launch();
  for (const [scale, prev] of [[2, false], [1, true]]) {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
    const page = await ctx.newPage();
    for (const p of L.pages) {
      let svg = pageSvg(p);
      if (prev) svg = svg.replace("</svg>", overlay(p) + "\n</svg>");
      else fs.writeFileSync(path.join(outDir, p.bg.replace(".jpg", ".svg")), svg);
      await page.setContent(`<html><body style="margin:0;background:#000">${svg}</body></html>`);
      await page.evaluate(() => document.fonts.ready);
      const file = prev ? path.join(prevDir, `vehicles-${p.key}-${p.mode}.png`) : path.join(outDir, p.bg);
      await page.screenshot(Object.assign({ path: file, clip: { x: 0, y: 0, width: 1920, height: 1080 } }, prev ? {} : { type: "jpeg", quality: 90 }));
    }
    await ctx.close();
  }
  await browser.close();
  console.log("rendered", L.pages.length, "pages");
})();
