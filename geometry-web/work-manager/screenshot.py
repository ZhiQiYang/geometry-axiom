"""Capture a running local work dashboard without uploading screenshots.

Optional runtime dependency: preinstalled Python Playwright and Chromium.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description="截取工作面板（私存 desktop 與 390px）")
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / ".local" / "screenshots")
    parser.add_argument("--chromium", default=shutil.which("chromium") or shutil.which("google-chrome"))
    parser.add_argument("--full-page", action="store_true", help="截取完整長頁（預設為可讀的實際 viewport）")
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost"} or url.username or url.password:
        parser.error("截圖 URL 必須是本工具的 loopback http URL")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        parser.error("本環境沒有 Playwright；工具不會自動安裝。可在瀏覽器使用系統截圖。")
    args.out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    evidence = {"url": args.url, "screenshots": [], "errors": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True)
        try:
            for label, width, height in (("desktop", 1440, 1000), ("mobile-390", 390, 844)):
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.on("pageerror", lambda error: evidence["errors"].append(str(error)))
                page.goto(args.url, wait_until="networkidle")
                page.wait_for_function("() => document.body.dataset.stateHash || document.querySelector('[data-state-hash]')")
                identity = page.evaluate("""() => ({title: document.title,
                    state_hash: document.body.dataset.stateHash || document.querySelector('[data-state-hash]')?.dataset.stateHash,
                    viewport: innerWidth, document_width: document.documentElement.scrollWidth})""")
                if identity["document_width"] > width:
                    raise RuntimeError(f"{label}: 內容超出視窗寬度")
                output = args.out_dir / f"{label}.png"
                page.screenshot(path=str(output), full_page=args.full_page)
                os.chmod(output, 0o600)
                evidence["screenshots"].append({"path": str(output), **identity})
                page.close()
        finally:
            browser.close()
    output = args.out_dir / "capture.json"
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(output, 0o600)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 1 if evidence["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
