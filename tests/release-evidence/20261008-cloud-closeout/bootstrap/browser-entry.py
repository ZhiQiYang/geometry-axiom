import json, pathlib, time
from playwright.sync_api import sync_playwright

out = pathlib.Path('/workspace/closure-evidence/bootstrap')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', chromium_sandbox=True, headless=True, timeout=20000)
    page = browser.new_page()
    response = page.goto('http://127.0.0.1:18990/', wait_until='domcontentloaded', timeout=15000)
    result = {'browser': browser.version, 'sandbox_requested': True, 'status': response.status, 'url': page.url, 'title': page.title(), 'body': page.locator('body').inner_text()}
    assert result['status'] == 200 and 'Directory listing' in result['title']
    page.screenshot(path=str(out/'browser-entry.png'))
    (out/'browser-entry-result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    browser.close()
