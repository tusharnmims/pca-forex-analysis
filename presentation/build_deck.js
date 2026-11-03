// Builds PCA_Forex_Analysis.pptx from deck_data.json + example_trade.json (python export_data.py first).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
// optional: writes the palette into the theme (pptx skill helper); the deck uses explicit colours either way
const applyTheme = process.env.PPTX_SKILL ? require(path.join(process.env.PPTX_SKILL, "scripts", "apply_theme.js")).applyTheme : null;

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json")));
const EX = JSON.parse(fs.readFileSync(path.join(__dirname, "example_trade.json")));
const IMG = path.join(__dirname, "..", "data");
const OUT = process.env.OUT || path.join(__dirname, "PCA_Forex_Analysis.pptx");

const THEME = {
  name: "PCA Forex",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F3B", lt1: "FFFFFF", dk2: "1E2761", lt2: "EEF1F8",
    accent1: "1E2761", accent2: "C9A227", accent3: "2E8B57", accent4: "C0392B",
    accent5: "5B6B9A", accent6: "9AA5B1", hlink: "1F5FBF", folHlink: "6B4FA0",
  },
};
const K = THEME.colors;
const NAVY = K.dk2, GOLD = K.accent2, GREEN = K.accent3, RED = K.accent4, SLATE = K.accent5,
  GREY = K.accent6, TINT = K.lt2, INK = K.dk1, ICE = "CADCFC", SILVER = "8C96A3";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Reading the Forex Market with PCA";

// ----------------------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE", background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.1, w: 11.7, h: 1.5, fontFace: "Cambria", fontSize: 44, bold: true, color: "FFFFFF", valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.8, w: 11.7, h: 2.7, fontFace: "Calibri", fontSize: 20, color: ICE, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.5, w: 11.7, h: 1.2, fontFace: "Cambria", fontSize: 40, bold: true, color: "FFFFFF", valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.85, w: 11.7, h: 0.8, fontFace: "Calibri", fontSize: 20, color: GOLD, valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: ICE, align: "right" },
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 12.1, h: 0.85, fontFace: "Cambria", fontSize: 32, bold: true, color: NAVY, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "PCA in the forex market", options: { x: 0.6, y: 6.95, w: 5, h: 0.3, fontSize: 10, color: GREY, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: GREY, align: "right" },
});

// ----------------------------------------------------------------------------- helpers
// SLIDES=1,5,9 builds only those slides (for finding a slide PowerPoint rejects)
const ONLY = process.env.SLIDES ? new Set(process.env.SLIDES.split(",").map(Number)) : null;
const scratch = new pptxgen();
scratch.defineSlideMaster({ title: "TITLE" }); scratch.defineSlideMaster({ title: "SECTION" }); scratch.defineSlideMaster({ title: "CONTENT" });
let slideNo = 0;
const newSlide = (o) => (++slideNo, !ONLY || ONLY.has(slideNo) ? pres.addSlide(o) : scratch.addSlide(o));
let SECTION = "Introduction";
const section = (t) => { SECTION = t; pres.addSection({ title: t }); };
const content = (title) => {
  const s = newSlide({ masterName: "CONTENT", sectionTitle: SECTION });
  s.addText(title, { placeholder: "title" });
  return s;
};
const divider = (title, sub, notes) => {
  const s = newSlide({ masterName: "SECTION", sectionTitle: SECTION });
  s.addText(title, { placeholder: "title" });
  s.addText(sub, { placeholder: "body" });
  if (notes) s.addNotes(notes);
  return s;
};
const card = (s, x, y, w, h, title, body, o = {}) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: o.fill || TINT }, line: { color: o.fill || TINT }, rectRadius: 0.08, objectName: o.name || `card ${title}` });
  const runs = [];
  if (title) runs.push({ text: title, options: { bold: true, fontSize: o.titleSize || 18, color: o.titleColor || NAVY, breakLine: true, paraSpaceAfter: 4 } });
  (Array.isArray(body) ? body : [body]).forEach((b, i, a) => runs.push({ text: b, options: { fontSize: o.size || 16, color: o.color || INK, breakLine: i < a.length - 1, paraSpaceAfter: 4, bullet: o.bullet ? true : undefined } }));
  s.addText(runs, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h - 0.3, valign: "top", isTextBox: true, margin: 0 });
};
const stat = (s, x, y, w, big, label, color) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 3.2, fill: { color: TINT }, line: { color: TINT }, rectRadius: 0.08, objectName: `stat ${big}` });
  s.addText(big, { x: x + 0.3, y: y + 0.3, w: w - 0.6, h: 1.4, fontFace: "Cambria", fontSize: 66, bold: true, color, isTextBox: true, margin: 0 });
  s.addText(label, { x: x + 0.3, y: y + 1.8, w: w - 0.6, h: 1.2, fontSize: 16, color: INK, valign: "top", isTextBox: true, margin: 0 });
};
const caption = (s, text, x, y, w, h = 0.4) =>
  s.addText(text, { x, y, w, h, fontSize: 12, color: SLATE, italic: true, isTextBox: true, margin: 0, valign: "top" });
