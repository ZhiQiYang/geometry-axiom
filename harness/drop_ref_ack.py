#!/usr/bin/python3
"""重演用的 receive-pack 包裝：真的執行 git-receive-pack（ref 會真的被更新），
但把它回給 client 的「ok refs/heads/<branch>」那一行拿掉，保留 unpack 結果與 flush。
client 因此看到 [remote failure] (remote failed to report status)。"""
import re, subprocess, sys
p = subprocess.Popen(["/usr/bin/git-receive-pack", *sys.argv[1:]], stdout=subprocess.PIPE)
while True:  # 原樣轉送 ref advertisement，直到第一個 flush
    header = p.stdout.read(4)
    if not header:
        break
    size = int(header, 16)
    body = p.stdout.read(size - 4) if size > 4 else b""
    sys.stdout.buffer.write(header + body); sys.stdout.buffer.flush()
    if size == 0:
        break
tail = p.stdout.read()
rc = p.wait()
wire, i, dropped = bytearray(), 0, 0
while i < len(tail):
    n = int(tail[i:i + 4], 16)
    if n == 0:
        wire.extend(b"0000"); i += 4; continue
    block = tail[i + 4:i + n]
    # side-band 時，report-status 是包在通道 1 裡的內層 pkt-line（「<4 碼長度>ok refs/heads/…\n」）；
    # 沒有 side-band 時，外層 pkt 本身就是「ok refs/heads/…\n」。兩種都只移除這一筆成功回覆。
    new = re.sub(rb"[0-9a-f]{4}ok refs/heads/[^\n]*\n", b"", block)
    if new.startswith(b"ok refs/heads/"):
        new = b""
    if new != block:
        dropped += 1
    wire.extend(f"{len(new) + 4:04x}".encode() + new); i += n
open("/tmp/drop-ref-ack.log", "w").write(f"receive-pack exit={rc} dropped_pkts={dropped}\n")
sys.stdout.buffer.write(bytes(wire)); sys.stdout.buffer.flush()
sys.exit(rc)
