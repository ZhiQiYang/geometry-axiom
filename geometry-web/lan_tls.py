# -*- coding: utf-8 -*-
"""區網測試模式的 TLS 材料（W-B DESIGN r2 §2.4）。

`cryptography` 惰性載入：缺套件時 `--lan` 以 exit 2 拒絕，絕不退回 http（不新增 CI 相依）。
CA：ECDSA P-256、critical BasicConstraints(ca, pathLen 0)、critical KeyUsage(keyCertSign, cRLSign)、
critical NameConstraints(只許 <ip>/32)；CA 私鑰從不序列化，簽完葉憑證即解除參照。
葉憑證：SAN 只有 IPAddress(<ip>)、EKU serverAuth、KeyUsage(digitalSignature)、ca=False，效期 ≤ CA（≤7 天）。
存放 %LOCALAPPDATA%\\geometry-lan\\<ip>-<port>\\（不在 repository 內、不另動 ACL）。

    python geometry-web/lan_tls.py --forget     # 刪除 %LOCALAPPDATA%\\geometry-lan\\（保存的伺服器憑證）
"""
import datetime
import hashlib
import ipaddress
import json
import os
import pathlib
import shutil
import ssl
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lan_guard import LanRefused  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
REUSE_MIN_REMAINING = datetime.timedelta(hours=1)
LEAF_CN = "geometry-web LAN test"
CA_CN = "geometry-web LAN test CA"


@dataclass(frozen=True)
class Material:
    directory: pathlib.Path
    leaf_path: pathlib.Path
    key_path: pathlib.Path
    ca_path: pathlib.Path
    ca_der: bytes
    fingerprint: str
    not_after: datetime.datetime
    reused: bool

    @property
    def pairing_path(self):
        return self.directory / "pairing.txt"


def require():
    try:
        import cryptography  # noqa: F401
    except ImportError:
        raise LanRefused("缺少 Python 套件 cryptography；區網模式只走 HTTPS，不退回 http") from None


def _inside(path, root):
    path, root = pathlib.Path(path).resolve(), pathlib.Path(root).resolve()
    return path == root or root in path.parents


def base_directory(environ=None, *, repo_root=REPO):
    environ = os.environ if environ is None else environ
    local = environ.get("LOCALAPPDATA")
    if not local:
        raise LanRefused("找不到 %LOCALAPPDATA%，無法存放伺服器憑證")
    base = (pathlib.Path(local) / "geometry-lan").resolve()
    if _inside(base, repo_root):
        raise LanRefused("伺服器憑證目錄不得位於 repository 內")
    return base


def state_directory(ip, port, environ=None, *, repo_root=REPO):
    ip = str(ipaddress.IPv4Address(ip))
    return base_directory(environ, repo_root=repo_root) / f"{ip}-{int(port)}"


def fingerprint(der):
    digest = hashlib.sha256(der).hexdigest().upper()
    return ":".join(digest[i:i + 2] for i in range(0, len(digest), 2))


def _not_after(cert):
    value = getattr(cert, "not_valid_after_utc", None)
    return value if value is not None else cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)


def issue(ip, days, now=None):
    """簽發 (葉憑證 PEM, 葉私鑰 PEM, 根憑證 DER)。CA 私鑰只存在於本函式的區域變數。"""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    if not 1 <= int(days) <= 7:
        raise LanRefused("憑證效期必須介於 1 與 7 天之間")
    address = ipaddress.IPv4Address(ip)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    start, end = now - datetime.timedelta(minutes=5), now + datetime.timedelta(days=int(days))

    def usage(**granted):
        names = ("digital_signature", "content_commitment", "key_encipherment", "data_encipherment",
                 "key_agreement", "key_cert_sign", "crl_sign", "encipher_only", "decipher_only")
        return x509.KeyUsage(**{name: granted.get(name, False) for name in names})

    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"{CA_CN} {address}")])
    ca_cert = (x509.CertificateBuilder()
               .subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
               .serial_number(x509.random_serial_number()).not_valid_before(start).not_valid_after(end)
               .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
               .add_extension(usage(key_cert_sign=True, crl_sign=True), critical=True)
               .add_extension(x509.NameConstraints(
                   permitted_subtrees=[x509.IPAddress(ipaddress.ip_network(f"{address}/32"))],
                   excluded_subtrees=None), critical=True)
               .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
               .sign(ca_key, hashes.SHA256()))
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    leaf = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, LEAF_CN)]))
            .issuer_name(ca_name).public_key(leaf_key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(start).not_valid_after(end)
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(address)]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(usage(digital_signature=True), critical=True)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))
    del ca_key  # CA 私鑰從不序列化；簽完即解除參照，之後只剩公開的根憑證
    return (leaf.public_bytes(serialization.Encoding.PEM),
            leaf_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                   serialization.NoEncryption()),
            ca_cert.public_bytes(serialization.Encoding.DER))


