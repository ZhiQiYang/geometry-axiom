import { load, find } from "./cssq.mjs";
const D = process.env.TEMP + "/u123main/";
const sm = load(D + "space-workspace.css"), app = load(D + "app.css"), gi = load(D + "grid-inspector.css"), ig = load(D + "grid-system-workspace.css");
const show = (title, rules, re, props) => {
  console.log("\n### " + title);
  for (const r of find(rules, re)) {
    const body = props ? r.body.split(";").map(s => s.trim()).filter(s => props.test(s)).join("; ") : r.body;
    if (!body) continue;
    console.log((r.media ? "[" + r.media + "] " : "") + r.sel.slice(0, 110) + " { " + body.slice(0, 260) + " }");
  }
};
console.log("rules: sm=" + sm.length + " app=" + app.length + " gi=" + gi.length + " ig=" + ig.length);
// F1 breakpoint
show("F1 sm @media rules (all, selectors containing welcome/view/stage/canvas/steps/source-actions)", sm, /welcome|sm-view|sm-stage|sm-canvas-wrap|sm-steps|sm-source-actions|sm-header|sm-metrics|sm-display/, /display|height|flex|position|padding|margin|grid|top|bottom|min|max|overflow/);
// F5
show("F5 .sm-button / primary / checkbox / focus", sm, /\.sm-button|sm-primary|:focus-visible|sm-display-options input|sm-eyebrow/, /height|min-height|padding|border-radius|background|color|outline|letter-spacing|accent|box-shadow|text-transform/);
// F6
show("F6 .sm-help / .sm-guide font-size & line-height", sm, /sm-help|sm-guide|sm-view-direction|small|\.sm-section p|sm-gesture|sm-source-summary/, /font-size|line-height|color/);
// X6 zoom bars
show("X6 app.css zoom bars", app, /canvas-controls|face-canvas-controls|v3ZoomBar|minimap-shell|face-coordinate-readout|zoom-level|mini-toggle/, /position|top|right|bottom|left|display|gap|z-index/);
show("X6 grid ig-zoombar", ig, /ig-zoombar|ig-zoom|ig-hint/, /position|top|right|bottom|left|display|gap|font|min-width/);
show("X6 sm view tools / fit", sm, /sm-view|smFit|sm-canvas-wrap/, /position|top|right|bottom|left|display|gap/);
// G3
show("G3 gi-delete / gi-actions", gi, /gi-delete|gi-actions|gi-header|gi-footer|gridObjectDelete|gi-open/, null);
// B6 selection-summary
show("B6 selection-summary visibility rules", app, /selection-summary|selection-copy/, /display|position|top|left|right|opacity|visibility|pointer|max-width/);
