"""T6 只讀診斷：不經 UI，重現 R03 確認後「派生宿主」上各畫面取不到的錯誤值，並指出取值的程式位置。

用法：
  python3 -I diag_derived_host.py --bridge <bridge 執行檔> --repo <repo 根目錄> <scene> [<scene> ...]
          [--ui-result walk_repro.result.json --ui-scene <該次匯出的 scene>]

做法（只讀）：
  - 每個場景各起一支新的 bridge 子行程（私有記憶體世界），`loadfile` 載入，接著只送唯讀查詢
    `dump`、`objects`、`surfaces`、`references`、`panel-fill-read`，最後再 `dump`；前後 dump 必須逐字相同。
    不寫任何檔案，不送 `line …`、`undo`、`redo` 或任何變更命令。
  - 前端取值用與 app.js／parameters.js 相同的運算式在 Python 重算（每項列出來源行，行號由下方程式片段在
    目前 repo 原始碼裡搜尋得出；找不到就標 MISSING，不猜）。
  - 有 --ui-result 時，把重算值與真 Chromium 走查（walk_repro.js）讀到的畫面值逐項比對。
結束碼：0＝所有場景載入成功、只讀、片段都找到且（若有）與 UI 值一致；1＝否則。
"""
import argparse
import json
import os
import subprocess
import sys

# 片段：(代號, 相對路徑, 原文片段)。行號在執行時搜尋。
SNIPPETS = [
    ('core.rect', 'current_geometry.c', ' *   rect：boundary_id == 0 時的矩形有效範圍。'),
    ('core.struct', 'current_geometry.c', '    uint32_t derived_fill_id;'),
    ('dp.write', 'geometry-core/derived_placements.inc', 'PlacementSurface p={0};p.id=value->id;p.derived_fill_id=value->derived_fill_id;'),
    ('bridge.objects.placement', 'geometry-web/web_bridge.c', '    /* 自帶矩形（無邊界面）的承載面也是一張面卡。 */'),
    ('bridge.objects.rect', 'geometry-web/web_bridge.c', '               (long long)p->rect.min_u, (long long)p->rect.min_v,'),
    ('bridge.surfaces', 'geometry-web/web_bridge.c', '               (unsigned)p->id, (unsigned)p->boundary_id,'),
    ('bridge.parameterUses', 'geometry-web/web_bridge.c', 'fputs("],\\"parameterUses\\":",stdout);json_parameter_uses(&g_world);'),
    ('bridge.json_parameter_uses', 'geometry-web/parameter_bridge.inc', 'static void json_parameter_uses(const World *w)'),
    ('core.parameter_uses.panel_fill', 'geometry-core/parameters.inc', 'parameter_native_use(u,"panel-fill %u %s",fill->id,names[k]);'),
    ('app.renderObjects.parameterUses', 'geometry-web/app.js', '  oc.parameterUses = r.parameterUses || [];'),
    ('app.faceCard', 'geometry-web/app.js', 'function faceCard(f) {'),
    ('app.faceCard.sub', 'geometry-web/app.js', '  sub.textContent = f.kind === "placement" ? "自帶矩形 · 無邊界"'),
    ('app.faceCard.bw', 'geometry-web/app.js', '  const bw = Math.max(1, f.bbox[2] - f.bbox[0]), bh = Math.max(1, f.bbox[3] - f.bbox[1]);'),
    ('app.faceCard.footer', 'geometry-web/app.js', '  ft.textContent = `${bw}×${bh} mm · ${nv} 頂點`;'),
    ('app.inspector.bbox', 'geometry-web/app.js', '    (o.bbox ? `<div class="kv"><span>外框尺寸</span><b>${o.bbox[2] - o.bbox[0]} × ${o.bbox[3] - o.bbox[1]} mm</b></div>` : "") +'),
    ('app.inspector.enter', 'geometry-web/app.js', '  if (sel.kind === "placement") { be.disabled = true; be.title = "placement 面沒有邊界可編輯"; }'),
    ('app.feSurf', 'geometry-web/app.js', "    || oc.surfs.find(s=>s.boundary===bid) || null;"),
    ('app.feLoadGuides.timbers', 'geometry-web/app.js', '  const timbers = r.timbers.filter(t => t.geometry.surface === sid).map(t => ({'),
    ('app.feLoadGuides.grids', 'geometry-web/app.js', '  const grids = (r.grids || []).filter(g => g.surface === sid);'),
    ('app.threeView.desc', 'geometry-web/app.js', "      desc:target ? `${({boundary:'面',placement:'自帶矩形面',guide:'參考線',timber:'角材',column:'柱',beam:'樑'})[target.root.kind]} ${target.root.id}` : '',hover:r.hoverOps};"),
    ('params.usage', 'geometry-web/parameters.js', '  function usage(id) {'),
    ('params.usage.uses', 'geometry-web/parameters.js', '    for(const use of oc.parameterUses||[])if(use.parameterId===id)uses.push(use);'),
    ('params.card', 'geometry-web/parameters.js', "個欄位 · ${usage(o.id).length} 處使用`;"),
    ('app.objectRow.parameter', 'geometry-web/app.js', '處使用`});}'),
]
# 物件畫布三個繪製函式（整段搜尋是否引用 timber）
CANVAS_FUNCS = ['function faceCard(f) {', 'async function renderObjects(', 'function drawObjects(']