def _write(path, data, private=False):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0),
                         0o600 if private else 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def _reusable(ip, port, directory, now):
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    if meta.get("ip") != ip or meta.get("port") != port:
        return None
    leaf = x509.load_pem_x509_certificate((directory / "leaf.pem").read_bytes())
    ca_der = (directory / "ca.cer").read_bytes()
    ca = x509.load_der_x509_certificate(ca_der)
    key = serialization.load_pem_private_key((directory / "leaf.key").read_bytes(), password=None)
    san = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    leaf.verify_directly_issued_by(ca)
    if (san.get_values_for_type(x509.IPAddress) != [ipaddress.IPv4Address(ip)] or len(list(san)) != 1
            or key.public_key().public_numbers() != leaf.public_key().public_numbers()
            or _not_after(leaf) - now < REUSE_MIN_REMAINING):
        return None
    return ca_der, _not_after(leaf)


def load_or_issue(ip, port, days, directory, now=None):
    """同 IP／埠且葉憑證剩餘效期 ≥1 小時就沿用（服務重啟不必重裝描述檔），否則重發。"""
    directory = pathlib.Path(directory)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    try:
        reused = _reusable(ip, port, directory, now)
    except Exception:  # 缺檔、壞檔、不同版本：一律重發
        reused = None
    if reused is None:
        leaf_pem, key_pem, ca_der = issue(ip, days, now)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            _write(directory / "leaf.key", key_pem, private=True)
            _write(directory / "leaf.pem", leaf_pem)
            _write(directory / "ca.cer", ca_der)
            from cryptography import x509
            not_after = _not_after(x509.load_pem_x509_certificate(leaf_pem))
            _write(directory / "meta.json", json.dumps(
                {"ip": ip, "port": port, "not_after": not_after.isoformat(),
                 "fingerprint": fingerprint(ca_der)}, ensure_ascii=False).encode("utf-8"))
        except OSError as exc:
            raise LanRefused(f"無法寫入伺服器憑證目錄 {directory}（{exc.strerror or exc}）") from None
        return Material(directory, directory / "leaf.pem", directory / "leaf.key", directory / "ca.cer",
                        ca_der, fingerprint(ca_der), not_after, False)
    ca_der, not_after = reused
    return Material(directory, directory / "leaf.pem", directory / "leaf.key", directory / "ca.cer",
                    ca_der, fingerprint(ca_der), not_after, True)


def server_context(material):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(str(material.leaf_path), str(material.key_path))
    return context


def discard_pairing(directory):
    try:
        (pathlib.Path(directory) / "pairing.txt").unlink()
    except OSError:
        pass


def forget(environ=None, *, repo_root=REPO):
    """刪除 %LOCALAPPDATA%\\geometry-lan\\（葉私鑰、根憑證、配對碼檔）；回傳刪掉的路徑或 None。"""
    base = base_directory(environ, repo_root=repo_root)
    if base.name != "geometry-lan" or not base.exists():
        return None
    shutil.rmtree(base)
    return base


if __name__ == "__main__":
    if sys.argv[1:] != ["--forget"]:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        sys.exit(64)
    try:
        removed = forget()
    except LanRefused as exc:
        print(f"未刪除：{exc}", file=sys.stderr)
        sys.exit(2)
    print(f"已刪除 {removed}" if removed else "沒有保存的區網伺服器憑證", file=sys.stderr)
