"""由 UI 匯出的 R03 第二片場景，以固定規則刪行產生最小場景（不新增、不改寫任何一行）。

用法：python3 -I make_minimal.py <UI 匯出的 .scene> <輸出 .scene>

保留：requires／parameters／engineering／boundary／placement／finish-surface／panel-fill／derived-placement／grid／canvas-pos，
以及角材 1（邊界材，`place 1 on 2 at-face … between …`，只靠派生宿主的邊鍵定位）。
刪除：角材 2–53 及其 place、R18 註解行、記號用的 spec 與 guide（只有記號副支引用它們）。
刪完後由 diag_derived_host.py 載入原生 bridge 驗證可載入，並對兩份場景各跑一次。
"""
import sys

KEEP_TIMBER = '1'


def keep(line: str) -> bool:
    if not line or line.startswith('#'):
        return False
    head = line.split(' ', 2)
    kind = head[0]
    if kind in ('spec', 'guide'):
        return False
    if kind in ('timber', 'place'):
        return head[1] == KEEP_TIMBER
    return True


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, 'rb') as f:
        data = f.read().decode('utf-8')
    lines = data.split('\n')
    kept = [line for line in lines if keep(line)]
    with open(dst, 'wb') as f:
        f.write(('\n'.join(kept) + '\n').encode('utf-8'))
    print(f'{src}: {len([l for l in lines if l])} lines -> {dst}: {len(kept)} lines')
    return 0


if __name__ == '__main__':
    sys.exit(main())