def read_text(repo, rel):
    with open(os.path.join(repo, rel), 'rb') as f:
        return f.read().replace(b'\r\n', b'\n').decode('utf-8')


def locate(repo):
    out, cache = {}, {}
    for key, rel, needle in SNIPPETS:
        text = cache.setdefault(rel, read_text(repo, rel))
        hits = [i + 1 for i, line in enumerate(text.split('\n')) if needle in line]
        out[key] = f'{rel}:{hits[0]}' if len(hits) == 1 else (f'MISSING {rel}' if not hits else f'AMBIGUOUS {rel}:{hits}')
    app = cache.setdefault('geometry-web/app.js', read_text(repo, 'geometry-web/app.js'))
    canvas = {}
    for head in CANVAS_FUNCS:
        i = app.find(head)
        if i < 0:
            canvas[head] = 'MISSING'
            continue
        j = app.find('\n}\n', i)
        body = app[i:j]
        canvas[head] = {'lines': f'geometry-web/app.js:{app[:i].count(chr(10)) + 1}-{app[:j].count(chr(10)) + 1}',
                        'mentionsTimber': 'timber' in body}
    return out, canvas


class Bridge:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, encoding='utf-8')

    def send(self, cmd):
        self.p.stdin.write(cmd + '\n')
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError('bridge closed on ' + cmd.split(' ')[0])
        return json.loads(line)

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=10)


def bbox_of(points):
    us = [p[0] for p in points]
    vs = [p[1] for p in points]
    return [min(us), min(vs), max(us), max(vs)]


