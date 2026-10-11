# -*- coding: utf-8 -*-
"""區網測試模式的守門邏輯（P-008／P-041／P-043；設計 W-B DESIGN r2 §2）。

預設關閉：只有 `serve.py <port> --lan <IPv4>` 明示才會用到本模組的設定與守門。
本模組不 import cryptography、不開任何 socket、不改任何系統設定；
NetworkCategory 只做唯讀查詢，查詢函式可注入（測試用）。

serve.py 的 LanHandler 在 `parse_request` 之後、任何 `do_*` 分派之前呼叫 `LanGate.check()`；
拒絕一律空白 403，拒絕原因只記在 `LanGate.denials`（測試觀察用，永不送給對端）。
"""
import argparse
import collections
import hashlib
import hmac
import ipaddress
import os
import pathlib
import secrets
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

RFC1918 = tuple(ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
FORBIDDEN_PORT = 8765                  # 日常服務埠：區網模式一律另開
COOKIE_NAME = "__Host-geometry-lan"
PAIR_PATH = "/lan/pair"
CA_PATH = "/lan/ca.cer"
PAIR_MAX_BYTES = 128
CATEGORY_TIMEOUT = 10.0
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CODE_LENGTH = 26                      # 128 位元 → 26 個 base32 字元
_CONFUSABLE = str.maketrans({"O": "0", "I": "1", "L": "1"})
LAN_FLAGS = ("--lan", "--lan-ttl", "--lan-idle", "--lan-devices", "--lan-cert-days",
             "--lan-serve-ca", "--lan-forget")


class LanRefused(Exception):
    """區網模式拒絕啟動。serve.py 以 exit 2 結束，loopback 也不啟動（fail-closed）。"""


@dataclass(frozen=True)
class LanConfig:
    ip: str
    port: int
    ttl: float = 120 * 60              # 秒；TTL 到期必關
    idle: float = 30 * 60              # 秒；只有帶有效 cookie 的請求重設
    devices: int = 1                   # 每台一組單次使用的配對碼
    cert_days: int = 7
    serve_ca: bool = False             # 只有明示 --lan-serve-ca 才在區網提供 /lan/ca.cer
    pair_ttl: float = 600.0            # 配對碼有效 10 分鐘
    pair_interval: float = 1.0         # 全域：每秒 ≤1 次配對嘗試
    max_connections: int = 32          # 非阻塞上限
    header_deadline: float = 10.0      # accept → TLS 交握 → 請求列 → 全部標頭 的總期限
    poll: float = 1.0                  # 計時執行緒與標頭期限巡檢的週期

    @property
    def host(self):
        return f"{self.ip}:{self.port}"

    @property
    def origin(self):
        return f"https://{self.ip}:{self.port}"


# ------------------------------------------------------------------ 旗標與啟動前檢查

def lan_requested(argv):
    """argv（serve.py 的 sys.argv[2:]）是否帶任何 --lan 系列旗標；沒有就走原本的無旗標路徑。"""
    return any(arg == "--lan" or arg.startswith(("--lan-", "--lan=")) for arg in argv)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise LanRefused(f"旗標錯誤：{message}")


def parse_args(argv):
    parser = _Parser(prog="serve.py <port>", add_help=False, allow_abbrev=False)
    parser.add_argument("--lan", metavar="IPv4")
    parser.add_argument("--lan-ttl", type=int, default=120, metavar="分鐘")
    parser.add_argument("--lan-idle", type=int, default=30, metavar="分鐘")
    parser.add_argument("--lan-devices", type=int, default=1)
    parser.add_argument("--lan-cert-days", type=int, default=7)
    parser.add_argument("--lan-serve-ca", action="store_true")
    parser.add_argument("--lan-forget", action="store_true")
    return parser.parse_args(argv)


CATEGORY_COMMAND = ("& { param($ip) (Get-NetConnectionProfile -InterfaceIndex "
                    "(Get-NetIPAddress -IPAddress $ip -ErrorAction Stop).InterfaceIndex "
                    "-ErrorAction Stop).NetworkCategory }")


def query_network_category(ip, *, run=subprocess.run, timeout=CATEGORY_TIMEOUT):
    """唯讀查詢 <ip> 所屬介面的 NetworkCategory（不改任何設定）。

    ip 先經 ipaddress 正規化（只剩數字與點），再作為獨立 argv 元素交給 PowerShell 的 param($ip)。
    查不到介面、沒有設定檔、逾時都由呼叫端視為拒絕。
    """
    ip = str(ipaddress.IPv4Address(ip))
    result = run(["powershell", "-NoProfile", "-NonInteractive", "-Command", CATEGORY_COMMAND, ip],
                 capture_output=True, text=True, errors="replace", timeout=timeout)
    if result.returncode != 0:
        raise LanRefused(f"查不到 {ip} 所屬的網路介面或網路設定檔（該 IP 可能不屬本機）")
    return result.stdout.strip()


def validate(args, *, port, repo_root, platform=None, environ=None, category_query=None, crypto_check=None):
    """`--lan` 的全部啟動前條件；任一不符就 LanRefused（serve.py → exit 2，不開任何監聽）。"""
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ
    category_query = query_network_category if category_query is None else category_query
    if not args.lan:
        raise LanRefused("缺少 --lan <IPv4>")
    if platform != "win32":
        raise LanRefused("區網測試模式 v1 只支援 Windows（start.ps1 入口；WSL2 NAT 下區網 IP 不在 WSL 內）")
    try:
        address = ipaddress.IPv4Address(args.lan)
    except ValueError:
        raise LanRefused("--lan 必須是 IPv4 字面值（例如 192.168.1.23）") from None
    if str(address) != args.lan:
        raise LanRefused(f"--lan 請用標準寫法 {address}")
    if not any(address in network for network in RFC1918):
        raise LanRefused(f"{address} 不在 RFC1918 私有位址（10/8、172.16/12、192.168/16）內；"
                         "0.0.0.0、loopback、link-local、CGNAT 等一律拒絕")
    if port == FORBIDDEN_PORT:
        raise LanRefused(f"不得在日常埠 {FORBIDDEN_PORT} 開區網模式；請另選一個埠")
    for name, value, low, high in (("--lan-ttl", args.lan_ttl, 1, 480), ("--lan-idle", args.lan_idle, 1, 480),
                                   ("--lan-devices", args.lan_devices, 1, 3),
                                   ("--lan-cert-days", args.lan_cert_days, 1, 7)):
        if not low <= value <= high:
            raise LanRefused(f"{name} 必須介於 {low} 與 {high} 之間")
    feedback = environ.get("GEOMETRY_FEEDBACK_DIR")
    if not feedback:
        raise LanRefused("必須設定獨立的 GEOMETRY_FEEDBACK_DIR（手機回報不得混進 repository 的 feedback/）")
    feedback, root = pathlib.Path(feedback).resolve(), pathlib.Path(repo_root).resolve()
    if feedback == root or root in feedback.parents:
        raise LanRefused("GEOMETRY_FEEDBACK_DIR 不得位於 repository 內")
    if environ.get("GEOMETRY_MANAGED_PREVIEW") == "1":
        raise LanRefused("受管預覽（GEOMETRY_MANAGED_PREVIEW）不得與區網測試模式並用")
    if crypto_check is not None:
        crypto_check()
    try:
        category = category_query(str(address))
    except LanRefused:
        raise
    except Exception as exc:  # 逾時、找不到 powershell、權限……一律 fail-closed
        raise LanRefused(f"無法確認 {address} 所屬網路的設定檔（{type(exc).__name__}）；查不到一律拒絕") from None
    if category != "Private":
        raise LanRefused(f"{address} 所屬網路的設定檔是 {category or '（空白）'}，不是 Private；"
                         "公用網路一律拒絕（要不要改成私人是你的安全決定，見 README 區網測試模式 U7）")
    return LanConfig(ip=str(address), port=port, ttl=args.lan_ttl * 60, idle=args.lan_idle * 60,
                     devices=args.lan_devices, cert_days=args.lan_cert_days, serve_ca=args.lan_serve_ca)


# ------------------------------------------------------------------ 配對碼

def new_code():
    value = int.from_bytes(secrets.token_bytes(16), "big")
    return "".join(CROCKFORD[(value >> (5 * i)) & 31] for i in reversed(range(_CODE_LENGTH)))


def format_code(code):
    return "-".join(code[i:i + 4] for i in range(0, len(code), 4))


def normalize_code(raw):
    """不分大小寫、忽略 - 與空白、O→0、I/L→1；非 ASCII 視為空碼。"""
    try:
        text = raw.decode("ascii") if isinstance(raw, bytes) else str(raw)
        text.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return ""
    return "".join(text.split()).replace("-", "").upper().translate(_CONFUSABLE)


def cookie_values(headers):
    values = []
    for line in headers.get_all("Cookie") or []:
        for part in line.split(";"):
            name, sep, value = part.strip().partition("=")
            if sep and name == COOKIE_NAME:
                values.append(value)
    return values


def _digest(token):
    return hashlib.sha256(token.encode("utf-8", "replace")).hexdigest()


session_digest = _digest   # serve.py 以它對應「哪台裝置的獨立世界」；伺服器從不保存 cookie 原值


def _printable(text, limit=120):
    return "".join(ch for ch in (text or "") if ch.isprintable())[:limit]


class _Code:
    __slots__ = ("value", "expires", "used")

    def __init__(self, value, expires):
        self.value, self.expires, self.used = value, expires, False


# ------------------------------------------------------------------ 每請求守門與生命週期

class LanGate:
    """配對碼、session、限速、閒置與關閉狀態。所有方法執行緒安全。"""

    def __init__(self, config, *, clock=time.monotonic, log=None):
        self.config = config
        self.clock = clock
        self.log = log or (lambda line: print(line, file=sys.stderr, flush=True))
        self.lock = threading.Lock()
        now = clock()
        self.started = now
        self.last_activity = now
        self.closed = False
        self.close_reason = None
        self.codes = [_Code(new_code(), now + config.pair_ttl) for _ in range(config.devices)]
        self.paired = 0
        self.sessions = set()          # 只存 SHA-256
        self.last_attempt = None
        self.denials = collections.Counter()

    # -- 守門（DESIGN §2.3 第 1–7 條）
    def check(self, method, target, headers):
        """回傳 (route, reason)。route 為 None ＝拒絕；否則是 pair-page／pair-submit／ca／app。"""
        with self.lock:
            route, reason = self._check(method, target, headers)
            if route is None:
                self.denials[reason] += 1
            elif route == "app":
                self.last_activity = self.clock()   # 只有帶有效 cookie 且全部通過的請求重設閒置
            return route, reason

    def _check(self, method, target, headers):
        config = self.config
        if self.closed or self._expired(self.clock()):
            return None, "closed"
        if not target.startswith("/"):
            return None, "target"
        hosts = headers.get_all("Host") or []
        if len(hosts) != 1 or hosts[0] != config.host:
            return None, "host"
        origins = headers.get_all("Origin") or []
        if len(origins) > 1 or (origins and origins[0] != config.origin):
            return None, "origin"
        sites = headers.get_all("Sec-Fetch-Site") or []
        if len(sites) > 1 or (sites and sites[0] not in ("same-origin", "none")):
            return None, "fetch-site"
        if method == "GET" and target == PAIR_PATH:
            return "pair-page", None
        if method == "POST" and target == PAIR_PATH:
            return "pair-submit", None
        if config.serve_ca and method == "GET" and target == CA_PATH:
            return "ca", None
        values = cookie_values(headers)
        if len(values) != 1 or _digest(values[0]) not in self.sessions:
            return None, "cookie"
        if method != "GET" and not origins:
            return None, "origin-required"
        return "app", None

    def _expired(self, now):
        return now >= self.started + self.config.ttl or now >= self.last_activity + self.config.idle

    # -- 配對（DESIGN §2.2）
    def take_pair_slot(self):
        """全域限速：距上一次「被評估」的嘗試未滿 pair_interval 就 False（429，不評估、不消耗）。"""
        with self.lock:
            now = self.clock()
            if self.last_attempt is not None and now - self.last_attempt < self.config.pair_interval:
                return False
            self.last_attempt = now
            return True

    def redeem(self, raw, *, peer, user_agent=""):
        """比對配對碼；成功回傳 (token, max_age)，失敗回傳 None。stderr 只印時間與對端，不印嘗試內容。"""
        stamp = time.strftime("%H:%M:%S")
        with self.lock:
            now = self.clock()
            if self.closed or self._expired(now):
                return None
            attempt = normalize_code(raw)
            matched = None
            for entry in self.codes:
                same = hmac.compare_digest(entry.value, attempt)
                if same and matched is None and not entry.used and now < entry.expires:
                    matched = entry
            if matched is None:
                self.log(f"區網配對失敗 {stamp} 對端 {peer}")
                return None
            matched.used = True
            self.paired += 1
            token = secrets.token_urlsafe(32)
            self.sessions.add(_digest(token))
            max_age = max(0, int(self.started + self.config.ttl - now))
            self.log(f"區網已配對 第 {self.paired}/{self.config.devices} 台 {stamp} 對端 {peer} "
                     f"UA {_printable(user_agent)}（不是你的裝置 → 立刻 Ctrl+C）")
            return token, max_age

    # -- 生命週期（DESIGN §2.5）
    def poll(self):
        """計時執行緒每 config.poll 秒呼叫；該關閉時關閉並回傳原因，否則 None。"""
        with self.lock:
            if self.closed:
                return None
            now = self.clock()
            reason = None
            if now >= self.started + self.config.ttl:
                reason = "TTL 到期"
            elif now >= self.last_activity + self.config.idle:
                reason = "閒置逾時"
            elif self.paired == 0 and all(now >= entry.expires for entry in self.codes):
                reason = "配對碼已全部過期且沒有裝置配對"
            if reason:
                self._close(reason)
            return reason

    def close(self, reason):
        with self.lock:
            if not self.closed:
                self._close(reason)

    def _close(self, reason):
        self.closed = True
        self.close_reason = reason
        self.sessions.clear()
        self.codes.clear()

    def display_codes(self):
        with self.lock:
            return [format_code(entry.value) for entry in self.codes if not entry.used]


# ------------------------------------------------------------------ 配對頁與啟動提示

PAIR_PAGE_CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                 "connect-src 'self'")