const chartBase = (title) => ({
  showTitle: !!title, title, titleFontFace: "+mn-lt", titleFontSize: 14, titleColor: NAVY,
  catAxisLabelColor: SLATE, valAxisLabelColor: SLATE, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  dataLabelColor: INK, dataLabelFontSize: 10, legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: INK,
  valGridLine: { color: "E3E7F0", size: 0.5 }, catGridLine: { style: "none" },
  catAxisLineShow: true, catAxisLineColor: "C7CCDA", valAxisLineShow: false,
});
const table = (s, rows, x, y, w, colW, o = {}) => {
  const head = rows[0].map((t) => ({ text: String(t), options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, fontSize: o.size || 13, align: "center" } }));
  const body = rows.slice(1).map((r, i) => r.map((t, j) => ({
    text: String(t), options: { fontSize: o.size || 13, color: (o.colColor && o.colColor(r, j)) || INK, fill: { color: (o.rowFill && o.rowFill(r, i)) || (i % 2 ? TINT : "FFFFFF") }, align: j === 0 ? "left" : "center", bold: o.bold ? o.bold(r, j) : false },
  })));
  s.addTable([head, ...body], { x, y, w, colW, border: { type: "solid", pt: 0.5, color: "D5DAE6" }, rowH: o.rowH || 0.36, valign: "middle", margin: 0.05 });
};
const const_ = (n, v) => Array(n).fill(v);