def diagnose(exe, scene):
    b = Bridge(exe)
    try:
        loaded = b.send('loadfile ' + os.path.abspath(scene))
        if not loaded.get('ok'):
            return {'scene': scene, 'loaded': loaded}
        d0 = b.send('dump')['text']
        objects = b.send('objects')
        surfaces = b.send('surfaces')
        refs = b.send('references')
        pf = b.send('panel-fill-read')
        d1 = b.send('dump')['text']
    finally:
        b.close()
    state = pf.get('state') or {}
    hosts = {h['id']: h for h in state.get('derivedPlacements') or []}
    fills = state.get('panelFills') or []
    rep = {'scene': scene, 'loaded': True, 'readOnly': d0 == d1, 'dumpLines': len([l for l in d0.split('\n') if l])}

    # 原生事實（取值來源）
    rep['native'] = {
        'objects.faces': [{k: f.get(k) for k in ('kind', 'id', 'bbox')} for f in objects['faces']],
        'surfaces': [{'id': s['id'], 'boundary': s['boundary']} for s in surfaces['surfaces']],
        'references.timbersBySurface': _count(t['geometry']['surface'] for t in refs.get('timbers') or []),
        'references.gridsBySurface': _count(g['surface'] for g in refs.get('grids') or []),
        'objects.timbersBySurface': _count(t['surface'] for t in objects.get('timbers') or []),
        'objects.parameterUses': objects.get('parameterUses'),
        'panel-fill-read.derivedPlacements': [{'id': h['id'], 'definition': h['definition'],
                                               'componentBboxes': [bbox_of(c['outline']) for c in h['derived']['components']]}
                                              for h in hosts.values()],
        'panel-fill-read.panelFillRefs': [{'id': f['definition']['id'],
                                           **{k: f['definition'][k] for k in ('gap', 'stagger', 'threshold') if isinstance(f['definition'].get(k), dict)}}
                                          for f in fills],
    }

    # 前端同式重算
    faces = objects['faces']
    sym = {}
    for f in faces:
        if f['kind'] != 'placement':
            continue
        bw0, bh0 = f['bbox'][2] - f['bbox'][0], f['bbox'][3] - f['bbox'][1]
        truth = hosts.get(f['id'])
        sym[f'S1 宿主卡尺寸（placement {f["id"]}）'] = {
            'ui': f'{max(1, bw0)}×{max(1, bh0)} mm', 'subtitle': '自帶矩形 · 無邊界',
            'objects.bbox': f['bbox'],
            'derivedHost': truth is not None,
            'truthComponentBbox': [bbox_of(c['outline']) for c in truth['derived']['components']] if truth else None}
        sym[f'S2 檢查器外框尺寸（placement {f["id"]}）'] = {'ui': f'{bw0} × {bh0} mm', 'objects.bbox': f['bbox']}
        sym[f'S6 進入面內工作區（placement {f["id"]}）'] = {'ui': 'disabled（kind === "placement" 一律停用）'}
    for f in faces:
        if f['kind'] != 'boundary':
            continue
        bid = f['id']
        sid = next((s['id'] for s in surfaces['surfaces'] if s['boundary'] == bid), None)
        tcount = sum(1 for t in refs.get('timbers') or [] if t['geometry']['surface'] == sid)
        gcount = sum(1 for g in refs.get('grids') or [] if g['surface'] == sid)
        sym[f'S3 面 {bid} 面內角材／網格'] = {
            'feSid': sid, 'uiTimbers': tcount, 'uiGrids': gcount,
            'timbersElsewhere': {k: v for k, v in rep['native']['references.timbersBySurface'].items() if k != sid},
            'gridsElsewhere': {k: v for k, v in rep['native']['references.gridsBySurface'].items() if k != sid}}
    for c in objects.get('parameters') or []:
        pid = c['id']
        uses_ui = [u for u in objects.get('parameterUses') or [] if u.get('parameterId') == pid]
        grid_sys = [g for g in objects.get('gridSystems') or [] for a in ('u', 'v')
                    for r in ((g.get(a + 'Definition') or {}).get('parameterRefs') or {}).values() if r.get('parameterId') == pid]
        card_refs = sum(1 for c2 in objects.get('parameters') or [] for fl in c2['card']['fields'] if _refs_param(fl.get('expression'), pid))
        truth = [(f['definition']['id'], k) for f in fills for k in ('gap', 'stagger', 'threshold')
                 if isinstance(f['definition'].get(k), dict) and f['definition'][k].get('parameterId') == pid]
        truth += [('host', h['id']) for h in hosts.values() if isinstance(h['definition'].get('h'), dict) and h['definition']['h'].get('parameterId') == pid]
        sym[f'S5 參數卡 {pid}「N 處使用」'] = {'ui': len(uses_ui) + len(grid_sys) + card_refs,
                                          'panelFillOrHostRefs': truth}
    sym['S4 物件畫布角材'] = {'ui': 0, 'note': '物件畫布只畫卡片；見 canvasFunctions（三個繪製函式都沒有引用 timber）',
                         'objects.timbersBySurface': rep['native']['objects.timbersBySurface']}
    sym['S7 三視圖選取說明'] = {'ui': '角材 <id>（app.threeView.desc 只用 owner 種類與 id）'}
    rep['symptoms'] = sym
    return rep