# 自足 HTML：不載任何外部或站內資源（不載 feedback.js）；腳本第一步抹掉網址片段再送出。
PAIR_PAGE = """<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>區網測試配對</title>
<style>
body{font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;margin:24px auto;max-width:30em;padding:0 16px}
input,button{font:inherit;padding:8px;box-sizing:border-box}
input{width:100%;letter-spacing:.05em;margin-bottom:8px}
ul{padding:0}li{list-style:none}.ok{color:#176b2c}.bad{color:#a11}
</style>
<h1>區網測試配對</h1>
<p>輸入電腦終端機印出的配對碼（每組限一台、10 分鐘內有效）。若瀏覽器先跳出憑證警告，請停止，不要繼續。</p>
<form id="f"><input id="code" autocomplete="off" autocapitalize="characters" spellcheck="false" aria-label="配對碼"><button>配對</button></form>
<p id="msg" role="status"></p>
<ul id="checks" hidden></ul>
<p id="go" hidden><a href="/">進入應用</a></p>
<script>
(function () {
  var m = /^#c=([0-9A-Za-z -]{1,64})$/.exec(location.hash);
  var initial = m ? m[1] : '';
  history.replaceState(null, '', '/lan/pair');
  var msg = document.getElementById('msg');
  function show(text, cls) { msg.textContent = text; msg.className = cls || ''; }
  function selfCheck() {
    var list = document.getElementById('checks');
    var items = [
      ['isSecureContext', window.isSecureContext === true],
      ['crypto.randomUUID', !!(window.crypto && typeof crypto.randomUUID === 'function')],
      ['crypto.subtle', !!(window.crypto && crypto.subtle)],
      ['navigator.locks', !!navigator.locks]
    ];
    var all = true;
    list.textContent = '';
    items.forEach(function (item) {
      var li = document.createElement('li');
      li.textContent = (item[1] ? '通過 ' : '未通過 ') + item[0];
      li.className = item[1] ? 'ok' : 'bad';
      all = all && item[1];
      list.appendChild(li);
    });
    list.hidden = false;
    document.getElementById('go').hidden = false;
    show(all ? '配對成功，四項自檢全部通過。' : '配對成功，但自檢有項目未通過：這個瀏覽器的驗收請標「未做」並回報。',
         all ? 'ok' : 'bad');
  }
  function pair(code) {
    show('配對中…');
    fetch('/lan/pair', {method: 'POST', body: code, credentials: 'same-origin', cache: 'no-store'}).then(function (r) {
      if (r.status === 204) selfCheck();
      else if (r.status === 429) show('嘗試太頻繁，請等一秒再按一次。', 'bad');
      else show('配對失敗（碼錯、已用過、已過期，或服務已關閉）。', 'bad');
    }, function () { show('連不上服務。', 'bad'); });
  }
  document.getElementById('f').addEventListener('submit', function (e) {
    e.preventDefault();
    pair(document.getElementById('code').value);
  });
  if (initial) pair(initial);
})();
</script>
</html>
""".encode("utf-8")