// ============================================================================= INTRO
section("Introduction");
{
  const s = newSlide({ masterName: "TITLE", sectionTitle: SECTION });
  s.addText("Reading the Forex Market with PCA", { placeholder: "title" });
  s.addText("Which currency relationships hold, which fail, and when not to trade them\nHourly data, 9 currencies + gold + silver, 2010 – 2026", { placeholder: "body" });
  s.addNotes("Project: using Principal Component Analysis to understand how currencies move together, test whether the leftover relationships between pairs pull back, and build a daily gauge that tells us when those relationships are unreliable.");
}
{
  const s = content("The answer in three numbers");
  stat(s, 0.6, 1.5, 3.85, "49%", "of all currency movement comes from one common force: the US dollar", NAVY);
  stat(s, 4.75, 1.5, 3.85, "3×", "more pair breakdowns when that common force weakens (7.7% vs 2.3%)", RED);
  stat(s, 8.9, 1.5, 3.85, "69%", "of trading days PCA marks as safe for pair trading (2011 – 2026)", GREEN);
  s.addText([{ text: "Conclusion: ", options: { bold: true, color: NAVY } }, { text: "PCA tells us when not to rely on relationships between currency pairs." }],
    { x: 0.6, y: 5.2, w: 12.1, h: 0.6, fontSize: 20, color: INK, isTextBox: true, margin: 0 });
  caption(s, "Gold vs silver was tested the same way and fails: its relationship trends instead of pulling back.", 0.6, 5.85, 12.1);
  s.addNotes("Main message first. 49% = average share of the first PCA factor. 3x = stretched cross pairs break further 7.7% of the time in low-concentration periods vs 2.3% in high. 69% = days marked tradable by the live rule.");
}
{
  const s = content("Data used");
  card(s, 0.6, 1.45, 3.85, 3.6, "What", ["9 currencies, each priced in US dollars: EUR, GBP, AUD, NZD, CAD, CHF, JPY, NOK, SEK", "Gold (XAU) and silver (XAG)", "23 cross pairs, e.g. EURGBP, AUDNZD, EURJPY"]);
  card(s, 4.75, 1.45, 3.85, 3.6, "Where from", ["HistData.com: hourly prices, Jan 2010 – Oct 2026 (~100,000 hours)", "Vantage MT5: real spreads and swaps 2019 – 2026", "Daily candles closing 17:00 New York, like brokers"]);
  card(s, 8.9, 1.45, 3.85, 3.6, "Checks", ["Time zones converted to UTC and validated against MT5 and Yahoo", "Second source compared: OANDA vs HistData correlation 0.998", "Missing AUDJPY 2012 rebuilt from AUDUSD × USDJPY"]);
  const chips = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "USDNOK", "USDSEK", "XAUUSD", "XAGUSD"];
  chips.forEach((c, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6 + i * 1.11, y: 5.45, w: 1.0, h: 0.42, fill: { color: i >= 9 ? GOLD : NAVY }, line: { color: i >= 9 ? GOLD : NAVY }, rectRadius: 0.2, objectName: `chip ${c}` });
    s.addText(c, { x: 0.6 + i * 1.11, y: 5.45, w: 1.0, h: 0.42, fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
  });
  caption(s, "The 11 instruments the PCA is built from (USDxxx pairs are inverted so every series is “value in US dollars”).", 0.6, 6.0, 12.1);
}
{
  const s = content("Step 1 · Scale the data before PCA");
  s.addChart(pres.charts.BAR, [{ name: "Yearly volatility %", labels: D.raw_vol.labels, values: D.raw_vol.values }], {
    x: 0.6, y: 1.4, w: 6.4, h: 5.2, barDir: "bar", ...chartBase("Raw yearly volatility, % (before scaling)"),
    chartColors: [SLATE], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", showLegend: false,
  });
  card(s, 7.4, 1.4, 5.35, 1.35, "Why scale?", "Silver moves 4.5× more than the Canadian dollar. Unscaled, PCA would mostly describe silver.");
  card(s, 7.4, 2.95, 5.35, 3.65, "How (same as StandardScaler)", [
    "1. Prices → hourly % changes (log returns)",
    "2. Standardise each series: z = (return − mean) / std",
    "3. Mean and std come from the past window only (480 hours / 120 days), so no future data leaks in",
    "4. Every series now has variance 1 → total variance = 11; PCA on this = PCA on the correlation matrix",
  ]);
  s.addNotes("We do scale: the model standardises every window before PCA, and the daily gauge uses the correlation matrix, which is mathematically the same as PCA on StandardScaler output. We do not fit one scaler on 2010-2026 because that would use future information.");
}
{
  const s = content("Step 2 · PCA finds the market's “dance moves”");
  card(s, 0.6, 1.45, 5.6, 2.15, "Eigenvector = a dance move", "A pattern of movement shared by the currencies, e.g. “everyone steps left together” (all currencies move against the dollar).");
  card(s, 0.6, 3.8, 5.6, 2.15, "Eigenvalue = how much that move is used", "The amount of total movement (variance) explained by that pattern. Eigenvalues add up to the number of series: 11.");
  s.addText("Example with 2 currencies (EUR and GBP, correlation 0.8)", { x: 6.6, y: 1.45, w: 6.15, h: 0.4, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  table(s, [["Factor", "Recipe (EUR, GBP)", "Meaning", "Eigenvalue", "Share"],
    ["PC1", "+0.71, +0.71", "move together", "1.8", "90%"],
    ["PC2", "+0.71, −0.71", "move apart", "0.2", "10%"],
    ["Total", "", "", "2.0", "100%"]], 6.6, 2.0, 6.15, [0.8, 1.55, 1.5, 1.2, 1.1], { size: 14, rowH: 0.5, bold: (r) => r[0] === "Total" });
  card(s, 6.6, 4.25, 6.15, 1.7, "", [
    "PC2 is the EURGBP “leftover”: the small part where the two move apart. This is what pair analysis studies.",
    "With our 11 series: share of the first factor = largest eigenvalue / 11.",
  ]);
  s.addNotes("Two-year-old version: 11 kids dance; most of the time they all copy the teacher (the dollar). PCA finds the dance moves (eigenvectors) and how much each was used (eigenvalues). For two series the eigenvalues are 1 + correlation and 1 - correlation.");
}
{
  // conceptual pullback cycle (sine wave) with the trades it produces
  const n = 97, sv = [], sell = [], buy = [];
  for (let t = 0; t < n; t++) sv.push(+(3.0 * Math.sin((2 * Math.PI * t) / 32 + 0.3)).toFixed(2));
  let pos = 0;
  for (let t = 0; t < n; t++) {
    if (pos === 0 && sv[t] >= 2.5) pos = -1;
    else if (pos === 0 && sv[t] <= -2.5) pos = 1;
    sell.push(pos === -1 ? sv[t] : null); buy.push(pos === 1 ? sv[t] : null);
    if (pos === -1 && sv[t] <= 0.5) pos = 0;
    if (pos === 1 && sv[t] >= -0.5) pos = 0;
  }
  const labels = Array.from({ length: n }, (_, i) => `Day ${i}`);
  const s = content("Step 3 · The pullback: stretch, then return");
  s.addChart(pres.charts.LINE, [
    { name: "s-score (how stretched)", labels, values: sv },
    { name: "Short trade open", labels, values: sell },
    { name: "Long trade open", labels, values: buy },
    { name: "Entry ±2.5", labels, values: const_(n, 2.5) },
    { name: "Entry −2.5", labels, values: const_(n, -2.5) },
    { name: "Exit ±0.5", labels, values: const_(n, 0.5) },
    { name: "Exit −0.5", labels, values: const_(n, -0.5) },
  ], {
    x: 0.6, y: 1.35, w: 8.0, h: 5.4, ...chartBase("Idealised pullback cycle of a pair's PCA leftover"),
    chartColors: [GREY, RED, GREEN, GOLD, GOLD, SLATE, SLATE], lineSize: 2, lineDataSymbol: "none",
    valAxisMinVal: -4, valAxisMaxVal: 4, valAxisMajorUnit: 1, catAxisLabelFrequency: 16,
    showLegend: true, legendPos: "b", displayBlanksAs: "gap",
  });
  card(s, 8.95, 1.35, 3.8, 5.4, "Reading the wave", [
    "Gold lines ±2.5: stretched far from normal → open a trade",
    "Red: s above +2.5 → SELL the pair, expecting it to fall back",
    "Green: s below −2.5 → BUY the pair, expecting it to rise back",
    "Grey lines ±0.5: back near normal → take profit",
    "Beyond ±4 the rubber band has snapped → exit (stop)",
  ]);
  s.addNotes("This is an idealised wave to show the idea. Real pairs are noisier (next slides). The pullback is the leftover returning toward its middle; a trade is opened at the stretch and closed on the return.");
}
{
  const s = content("How the s-score is built");
  const steps = [
    ["1", "Leftover", "PCA removes the common forces. EURGBP leftover = euro's own move − pound's own move"],
    ["2", "Running total X", "Add the leftover up day by day: the “rubber band” line"],
    ["3", "Pull-back model", "Ornstein–Uhlenbeck fit on the last 120 days: X tomorrow = a + b·X today + noise. Needs 0 < b < 1"],
    ["4", "s-score", "s = (X − middle) / normal stretch. Middle m = a/(1−b), half-life = ln2 / −ln b"],
  ];
  steps.forEach(([n, t, b], i) => {
    const x = 0.6 + i * 3.1;
    s.addShape(pres.shapes.OVAL, { x: x + 1.05, y: 1.45, w: 0.75, h: 0.75, fill: { color: NAVY }, line: { color: NAVY }, objectName: `step ${n}` });
    s.addText(n, { x: x + 1.05, y: 1.45, w: 0.75, h: 0.75, fontSize: 22, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
    card(s, x, 2.4, 2.85, 2.6, t, b);
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.88, y: 3.5, w: 0.2, h: 0.35, fill: { color: GOLD }, line: { color: GOLD }, objectName: `arrow ${n}` });
  });
  card(s, 0.6, 5.25, 12.15, 1.5, "Why Ornstein–Uhlenbeck?", "Simplest model of “pulled back to a middle”: 3 parameters fit reliably on 120 days, gives middle, speed and normal stretch, and is the standard in PCA statistical arbitrage (Avellaneda & Lee, 2010). Alternatives: rolling z-score, cointegration tests, Kalman filter.", { size: 14 });
  s.addNotes("If b is not between 0 and 1 there is no pullback, so no s-score and no trade. The s-score is like a z-score for the pair's leftover: how many normal stretches away from the middle.");
}
{
  const n = EX.labels.length;
  const ent = EX.labels.indexOf(EX.entry), ext = EX.labels.indexOf(EX.exit);
  const inTrade = (arr) => arr.map((v, i) => (i >= ent && i <= ext ? v : null));
  const s = content("Real example: a pullback trade on EURGBP");
  s.addChart(pres.charts.LINE, [
    { name: "s-score", labels: EX.labels, values: EX.s },
    { name: "Trade open", labels: EX.labels, values: inTrade(EX.s) },
    { name: "Entry +2.5", labels: EX.labels, values: const_(n, 2.5) },
    { name: "Exit +0.5", labels: EX.labels, values: const_(n, 0.5) },
  ], {
    x: 0.6, y: 1.3, w: 7.9, h: 2.6, ...chartBase("EURGBP s-score, Sep – Nov 2024"),
    chartColors: [GREY, RED, GOLD, SLATE], lineSize: 2, lineDataSymbol: "none", catAxisLabelFrequency: 8,
    valAxisMinVal: -3, valAxisMaxVal: 3.5, valAxisMajorUnit: 1, showLegend: true, legendPos: "r", displayBlanksAs: "gap",
  });
  s.addChart(pres.charts.LINE, [
    { name: "EURGBP price", labels: EX.labels, values: EX.price },
    { name: "Trade open", labels: EX.labels, values: inTrade(EX.price) },
  ], {
    x: 0.6, y: 3.95, w: 7.9, h: 2.45, ...chartBase("EURGBP price"),
    chartColors: [SLATE, RED], lineSize: 2, lineDataSymbol: "none", catAxisLabelFrequency: 8,
    valAxisMinVal: 0.826, valAxisMaxVal: 0.846, valAxisLabelFormatCode: "0.000", valAxisMajorUnit: 0.005,
    showLegend: true, legendPos: "r", displayBlanksAs: "gap",
  });
  card(s, 8.85, 1.3, 3.9, 5.1, "The trade", [
    `31 Oct 2024: s = +${EX.s_entry}. After removing the dollar, the euro is unusually expensive against the pound`,
    `SELL EURGBP at ${EX.px_entry.toFixed(4)} (expected half-life ${EX.half_life} days)`,
    `6 Nov 2024: s back to +${EX.s_exit} → close at ${EX.px_exit.toFixed(4)}`,
    `Held ${EX.bars} days, price −${((1 - EX.px_exit / EX.px_entry) * 100).toFixed(2)}%`,
    `Result +${EX.net}% of the account after costs (${EX.cost}%)`,
  ], { size: 13 });
  caption(s, `Same days: EUR ${EX.eur_move}% and GBP ${EX.gbp_move}% against the dollar (US election week). PCA removed that dollar move; only euro vs pound was traded.`, 0.6, 6.45, 12.1, 0.45);
  s.addNotes("Actual trade from the 2019-2026 test, daily model (window 120 days, entry 2.5, exit 0.5). The rubber band stretched on 31 Oct and pulled back within 4 trading days.");
}
{
  const s = content("Step 4 · Testing the pullback: variance ratio");
  card(s, 0.6, 1.45, 3.85, 1.7, "VR = 1 · no leash", "Random walk. Wanders 10× as much in 10 days as in 1 day.");
  card(s, 4.75, 1.45, 3.85, 1.7, "VR < 1 · on a leash", "Moves get undone → pulls back. ✓", { titleColor: GREEN });
  card(s, 8.9, 1.45, 3.85, 1.7, "VR > 1 · chasing a squirrel", "Moves keep adding up → trends. ✗", { titleColor: RED });
  s.addText("VR(k) = variance of k-day moves ÷ (k × variance of 1-day moves)", { x: 0.6, y: 3.45, w: 12.15, h: 0.6, fontFace: "Cambria", fontSize: 24, color: NAVY, align: "center", isTextBox: true, margin: 0 });
  card(s, 0.6, 4.35, 12.15, 2.0, "Why variance, and why it matters", [
    "For a random walk, variance grows exactly in proportion to time, so any departure shows pull-back (<1) or trend (>1)",
    "No model is fitted, so it independently checks the OU s-score (Lo & MacKinlay, 1988)",
  ]);
  s.addNotes("Example: daily leftover variance 1. Random walk: 10-day variance 10, VR = 1. EURSEK measured 7.9, VR 0.79. Gold/silver measured 12, VR 1.20.");
}

// ============================================================================= GOLD / SILVER
section("Part 1 · Gold and silver");
divider("Part 1 · Gold and silver", "Why the PCA pullback fails for metals");
{
  const s = content("Gold and silver share most of their movement");
  s.addChart(pres.charts.BAR, [{ name: "Share %", labels: ["PC1 · all together", "PC2 · the dollar", "PC3 · silver vs gold"], values: D.gs_share.values }], {
    x: 0.6, y: 1.4, w: 6.6, h: 5.3, barDir: "col", ...chartBase("Variance explained (gold, silver, USD index; hourly 2019 – 2026)"),
    chartColors: [GOLD], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0\"%\"", showLegend: false, valAxisMaxVal: 80,
  });
  card(s, 7.6, 1.4, 5.15, 1.6, "PC1 · 68%", "Gold (0.63) and silver (0.62) rise when the dollar (−0.46) falls");
  card(s, 7.6, 3.2, 5.15, 1.4, "PC2 · 24%", "The dollar moving on its own (0.89)");
  card(s, 7.6, 4.8, 5.15, 1.9, "PC3 · 8%", "Silver vs gold (+0.72 / −0.69). The only leftover to trade, and it is small", { titleColor: RED });
}
{
  const s = content("The gold/silver ratio trends instead of returning");
  const yrs = D.gs_ratio.labels.map((l) => l.slice(0, 4));
  s.addChart(pres.charts.LINE, [{ name: "Gold / silver ratio", labels: yrs, values: D.gs_ratio.values }], {
    x: 0.6, y: 1.35, w: 8.6, h: 5.4, ...chartBase("Ounces of silver per ounce of gold, weekly 2010 – 2026"),
    chartColors: [GOLD], lineSize: 2, lineDataSymbol: "none", catAxisLabelFrequency: 104, showLegend: false, valAxisMinVal: 20,
  });
  card(s, 9.55, 1.35, 3.2, 1.6, "32 → 122", "Low in 2011, high in the 2020 COVID crash");
  card(s, 9.55, 3.15, 3.2, 1.6, "105 → 46", "Collapse in 2025 – 26 as silver surged");
  card(s, 9.55, 4.95, 3.2, 1.8, "5.2%", "Typical distance from its 1-year average (forex crosses: 1.4 – 3.9%)");
}
{
  const s = content("No pullback: variance ratio above 1 and rising");
  s.addChart([
    { type: pres.charts.BAR, data: [{ name: "Variance ratio", labels: D.gs_vr.labels, values: D.gs_vr.values }], options: { chartColors: [GOLD], barGapWidthPct: 60, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00" } },
    { type: pres.charts.LINE, data: [{ name: "1.0 = random walk", labels: D.gs_vr.labels, values: const_(4, 1) }], options: { chartColors: [RED], lineSize: 2, lineDataSymbol: "none", lineDash: "dash" } },
  ], {
    x: 0.6, y: 1.35, w: 6.0, h: 5.4, ...chartBase("Silver-vs-gold leftover, out-of-sample"),
    showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 1.6,
  });
  const rows = [["Year", "Trades", "Win %", "Return %"], ...D.gs_trades.map(([y, t, w, r]) => [y, t, w, (r > 0 ? "+" : "") + r.toFixed(1)])];
  s.addText("Trading the leftover anyway (costs included)", { x: 7.0, y: 1.35, w: 5.75, h: 0.4, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  table(s, rows, 7.0, 1.85, 5.75, [1.35, 1.4, 1.4, 1.6], { colColor: (r, j) => (j === 3 ? (parseFloat(r[3]) < 0 ? RED : GREEN) : INK) });
  caption(s, "104 trades · Sharpe −0.61 · 7 of 8 years negative", 7.0, 5.3, 5.75);
  s.addNotes("The longer we wait, the further the silver-vs-gold leftover drifts (1.20 at 10 days, 1.48 at 20). Even 2022 with a 68% win rate lost money because the few losing trades were large: the ratio kept trending.");
}

// ============================================================================= FOREX
section("Part 2 · Forex cross pairs");
divider("Part 2 · Forex cross pairs", "Where the pullback works");
{
  const s = content("Currencies move together, mostly through the dollar");
  s.addImage({ path: path.join(IMG, "forex", "correlation_heatmap.png"), x: 0.6, y: 1.3, w: 6.23, h: 5.4, altText: "Correlation heatmap of daily returns for 9 currencies, gold and silver, 2010-2026" });
  card(s, 7.25, 1.3, 5.5, 1.6, "Strongest links", "EUR–SEK 0.79, AUD–NZD 0.83, NOK–SEK 0.77: neighbouring economies");
  card(s, 7.25, 3.1, 5.5, 1.6, "Weakest link: JPY", "0.10 – 0.41 with others. The yen is a safe haven with its own story");
  card(s, 7.25, 4.9, 5.5, 1.8, "Metals", "Gold–silver 0.78 together, but only 0.19 – 0.42 with currencies");
  s.addNotes("Daily returns of each currency priced in US dollars. Every correlation is positive because the dollar moves all of them together.");
}
{
  const s = content("Three forces explain 72% of all movement");
  s.addChart(pres.charts.BAR, [{ name: "Share %", labels: D.fx_share.labels, values: D.fx_share.values }], {
    x: 0.6, y: 1.35, w: 5.2, h: 3.9, barDir: "col", ...chartBase("Variance explained by each factor, %"),
    chartColors: [NAVY], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showLegend: false,
  });
  s.addChart(pres.charts.BAR, [
    { name: "PC1 · dollar", labels: D.fx_load.labels, values: D.fx_load.PC1 },
    { name: "PC2 · currencies vs metals", labels: D.fx_load.labels, values: D.fx_load.PC2 },
    { name: "PC3 · risk-on vs safe havens", labels: D.fx_load.labels, values: D.fx_load.PC3 },
  ], {
    x: 6.1, y: 1.35, w: 6.65, h: 3.9, barDir: "col", ...chartBase("What each factor is made of (loadings)"),
    chartColors: [NAVY, GREEN, GOLD], showLegend: true, legendPos: "b", valAxisLabelFormatCode: "0.0",
  });
  card(s, 0.6, 5.45, 3.9, 1.3, "PC1 · 49% · the dollar", "Every currency moves the same way against USD", { size: 13 });
  card(s, 4.72, 5.45, 3.9, 1.3, "PC2 · 13% · metals", "Gold and silver vs the currencies", { size: 13 });
  card(s, 8.85, 5.45, 3.9, 1.3, "PC3 · 10% · risk mood", "AUD, NZD, CAD vs safe havens JPY, CHF", { size: 13 });
}
{
  const s = content("Forex leftovers pull back; gold/silver doesn't");
  const fx = D.fx_vr.labels.map((l, i) => (l === "GOLD/SILVER" ? 0 : D.fx_vr.values[i]));
  const gs = D.fx_vr.labels.map((l, i) => (l === "GOLD/SILVER" ? D.fx_vr.values[i] : 0));
  const lab = D.fx_vr.labels.map((l) => (l === "GOLD/SILVER" ? "GOLD/SLV" : l));
  s.addChart([
    { type: pres.charts.BAR, data: [{ name: "Forex cross", labels: lab, values: fx }, { name: "Gold / silver", labels: lab, values: gs }], options: { chartColors: [NAVY, GOLD], barGrouping: "stacked", barGapWidthPct: 40 } },
    { type: pres.charts.LINE, data: [{ name: "1.0 = random walk", labels: lab, values: const_(lab.length, 1) }], options: { chartColors: [RED], lineSize: 2, lineDataSymbol: "none", lineDash: "dash" } },
  ], {
    x: 0.6, y: 1.35, w: 12.15, h: 4.4, ...chartBase("Variance ratio of the PCA leftover over 10 days (below 1 = pulls back)"),
    showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 1.3, valAxisLabelFormatCode: "0.0", catAxisLabelRotate: -45, catAxisLabelFontSize: 10,
  });
  card(s, 0.6, 5.9, 3.9, 0.9, "15 of 23", "crosses below 1", { size: 13 });
  card(s, 4.72, 5.9, 3.9, 0.9, "0.79 · EURSEK", "strongest pullback", { size: 13 });
  card(s, 8.85, 5.9, 3.9, 0.9, "1.20 · gold/silver", "worst of all 24", { size: 13, titleColor: RED });
}
{
  const s = content("Trading the pullback, 2010 – 2026");
  const tr = D.fx_trades.map(([y, t, w, r]) => [y, t, w, (r > 0 ? "+" : "") + r.toFixed(1)]);
  const train = tr.filter((r) => r[0] < 2019), test = tr.filter((r) => r[0] >= 2019);
  const hdr = ["Year", "Trades", "Win %", "Return %"];
  const cc = (r, j) => (j === 3 ? (parseFloat(r[3]) < 0 ? RED : GREEN) : INK);
  s.addText("TRAIN 2010 – 2018 · settings chosen here", { x: 0.6, y: 1.3, w: 5.0, h: 0.4, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  table(s, [hdr, ...train], 0.6, 1.75, 5.0, [1.1, 1.2, 1.2, 1.5], { colColor: cc, rowH: 0.34, size: 12 });
  s.addText("TEST 2019 – 2026 · untouched", { x: 5.95, y: 1.3, w: 5.0, h: 0.4, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  table(s, [hdr, ...test], 5.95, 1.75, 5.0, [1.1, 1.2, 1.2, 1.5], { colColor: cc, rowH: 0.34, size: 12 });
  stat2(s);
  caption(s, "13 cross pairs, daily candles, entry |s| ≥ 2.5, exit at 0.5. Costs = Vantage spreads + commission, swap-free account. Supporting evidence only.", 0.6, 6.5, 12.1);
  function stat2(sl) {
    card(sl, 11.25, 1.3, 1.5, 2.3, "1.10", ["train Sharpe", "8.1%/yr"], { size: 12, titleSize: 20 });
    card(sl, 11.25, 3.8, 1.5, 2.3, "0.58", ["test Sharpe", "4.4%/yr"], { size: 12, titleSize: 20, titleColor: GREEN });
  }
}

// ============================================================================= WHEN NOT TO TRADE
section("Part 3 · When not to trade");
divider("Part 3 · When not to trade", "A daily PCA gauge of how much one force drives the market");
{
  const s = content("The daily gauge: share of the first factor");
  const steps = [
    ["1", "Collect", "Last 480 hourly returns (≈ 20 days) of the 11 instruments"],
    ["2", "Scale", "Correlation matrix 11 × 11 (each series variance 1)"],
    ["3", "PCA", "11 eigenvalues, adding up to 11"],
    ["4", "Share", "Largest eigenvalue ÷ 11"],
  ];
  steps.forEach(([n, t, b], i) => {
    const x = 0.6 + i * 3.1;
    s.addShape(pres.shapes.OVAL, { x: x + 1.05, y: 1.4, w: 0.7, h: 0.7, fill: { color: NAVY }, line: { color: NAVY }, objectName: `gauge step ${n}` });
    s.addText(n, { x: x + 1.05, y: 1.4, w: 0.7, h: 0.7, fontSize: 20, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
    card(s, x, 2.25, 2.85, 1.75, t, b);
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.88, y: 2.95, w: 0.2, h: 0.35, fill: { color: GOLD }, line: { color: GOLD }, objectName: `gauge arrow ${n}` });
  });
  card(s, 0.6, 4.25, 5.9, 2.5, "Example · 16 Oct 2026", [
    "Eigenvalues: 6.45, 1.23, 0.89, 0.58 … 0.11 (sum 11.0)",
    "Share = 6.45 ÷ 11 = 58.6%",
    "Cut-off 47.5% → tradable day ✓",
  ]);
  card(s, 6.85, 4.25, 5.9, 2.5, "Rule (uses past data only)", [
    "Cut-off = the level that one third of all previous days fell below (33rd percentile)",
    "Share ≤ cut-off → no-trade day: currencies are moving on their own news",
  ], { titleColor: RED });
}
{
  const s = content("The gauge, 2010 – 2026");
  const yrs = D.conc.labels.map((l) => l.slice(0, 4)), n = yrs.length;
  s.addChart(pres.charts.LINE, [
    { name: "First-factor share %", labels: yrs, values: D.conc.values },
    { name: `Bottom third ≤ ${D.conc.q1}%`, labels: yrs, values: const_(n, D.conc.q1) },
    { name: `Top third > ${D.conc.q2}%`, labels: yrs, values: const_(n, D.conc.q2) },
  ], {
    x: 0.6, y: 1.35, w: 7.4, h: 5.4, ...chartBase("Weekly average of the daily gauge"),
    chartColors: [NAVY, RED, GREY], lineSize: 2, lineDataSymbol: "none", catAxisLabelFrequency: 104,
    showLegend: true, legendPos: "b", valAxisMinVal: 20, valAxisMaxVal: 80,
  });
  const rows = [["When", "Event", "Share", "Cut-off", "Gauge"], ...D.events.map(([d, e, v, c, r]) => [d, e, v + "%", c + "%", r])];
  table(s, rows, 8.3, 1.35, 4.45, [0.8, 1.45, 0.7, 0.75, 0.75], {
    size: 11, rowH: 0.5,
    colColor: (r, j) => (j === 4 ? (r[4] === "no-trade" ? RED : GREEN) : INK), bold: (r, j) => j === 4,
  });
  caption(s, "Gauge one week after each shock. Crises that split currencies into safe vs risky (COVID, SNB, US downgrade) push the share DOWN; dollar-driven episodes (UK gilt crisis) push it up.", 8.3, 5.05, 4.45, 1.6);
}
{
  const s = content("When the gauge is low, pair relationships break");
  s.addChart(pres.charts.BAR, [
    { name: "Pulled back", labels: ["Low", "Medium", "High"], values: D.regime["snapped back"] },
    { name: "Broke further", labels: ["Low", "Medium", "High"], values: D.regime.broke },
    { name: "Neither", labels: ["Low", "Medium", "High"], values: D.regime.neither },
  ], {
    x: 0.6, y: 1.35, w: 6.6, h: 5.4, barDir: "col", ...chartBase("Stretched pairs (|s| ≥ 2): next 10 days, % by gauge level"),
    chartColors: [GREEN, RED, GREY], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", showLegend: true, legendPos: "b",
  });
  s.addText("Break rate, low vs high gauge", { x: 7.6, y: 1.35, w: 5.15, h: 0.4, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
  table(s, [["Period", "Low", "High"], ...D.break_period.map(([p, l, h]) => [p, l.toFixed(1) + "%", h.toFixed(1) + "%"])], 7.6, 1.85, 5.15, [1.85, 1.65, 1.65], {
    rowH: 0.42, colColor: (r, j) => (j === 1 ? RED : j === 2 ? GREEN : INK),
  });
  card(s, 7.6, 4.2, 2.45, 2.55, "3×", "more breaks in low periods (7.7% vs 2.3%), 3,345 events", { titleSize: 28, titleColor: RED, size: 13 });
  card(s, 10.3, 4.2, 2.45, 2.55, `${D.pairs_low_gt_high} of 23`, "pairs break more when the gauge is low", { titleSize: 28, size: 13 });
  s.addNotes("Low gauge = no single boss; each currency follows its own news (rate surprises, safe-haven flows), so the rubber bands between them snap. Holds in every period. Only AUDNZD is the exception.");
}
{
  const s = content("Days PCA marks as safe, per year");
  s.addChart(pres.charts.BAR, [{ name: "Tradable %", labels: D.tradable.labels, values: D.tradable.values }], {
    x: 0.6, y: 1.35, w: 8.6, h: 5.4, barDir: "col", ...chartBase("% of trading days above the cut-off (live rule)"),
    chartColors: [NAVY], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 110, valAxisMajorUnit: 20,
  });
  card(s, 9.55, 1.35, 3.2, 1.6, "69%", "of days tradable on average (≈ 180 per year)", { titleSize: 24 });
  card(s, 9.55, 3.15, 3.2, 1.6, "31 – 33%", "2013 – 14: Abenomics, central banks diverging", { titleSize: 24, titleColor: RED });
  card(s, 9.55, 4.95, 3.2, 1.8, "~10 days", "typical no-trade spell; the warning stays on for a while", { titleSize: 24, titleColor: GOLD });
}
{
  const s = content("Check on real trades");
  const pick = (strategy, period, day) => D.trades_regime.find((r) => r.strategy === strategy && r.period === period && r["opened on"] === day);
  const rows = [["Trades opened on", "Trades", "Win %", "Stopped out %", "Avg net per trade %"]];
  for (const [p, lab] of [["all", "2010 – 26"], ["2010-18", "2010 – 18"], ["2019-26", "2019 – 26"]]) {
    for (const [d, dl] of [["no-trade", "no-trade days"], ["trade", "trade days"]]) {
      const r = pick("forex D1, 13 crosses", p, d);
      rows.push([`${lab} · ${dl}`, r.trades, r["win %"].toFixed(0), r["stopped out %"].toFixed(1), r["avg net per trade %"].toFixed(2)]);
    }
  }
  table(s, rows, 0.6, 1.4, 7.6, [2.6, 1.0, 1.0, 1.4, 1.6], {
    size: 13, rowH: 0.48,
    rowFill: (r, i) => (r[0].includes("no-trade") ? "FBEDEB" : "FFFFFF"),
    colColor: (r, j) => (j === 3 && r[0].includes("no-trade") ? RED : INK), bold: (r, j) => j === 3,
  });
  card(s, 8.6, 1.4, 4.15, 2.45, "Supports the conclusion", ["Stop-losses hit 1.7× more often on no-trade days (13.4% vs 8.0%)", "2019 – 26: 0.04% vs 0.17% per trade"], { titleColor: GREEN });
  card(s, 8.6, 4.05, 4.15, 2.7, "Honest limit", ["2010 – 18: no-trade days earned more (bigger moves, bigger winners)", "So the gauge is a risk warning, not a profit rule"], { titleColor: RED });
}
{
  const s = content("Limits of this study");
  card(s, 0.6, 1.45, 3.85, 2.2, "Not every pair pulls back", "8 of 23 crosses have a variance ratio above 1 (e.g. AUDNZD 1.14)");
  card(s, 4.75, 1.45, 3.85, 2.2, "Breakdowns are the tail", "The gauge changes the break rate a lot; the chance of pulling back only moves 39 – 45%");
  card(s, 8.9, 1.45, 3.85, 2.2, "Trading costs", "Results are swap-free. With worst-case swap the 2019 – 26 test was about flat");
  card(s, 0.6, 3.95, 5.95, 1.9, "Scope", "Tested on 23 cross pairs. USD pairs themselves, exotics, indices and crypto not tested");
  card(s, 6.8, 3.95, 5.95, 1.9, "Per-pair numbers are small", "About 2 – 15 breaks per pair. The evidence is the pattern across all 23 together");
}
{
  const s = newSlide({ masterName: "TITLE", sectionTitle: SECTION });
  s.addText("PCA tells us when not to trust pair relationships", { placeholder: "title" });
  s.addText([
    { text: "Forex cross leftovers pull back; gold/silver trends and fails", options: { bullet: true, breakLine: true } },
    { text: "When one common force explains less of the market than on two-thirds of past days, stretched pairs break about 3× more often", options: { bullet: true, breakLine: true } },
    { text: "A simple daily PCA gauge, using past data only, flags those periods: about one-third of days", options: { bullet: true } },
  ], { placeholder: "body" });
}

pres.writeFile({ fileName: OUT }).then(async () => {
  if (applyTheme && !process.env.NO_THEME) await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
});