def _count(it):
    out = {}
    for k in it:
        out[k] = out.get(k, 0) + 1
    return out


def _refs_param(ast, pid):
    if not isinstance(ast, dict):
        return False
    if ast.get('op') == 'ref' and ast.get('parameterId') == pid:
        return True
    return _refs_param(ast.get('left'), pid) or _refs_param(ast.get('right'), pid)


def compare_ui(rep, ui):
    """與真 Chromium 讀到的畫面值逐項比對（只比本腳本重算得出的項目）。"""
    v, s = ui['view'], ui['sources']
    sym = rep['symptoms']
    host_card = next((c['text'] for c in v['cards'] if c['kind'] == 'placement'), '')
    param_row = next((r['text'] for r in v['rows'] if r['kind'] == 'parameter'), '')
    s1 = next(x for k, x in sym.items() if k.startswith('S1'))
    s2 = next(x for k, x in sym.items() if k.startswith('S2'))
    s3 = next(x for k, x in sym.items() if k.startswith('S3 面 1 '))
    s5 = next(x for k, x in sym.items() if k.startswith('S5'))
    return {
        'S1 卡片文字含重算值': [s1['ui'] in host_card, s1['ui'], host_card],
        'S1 卡片副標': [s1['subtitle'] in host_card, s1['subtitle']],
        'S2 檢查器文字含重算值': [('外框尺寸\n' + s2['ui']) in (v.get('hostInspector') or ''), s2['ui']],
        'S3 面 1 feSid 與 UI 相同': [s3['feSid'] == v.get('face1Sid'), s3['feSid'], v.get('face1Sid')],
        'S3 面 1 角材數與 UI 相同': [s3['uiTimbers'] == v.get('face1FeTimbers') and '尚無角材' in (v.get('face1Layers') or ''), s3['uiTimbers'], v.get('face1FeTimbers')],
        'S4 物件畫布角材元素': [v.get('objectCanvasTimberElements') == 0, v.get('objectCanvasTimberElements')],
        'S5 參數列文字': [f'{s5["ui"]} 處使用' in param_row and s5['ui'] == len(s['frontend']['parameterUsage1'] or []), s5['ui'], param_row],
        'S6 進入鈕停用': [bool(v.get('hostEnter', {}).get('disabled')), v.get('hostEnter')],
        'S7 三視圖說明': [v.get('threeViewPickInfo') == '角材 3', v.get('threeViewPickInfo')],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bridge', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--ui-result')
    ap.add_argument('--ui-scene', help='與 --ui-result 同一次走查匯出的場景（只比對這一份）')
    ap.add_argument('scenes', nargs='+')
    a = ap.parse_args()
    where, canvas = locate(a.repo)
    out = {'sourceLocations': where, 'canvasFunctions': canvas, 'scenes': []}
    ok = all(not v.startswith(('MISSING', 'AMBIGUOUS')) for v in where.values()) and \
        all(isinstance(c, dict) and not c['mentionsTimber'] for c in canvas.values())
    for scene in a.scenes:
        rep = diagnose(a.bridge, scene)
        ok = ok and rep.get('loaded') is True and rep.get('readOnly') is True
        out['scenes'].append(rep)
    if a.ui_result:
        with open(a.ui_result, encoding='utf-8') as f:
            ui = json.load(f)
        out['uiComparison'] = {}
        ok = ok and any(rep['scene'] == a.ui_scene for rep in out['scenes'])
        for rep in out['scenes']:
            if rep['scene'] == a.ui_scene:
                cmp_ = compare_ui(rep, ui)
                out['uiComparison'][rep['scene']] = cmp_
                ok = ok and all(v[0] for v in cmp_.values())
    out['ok'] = ok
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