def announce(config, gate, *, ca_path, fingerprint, reused, pairing_path, tty, log):
    """啟動提示（stderr）。配對碼只在 TTY 印；非 TTY 寫入私有目錄的 pairing.txt，只印路徑。"""
    closes_at = time.strftime("%H:%M", time.localtime(time.time() + config.ttl))
    log("警告：區網測試模式已開啟（只限本次）")
    log(f"  介面 https://{config.ip}:{config.port}/（本機 http://localhost:{config.port}/ 不變）")
    log(f"  最晚 {closes_at} 自動關閉（TTL {int(config.ttl // 60)} 分；閒置 {int(config.idle // 60)} 分；"
        "配對碼過期且無裝置配對也立即關閉）")
    log(f"  根憑證檔 {ca_path}（{'沿用既有憑證，已裝過的手機不必重裝' if reused else '新發憑證：手機須重新安裝並移除舊描述檔'}）")
    log(f"  根憑證 SHA-256 {fingerprint}")
    log("  安裝前在手機上核對 SHA-256（至少頭尾各 16 字，建議全 64 字）；不一致＝被調包，立刻刪除並停止")
    if config.serve_ca:
        log(f"  注意：已開 --lan-serve-ca，可從 https://{config.ip}:{config.port}{CA_PATH} 下載根憑證。"
            "區網下載可被調包；調包的根可攔截手機上全部 HTTPS——必須全比 64 字指紋")
    codes = gate.display_codes()
    if tty:
        for index, code in enumerate(codes, 1):
            log(f"  配對碼 第 {index}/{len(codes)} 台（限用一次、10 分鐘）：{code}")
    else:
        path = pathlib.Path(pairing_path)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("".join(f"{code}\n" for code in codes))
        log(f"  配對碼 ×{len(codes)} 已寫入 {path}（輸出不是終端機，所以不印；各限 1 台、10 分鐘）")
    log(f"  手機開 https://{config.ip}:{config.port}{PAIR_PATH} 輸入配對碼（請在網址列輸入或貼上，不要從網頁連結點開）")
    log("  立即關閉：Ctrl+C；用完移除手機描述檔（見 geometry-web/README.md「區網測試模式」）")
