// Read-only CSS rule extractor (handles minified CSS and @media nesting). No dependencies.
import fs from "node:fs";
export function parse(src) {
  const out = []; let i = 0; const stack = []; let buf = "";
  src = src.replace(/\/\*[\s\S]*?\*\//g, "");
  const media = () => stack.filter(s => s.startsWith("@")).join(" > ");
  for (; i < src.length; i++) {
    const c = src[i];
    if (c === "{") { stack.push(buf.trim()); buf = ""; }
    else if (c === "}") {
      const top = stack.pop();
      if (buf.trim() && top !== undefined && !top.startsWith("@")) out.push({ sel: top, body: buf.trim(), media: media() });
      buf = "";
    } else if (c === ";" && stack.length && stack[stack.length - 1].startsWith("@") && !buf.includes("{")) { buf += c; }
    else buf += c;
  }
  return out;
}
export function find(rules, re) { return rules.filter(r => re.test(r.sel)); }
export function load(path) { return parse(fs.readFileSync(path, "utf8")); }
