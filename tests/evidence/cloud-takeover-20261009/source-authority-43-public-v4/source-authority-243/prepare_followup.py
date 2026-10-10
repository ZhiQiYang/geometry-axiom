#!/usr/bin/env python3
"""Prepare a portable 43-ID source follow-up. Scratch writes only."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,urllib.parse
ROOT=Path('<workspace-path>');OUT=Path(__file__).parent;PARENT=OUT.parent
BASE='243326b512896ace70e068f62c8f3d6397f6000d'
FIVE='0b37d8d8d4ee501fe6208e3e88440b3d078d7c0b'
HIST='640a81443b3d070dba3d8a0aa52adb2d64cebe0b'
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def save(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
head=git('rev-parse','HEAD').decode().strip();dirty=git('status','--short').decode()
historyPath=PARENT/'issue123-43-current640-source-audit.md';history=historyPath.read_bytes()
issuePath=PARENT/'issue123-original.json';issueBytes=issuePath.read_bytes();issue=json.loads(issueBytes)
records=[];texts={}
paths=['AGENTS.md','公理層.md','geometry-guide/PRODUCT-VISION.md','geometry-web/docs/issue123-handoff/README.md','geometry-web/docs/issue123-handoff/C-review.md','geometry-web/docs/issue123-handoff/A-43-map.md','geometry-web/docs/DOM-CONTRACT.md','geometry-web/app.js','geometry-web/app.css','geometry-web/index.html','geometry-web/project-ui.css','geometry-web/workspace-shell.js','geometry-web/workspace-shell.css','geometry-web/workspace-guidance.js','geometry-web/workspace-guidance.css','geometry-web/grid-system-workspace.js','geometry-web/grid-system-workspace.css','geometry-web/grid-inspector.js','geometry-web/grid-inspector.css','geometry-web/grid-anchor-positions.js','geometry-web/space-workspace.js','geometry-web/space-workspace.css','geometry-web/room-outline-workspace.js','geometry-web/room-outline.js','geometry-web/reference-workspace.js','geometry-web/cdp_test.js','geometry-web/grid_rule_editor_test.js','geometry-web/space_model_test.js','tests/INTEGRATION-GATES.md']
for path in paths:
 data=git('show',BASE+':'+path);texts[path]=data.decode();saved=OUT/'source'/path;save(saved,data)
 records.append({'path':path,'fullSourceSHA':BASE,'sha256':sha(data),'bytes':len(data),'retainedPath':str(saved)})
save(OUT/'authority/issue123-original.json',issueBytes);save(OUT/'authority/issue123-43-current640-source-audit.md',history)
repoURL=issue['html_url'].rsplit('/issues/',1)[0]
def source(path,needle,last=False):
 text=texts[path];at=text.rfind(needle) if last else text.find(needle)
 if at<0:return {'path':path,'needle':needle,'status':'unknown: exact anchor not found','fullSourceSHA':BASE}
 line=text[:at].count('\n')+1
 return {'path':path,'line':line,'needle':needle,'url':repoURL+'/blob/'+BASE+'/'+urllib.parse.quote(path)+'#L'+str(line),'fullSourceSHA':BASE}
def refs(*pairs):return [source(*pair) for pair in pairs]
A='geometry-web/app.js';C='geometry-web/app.css';I='geometry-web/index.html';GW='geometry-web/grid-system-workspace.js';GC='geometry-web/grid-system-workspace.css';GI='geometry-web/grid-inspector.js';GIC='geometry-web/grid-inspector.css';SM='geometry-web/space-workspace.js';SC='geometry-web/space-workspace.css';DOM='geometry-web/docs/DOM-CONTRACT.md'
data=[
 ('X1','S1','SOURCE_WIRED_WITH_UNKNOWN','共用主要 accent／ink／muted／border 切片維持；四處 computed background 是待同版實測條件，不能以宣告字串取代。私人全部色票／label 像素未知。',refs((C,'--accent:'),(SC,'--sm-primary'))),
 ('X2','S1','SOURCE_PENDING','56／96px 共用標頭、原 projectBar、右 history 接線維持；243 的 bounded navscroll 已接。另有標題垂直越界待修：不能以 titleWidth 通過或 nav 框正常取代 title top/bottom。',refs((C,'.workspace-tools-row .face-workspace-tools'),(C,'.workspace-title-copy small'),(DOM,'頂列'))),
 ('X3','S1','SOURCE_WIRED_WITH_UNKNOWN','既有控制與手機 44px 規則維持，243 nav 不縮字級／hit target。32／36／44 與私人40、input32／36歧義仍須原稿核對，不新增一律尺寸。',refs((C,'min-height:44px'),(GC,'min-height: 44px'))),
 ('X4','S1/S3','SOURCE_WIRED','共用分段控制及一次一構件表單維持；原 guide／timber／grid 路由、raw 與焦點契約不變。',refs((A,'faceComponentSwitch'),(DOM,'[data-component-tab]'))),
 ('X5','S1','SOURCE_WIRED_FIVE','0b37 已把網格返回／縮小／放大接到既有 arrowLeft／minus／plus SVG；ID、aria-label、handlers 維持，不宣稱全面私人圖示像素相符。',refs((GW,"icon('arrowLeft')"),(GW,"icon('minus')"),(GW,"icon('plus')"),(GC,'.ig-zoombar button svg'))),
 ('X6','S1/S2/S4','SOURCE_WIRED','縮放仍在實際 viewport，390 網格 preview先於 settings；243 nav變成有界scroll但正常 last/first tool pointer／Tab 尚待本版。網格實際格距／像素讀值保留。',refs((GC,'.ig-main { order: 0'),(GW,"$('igZoom')"),(C,'.workspace-tools-row .face-workspace-tools'))),
 ('X7','S1/S4','SOURCE_WIRED','柱／樑／網格色彩來源維持共用型別 token；樑實名是--beam／--beam-soft，顏色呈現不改 typed/native 幾何。',refs((C,'--beam:'),(C,'.type-icon.beam, .object-row .row-icon.beam'))),
 ('B1','S1/S3','SOURCE_PENDING','桌面56px、<=560px96px與viewport原要求維持；243 bounded navscroll 已接，尚有原標題 small換行垂直越界缺口。需保持56／44與11／13字級，另驗真正 top/bottom／正常scroll。',refs((C,'--topbar-h: 56px'),(C,'.workspace-tools-row .face-workspace-tools'),(DOM,'viewport−88px'))),
 ('B2','S3','SOURCE_WIRED','左欄維持純圖層／定位／顯示；唯一 BOM在右構件→角材，投影表單在右Shape。移位不複製提交、料單或 native來源。',refs((A,'faceTimberSchedule'),(A,'faceProjectionEditor'),(DOM,'原生角材料單'))),
 ('B3','S3','EXISTING_CONTRACT_NOT_NEW_POLICY','五個persistent layer groups及真可建立的empty入口保留。原完整CDP明確依賴五組／>=3 .fl-empty及實際empty點擊；portable S3沒有採納hide-all-empty，不刪它們冒充去重。',refs(('geometry-web/cdp_test.js','five persistent groups'),('geometry-web/cdp_test.js',"#faceLayerList .fl-empty"),(A,'className = "fl-empty"'))),
 ('B4','S3/S6','SOURCE_WIRED','guide／timber／grid一次一表單及BOM在timber維持。243的direct-room raw由exact-draft pendingRows擁有、從泛ref備份排除；其他表單raw/焦點保全不變，#54旁帶修復不當成多房新規格。',refs((A,'faceComponentSwitch'),(A,'!e.matches("[data-room-edge-length]")'),('geometry-web/room-outline-workspace.js','const pendingRows=new WeakMap()'))),
 ('B5','S1/S3','SOURCE_WIRED_WITH_UNKNOWN','既有desktop/mobile控制來源維持；沒有因nav／標題修復縮小44px hit target。私人未指定控制尺寸未知。',refs((C,'.object-workspace :is(.btn'),(C,'min-height:44px'))),
 ('B6','S3','EXISTING_CONTRACT_WITH_UNVERIFIED_TIMING','GEO216 first-visit／dynamic summary與已讀狀態区分維持；C-review的首次fit後出現卡片／真.fe-dim.fe-edge-dim／重進場景時序仍須實測，不把main/face不同選取狀態抹平。',refs(('geometry-web/workspace-guidance.js','dynamic'),(A,'feViewportInsets'),(DOM,'選取'))),
 ('B7','S3','SOURCE_WIRED_FIVE','0b37 移除只做同一feSetTool(hole)的重複shape-menu hole入口；standalone [data-face-tool=hole]、R、其餘不同shape操作及native孔洞契約維持。',refs((I,'data-shape-action="notch"'),(I,'data-face-tool="hole"'),(A,'feSetTool("hole")'))),
 ('B8','S3','UNKNOWN_PRIVATE_TARGET','目前decorative origin stroke不新增永久caption。A-map自寫摘要不是已採納的精確對比值；保留來源現況，私人視覺要求／額外policy未知。',refs((DOM,'#123 已採納介面切片'))),
 ('C1','S4','SOURCE_WIRED','實名是#spacePlanMetrics、.space-plan-strip、data-plan-grid-step／[data-plan-grid]與12px螢幕label；spacePlanReadout是原issue提議名。尺寸／座標／格線僅呈現，不新增吸附或改World。',refs((A,"planMetrics.id='spacePlanMetrics'"),(I,'class="space-plan-strip"'),(DOM,'空間平面圖'))),
 ('C2','S1/S4','SOURCE_WIRED','既有樑卡及plan renderer共用--beam／--beam-soft，243沒有重造另一樑顏色系統。',refs((C,'--beam:'),(C,'.space-plan-beam'),(DOM,'空間平面圖'))),
 ('C3','S4','SOURCE_WIRED','原#spaceWorkspaceTools及#spaceSizeTools位於同一.space-plan-strip平面工具列，proj不顯示放置控制；不是另造spacePlanToolbar ID。',refs((A,"document.querySelector('.space-plan-strip').prepend"),(I,'id="spaceSizeTools"'),(DOM,'#spaceSizeTools'))),
 ('C4','S4','EXISTING_CONTRACT','既有常駐空槽入口及slot名稱／axis／action區分維持；不改slot allocation或native語意。',refs((A,'slot-empty'),(DOM,'槽'))),
 ('C5','S4','UNKNOWN_UNADOPTED_REMOVAL','spaceAddMembers／spEditMembers仍是兩個位置的同openMemberDialog，RC有hover／focus／coarse呈現。portable S4未指定刪除哪個member入口或滑鼠RCalways-visible policy；列決策，不自行移除。',refs((I,'id="spaceAddMembers"'),(A,'spEditMembers'),(A,'openMemberDialog'))),
 ('C6','S4','POLICY_UNKNOWN','free RC仍列既有未擁有成員來源。附近過濾需新增距離／範圍／優先規則，portable adopted scope未定，不擴張成新空間policy。',refs((A,'spaceRcFreeList'))),
 ('C7','S4','UNKNOWN_UNADOPTED_REMOVAL','title ID／closed tag及詳細ID/status行是既有source。portable S4未定精確刪哪列，A-map重複摘要不構成新採納規格；私人稿件對照未知。',refs((A,'function renderSpaceInspector'),(DOM,'空間'))),
 ('D1','S4','SOURCE_WIRED','#workSurf隱藏相容consumer維持；唯一可見#v3ToolbarSurf在rect-only #v3PlaneControls，由syncV3PlaneControls同步。不刪native select值／原change路徑。',refs((I,'id="workSurf"'),(I,'id="v3ToolbarSurf"'),(A,'function syncV3PlaneControls'))),
 ('D2','S4','SOURCE_WIRED','桌面右欄固定240px及unselected空態維持；v3-picked只標selection，mobile沿原drawer。',refs((C,'--right-w: 240px'),(DOM,'body.v3-picked'))),
 ('D3','S4','SOURCE_WIRED_FIVE','0b37 可見三視圖view/hole及native option詞彙統一為選取／開口；data-v3-tool=view/hole、values、ID／handler維持。rect/redraw是不同原操作，不合併成同工具。',refs((I,'data-v3-tool="view"'),(I,'data-v3-tool="hole"'),(I,'id="btnHole2"'))),
 ('D4','S1/S4','SOURCE_WIRED','整列view／layer labels及手機44px入口維持真label/Space行為；不能由同名label推論新native行為。',refs((I,'v3-check-col'),(C,'.v3-check-col label'),(DOM,'視圖／圖層整列'))),
 ('E1','S2','SOURCE_WIRED','唯一原#igBoundarySection／#igBoundaryView已移右binding step2；640既有SVG screen-coordinate／vertex-focus修復保留，typed outer/hole/key與native dropdown不變。',refs((GW,"$('igVertexSummary').after($('igBoundarySection'))"),(GW,'function drawBoundary(s)'),(DOM,'#igBoundarySection'))),
 ('E2','S2/S6','SOURCE_WIRED_NEW_GUARD','discard左／primary右及同workspace inline question維持；243 close走stored one-shot discardCleanup，不再click被inert的Cancel。原current／pending guard、正常Cancel焦點與原World/attachment語意維持，same-ID retired callback待本版。',refs((GW,'function confirmDiscard(s,trigger)'),(GW,'let cleaned=false'),(GW,'state?.discardCleanup?.()'))),
 ('E3','S1/S2','SOURCE_WIRED','source-save共用accent，native scene套用與full-project保存提示區分維持，raw draft不冒充已確認World。',refs((GW,'syncDraftState(s)'),(GC,'.primary-button'),(DOM,'網格'))),
 ('E4','S1/S2','SOURCE_WIRED_FIVE','返回左位及共用header source维持；0b37 返回改既有arrowLeft圖示而保留#igClose／aria／handler。',refs((GW,"icon('arrowLeft')"),(DOM,'標頭'))),
 ('E5','S2','SOURCE_WIRED_FIVE','共用GridAnchorPositions九名与0／1、1／2、1／1精確分數、custom1/3保留；0b37 compact vertex/preset重繪restore同typed focused node preventScroll，原current/busy守門不變。',refs(('geometry-web/grid-anchor-positions.js','window.GridAnchorPositions'),(GI,'focusedVertex'),(GI,'focusedAnchor'))),
 ('E6','S1/S2','SOURCE_WIRED_FIVE','0b37 minus／plus共用SVG圖示已接，縮放位置與格距／像素readout保留。沒有percentage替換或privatepixel重設規格。',refs((GW,"icon('minus')"),(GW,"$('igZoom')"),(GC,'.ig-zoombar button svg'))),
 ('G1','S1/S2','UNKNOWN_PRIVATE_CONTRAST','compact既有readable stylesheet、focus及語境文字source維持。私人全部label對比／像素未核，不能以四primary契約宣称每個label相同。',refs((GIC,'.gi-heading'),('geometry-web/docs/issue123-handoff/C-review.md','G3 文字對比'))),
 ('G2','S1/S2','UNKNOWN_PRIVATE_HEIGHT','compact/full可有既有不同密度；保留focus／mobile目標／native编辑。原issue尺寸歧義未定，不把所有compact40自行判錯或統一44。',refs((GIC,'.gi-actions .btn'),(GIC,'@media(max-width:680px)'))),
 ('G3','S2','SOURCE_WIRED_FIVE','0b37 將原#gridObjectDelete唯一node放進closed footer .gi-delete-section，與open/new-binding隔離；原onclick/current/busy及deleteObject→native impact不變，不加第二confirm。normal caller已加一次summary導覽，行為斷言保留。',refs((GI,'gi-delete-section'),(GI,"gridObjectDelete').onclick"),(GIC,'.gi-delete-section'),('geometry-web/grid_rule_editor_test.js','.gi-delete-section'))),
 ('G4','S2','SOURCE_WIRED','source/binding不同native概念及同九點詞彙維持；0b37焦點保全不把compact未保存選擇當成已保存配置。',refs((GI,'gi-eyebrow'),(GI,'GridAnchorPositions'),(DOM,'GridAnchorPositions'))),
 ('F1','S5','SOURCE_WIRED_NEW_GUARD','welcome置stage且controls按真result顯隱維持；243 valid source render後收起#smOtherExamples picker，保留原範例／確認入口，不靠縮小44px控制騰位。',refs((SM,'function renderSource(source'),(SM,'$("smOtherExamples").open=false'),(SM,'.sm-view-tools'))),
 ('F2','S1/S5','SOURCE_WIRED_WITH_OPEN_VERIFICATION','共用header／3step form／stage／short-height900來源維持；243 chooser收起已接，390 projection Confirm完整inside-scroll及共享header垂直界線仍待真新版驗收。舊fullSpace titleWidth pass只證明寬度。',refs((SC,'max-height:900px'),(SM,'$("smOtherExamples").open=false'),(SM,'function organizeSetup()'))),
 ('F3','S5','SOURCE_WIRED_NEW_GUARD','welcome一個primary／其他原範例在disclosure維持；243 renderSource valid選妥後關disclosure，不刪例子，不宣稱永遠可見或自動重建preview。',refs((SM,'smOtherExamples'),(SM,'$("smOtherExamples").open=false'))),
 ('F4','S5','SOURCE_WIRED','唯一三step編號，原各節duplicate numbers移除；既有source／geometry／preview/build順序與#119診斷維持。',refs((SM,'function organizeSetup()'),(SM,'sm-section-heading'))),
 ('F5','S1/S5','SOURCE_WIRED_WITH_UNKNOWN','主要accent／focus／控制source維持；C-review的已量smCanvas和未量face toolbar焦點不能互借。私人像素對照未知。',refs((SC,'--sm-primary'),('geometry-web/docs/issue123-handoff/C-review.md','F5 的 2px'))),
 ('F6','S5','SOURCE_WIRED_WITH_OPEN_VERIFICATION','既有guide/help/direction最終12px override來源保留，早期11px只作歷史；GEO210的confirmBottom<=setup-scroll.bottom與完整44px須核本版實測範圍，不以舊文字尺寸或titleWidth替代。',refs((SC,'.sm-guide,.sm-guide p,.sm-help,.sm-view-direction{font-size:12px}'),('geometry-web/docs/issue123-handoff/C-review.md','confirmBottom<=bottom'))),
 ('F7','S1/S5','SOURCE_WIRED','原#smClose左置與返回／focus路由維持；正常Tab首停焦點需本版核收，沒有新增另一個返回入口。',refs((SM,'smClose'),(DOM,'#smClose')))
]
historical=[]
for line in history.decode().splitlines():
 if line.startswith('| ') and line.split('|')[1].strip() in {d[0] for d in data}:
  pieces=[p.strip() for p in line.split('|')[1:-1]];historical.append({'id':pieces[0],'source':pieces[1],'status':pieces[2],'rawLine':line})
ids=[d[0] for d in data];assert len(ids)==len(set(ids))==43 and [x['id'] for x in historical]==ids
itemHistory={r['id']:r for r in historical}
proofPath=Path('<workspace-path>')
proofBytes=proofPath.read_bytes();proof=json.loads(proofBytes)
assert sha(proofBytes)=='72314c2a9ff61d77cd6e7f1073e5cd1f5da94b7c1b0613ebeb4b67dfbbfb4074'
assert proof['sourceSHA']==BASE and proof['dirty']=='' and proof['ok'] is True
assert proof['recordedAcceptance']=={'passed':185,'failed':2,'exitCode':1,'acceptanceCompleted':False,'allDeclaredGroupsAttempted':True,'scope':['plan','bom','row-blur','s2']}
probePath=Path('<isolated-test-directory>')
probeBytes=probePath.read_bytes();probe=json.loads(probeBytes)
assert sha(probeBytes)=='1d2126a9cc62bc50015de3aa409f23a1cbb60d903b8edc756cc33593d33061b1'
assert len(probe['results'])==187 and sum(x['ok'] is True for x in probe['results'])==185
evidenceSources=[{'path':str(proofPath),'sha256':sha(proofBytes),'retainedPath':str(OUT/'evidence/supplementary-validation-243-supplement-v4.json')},{'path':str(probePath),'sha256':sha(probeBytes),'retainedPath':str(OUT/'evidence/supplement-four-v4-original-probe.json')}]
save(OUT/'evidence/supplementary-validation-243-supplement-v4.json',proofBytes);save(OUT/'evidence/supplement-four-v4-original-probe.json',probeBytes)
limited={'sourceSHA':BASE,'dirty':'','originalPassed':185,'originalFailed':2,'exitCode':1,'acceptanceCompleted':False,'allDeclaredGroupsAttempted':True,'groupCensus':{'plan':{'passed':16,'failed':0,'desktopAnd390Completed':True},'bom':{'passed':44,'failed':0,'desktopAnd390Completed':True},'row-blur':{'passed':32,'failed':1,'desktopStoppedAtCheck':33,'mobile390NotReached':True},'s2':{'passed':86,'failed':1,'desktopPassed':84,'desktopCompleted':True,'mobile390PassedSetupChecks':2,'mobile390Failure':'hidden #toggleRight normal click','mobile390DownstreamNotReached':True}},'rowLimit':'Failed zero-all-API assertion observed only source-inspect and engineering-read. Direct retirement/native-after/new-candidate/390 checks were not reached. Preserve original failure; no retrofit oracle.', 'evidence':evidenceSources,'newBrowserExecutionByThisSubtask':False,'all43Accepted':False,'fullCDPAccepted':False}
limited['additionalCheckCensus']={'preflight':{'passed':4,'failed':0},'final':{'passed':3,'failed':0}}
spaceRoot=Path('<original-evidence-root>/after-final-243326b5-full-space-20261009')
spaceReceiptBytes=(spaceRoot/'receipt.json').read_bytes();spaceReceipt=json.loads(spaceReceiptBytes)
spaceResultBytes=(spaceRoot/'space-artifacts/result.json').read_bytes();spaceResult=json.loads(spaceResultBytes)
spaceLogBytes=(spaceRoot/'command.log').read_bytes()
canonicalLines=[line[len('SPACE_RESULT '):] for line in spaceLogBytes.decode().splitlines() if line.startswith('SPACE_RESULT ')]
assert len(canonicalLines)==1;canonical=json.loads(canonicalLines[0])
assert all(spaceReceipt[when]['git']['head']==BASE and spaceReceipt[when]['git']['status']=='' for when in ['before','after'])
assert spaceReceipt['command']==['node','geometry-web/space_model_test.js'] and spaceReceipt['cwd']==str(ROOT)
assert spaceReceipt['execution']['exitCode']==spaceReceipt['gateExitCode']==0 and spaceReceipt['executionVerified'] is True
assert not spaceReceipt['execution']['timedOut'] and not spaceReceipt['execution']['interrupted']
assert spaceReceipt['log']['sha256']==sha(spaceLogBytes)
assert canonical==spaceReceipt['evidence']['canonicalResult'] and canonical['completed'] is True
assert spaceResult['completed'] is True and spaceResult['passed']==canonical['passed']==228 and spaceResult['failed']==canonical['failed']==0
assert len(spaceResult['results'])==228 and all(x['ok'] is True for x in spaceResult['results'])
assert canonical['scope']['mode']=='full-space-suite' and canonical['scope']['filters']==[]
assert canonical['scope']['omitted']==['timber-material','timber-source-guards']
assert canonical['groups']['font-layout']=={'expected':19,'passed':19,'failed':0,'completed':True}
assert all(x in texts['geometry-web/space_model_test.js'] for x in ['titleWidth:title.width','rows.titleWidth>0'])
spaceEvidence=[]
for filename,b in [('receipt.json',spaceReceiptBytes),('space-artifacts/result.json',spaceResultBytes),('command.log',spaceLogBytes)]:
 retained=OUT/'evidence/full-space-243'/filename;save(retained,b)
 spaceEvidence.append({'path':str(spaceRoot/filename),'sha256':sha(b),'bytes':len(b),'retainedPath':str(retained)})
evidenceSources.extend(spaceEvidence)
fullSpace={'sourceSHA':BASE,'dirtyBefore':'','dirtyAfter':'','originalReceiptReceivedByThisSubtask':True,'passed':228,'failed':0,'completed':True,'exitCode':0,'command':spaceReceipt['command'],'cwd':spaceReceipt['cwd'],'scope':canonical['scope'],'fontLayout':canonical['groups']['font-layout'],'canonicalLogCount':1,'evidence':spaceEvidence,'executionIdentityRetainedFromOriginalReceipt':spaceReceipt['executionIdentity'],'doesNotVerifyTitleVerticalBounds':True,'newBrowserExecutedByThisSubtask':False,'notAll43OrFullCDP':True}
itemLimited={'C1':'Plan supplement16/0完成桌面／390：僅原scope，不是C1私人全部對照或all43。','C3':'Plan supplement16/0完成桌面／390：僅原scope。','B2':'BOM supplement44/0完成桌面／390：僅原scope，不借成投影完整回歸。','B4':'row-blur32/1，desktop第33停止；direct retirement/native-after/new-candidate及390未到。','E1':'S2 desktop84/0完成；390只2個setup通過，hidden #toggleRight失敗，後段未到。','E2':'S2 desktop84/0含same-ID detach／原oldcallback／B continuation；390後段未到。','E5':'S2 desktop84/0；390後段未到，不借桌面成手機focus驗收。','G3':'S2 desktop84/0含原delete路徑；390後段未到。','G4':'S2 desktop84/0；390後段未到。'}
items=[{'id':id,'portablePhase':phase,'sourceStatus':status,'currentSourceNote':note,'sourceReferences':references,'historical640':itemHistory[id],'browserAcceptanceAt243':{'entireItemAccepted':False,'limitedReadReceipt':itemLimited.get(id,'No new item-wide acceptance; see separate bounded243 receipts.'),'sourceOnlyChangesNotAutomaticallyAccepted':True},'privateZIPCompared':False} for id,phase,status,note,references in data]
assert 'data-shape-action="hole"' not in texts[I] and 'data-face-tool="hole"' in texts[I]
assert all(s in texts[GW] for s in ["icon('arrowLeft')","icon('minus')","icon('plus')",'let cleaned=false','s.discardCleanup=cleanup','state?.discardCleanup?.()'])
assert all(s in texts[GI] for s in ['gi-delete-section','focusedVertex','focusedAnchor','focus({preventScroll:true})'])
assert 'const pendingRows=new WeakMap()' in texts['geometry-web/room-outline-workspace.js'] and '!e.matches("[data-room-edge-length]")' in texts[A]
assert '$("smOtherExamples").open=false' in texts[SM] and 'max-width: 100%' in texts[C]
authorityText=issue['body'];phases={}
for line in authorityText.splitlines():
 if line.startswith('- [ ] S'):phases[line[6:8]]=line
assert set(phases)=={'S0','S1','S2','S3','S4','S5','S6'}
titlePending={'status':'SOURCE_PENDING','reportedHistoricalSHA':FIVE,'measuresReportedByRoot':[{'width':900,'titleBottom':61.328,'headerHeight':56},{'width':680,'titleBottom':69.297,'headerHeight':56},{'width':600,'titleBottom':69.297,'headerHeight':56}],'rawDiagnosticOriginalReceivedByThisSubtask':False,'rawDiagnosticPath':'unknown to this subtask; parent reported original 0b37 diagnostic JSON','next':'Root intends shared small nowrap/overflow hidden/text-overflow ellipsis after frozen243 verification; preserve11/13px text,56px header,44px controls. Do not mark this implemented at243 or use historical titleWidth pass as vertical-bound proof.'}
doc='''# #123：43 ID 的 source 續註（243326）

本文件逐項接續原640 available-source audit，沒有覆寫歷史 A-43-map、README/C-review或原 audit。完整受讀版本是 `'''+BASE+'''`。這是 source 對照，不是新 HEAD 的 browser PASS、43項產品結案或私人 ZIP／像素比對。每列保留640原註記並另列本版 source；歷史「0-fixed／30-unknown」和其舊測試數字仍只屬各自原版本／範圍，不重計成新head通過。

權威與界線：可攜原 #123 的 S0–S6、已採納公理及既有 DOM/command/transaction 為判準。43 IDs與歷史自寫摘要來自 A-map／640 audit，不冒充私人附件原句。原issue明列 ZIP私人Library素材未核，尺寸／座標／ID相容等歧義不能自行補規格。C-review優於A/B相衝突技術解讀；舊README的writer等待是歷史，本輪交接已解除，不重新設成阻塞。

## 本輪已接 source 與仍待修

`'''+FIVE+'''` 的五項採納修正已在本版 source 中確認：compact delete隔離（G3）；三視圖選取／開口同詞（D3）；去掉完全同feSetTool(hole)的shape-menu重複入口，保留R／standalone／原生孔洞（B7）；網格返回／縮放用既有SVG icons（X5/E4/E6）；compact typed vertex／九點preset重繪保留鍵盤焦點（E5/G4）。它們是source已接，不借舊版測試當本版browser結果。

243326 的新增守門：direct-room `pendingRows` exact-draft WeakMap跨notice/redraw保留raw，泛ref備份排除 `[data-room-edge-length]`；驗證成功只退役所套用邊，完整頂點替換成功才退役全部，非法值／owner拒絕保留；Review/Confirm看semantic pending map。這是既有#54單房及S6中斷流程的UI一致性修復，不擴成#87，不增保存格式。`discardCleanup` one-shot退役舊inline prompt及captured inert狀態，lifecycle close直接cleanup，舊callback不能聚焦／清B。nav改有界scroll而保留56/96與44px控制。有效3D source選妥後收起原#smOtherExamples chooser，原organizeSetup本就已把guide移末，不把移guide的廢棄猜想寫成修復。

**SOURCE_PENDING：共享標題垂直界線。** Root回報原0b37 diagnostic JSON：900px title.bottom61.328、680/600px69.297，超過header56；此subtask未核收該raw JSON/path（unknown，不能把回報冒充親讀）。243 source還未套用最後small nowrap／hidden／ellipsis修復。Root已計畫於243凍結驗收後完成，保留11/13字級、56px header與44px控制。舊fullSpace titleWidth通過只測寬度，不能聲稱完整vertical bounds；X2/B1因此保留待修。

## 本版已核讀的有限 browser 結果

此subtask沒有執行browser。已核讀同版乾淨243的原v4 probe與獨立核對收據：原四scope **185通過／2失敗、exit1、acceptanceCompleted:false**。原probe completed:true只是四scope均attempted，不能改成完整驗收成功。核對收據原檔SHA256 `72314c2a9ff61d77cd6e7f1073e5cd1f5da94b7c1b0613ebeb4b67dfbbfb4074`，保留在evidence/，原始gate/log位置與hash維持原收據。

- plan **16/0**與BOM **44/0**各自在desktop／390完成，只承認原scope。
- row-blur **32/1**：第33項「Cancel後所有API為0」觀察到`source-inspect`／`engineering-read`兩只readonly請求而失敗。原失敗保留，不能在原執行後改oracle聲稱通過。其後direct retirement、native-after、新candidate与390未到。
- S2 **86/1**：desktop **84/0**完整至trustededitingevents，含same-ID import detach、原舊callback與B continuation；390只通過New確認與nativefixture兩個setup，第三步normal點擊hidden `#toggleRight`失敗，不能替尚未到的390行為補PASS。

另已親讀同版正式fullSpace原gate／result／raw log，乾淨full243 before／after、`node geometry-web/space_model_test.js` exit0、唯一`SPACE_RESULT` **228/0 completed:true**，scope為`full-space-suite`且明列略過`timber-material`／`timber-source-guards`；原件另保留在evidence/full-space-243/。其中font-layout **19/0**，source833–834只檢`titleWidth>0`，不讀title top／bottom，不能證明標題vertical bounds。原執行者Node／Chromium身分、命令與source／native版本均保留原gate，不在此重跑。正式#54 ten-normal／six-negative／six-cost、最新正式六組、fullCDP／all43／private ZIP均不從這些scope補全；同版必需後段應另有實際收據。這些有限觀測不把任何43整項或SOURCE_PENDING標為結案。

## 全部43 inventory（每列新source註記）

欄位 SOURCE_WIRED 只表示可攜採納切片接線；帶UNKNOWN／POLICY的列不得變成新規格。有限browser scope見上節及source-followup.json逐項欄位，不表示43整項驗收。實名／line連結均綁完整243 SHA。

| ID | 原可攜階段 | 本版source狀態 | 243 source續註／原生界線 | 凍結source位置 |
|---|---|---|---|---|
'''
for item in items:
 links='<br>'.join('['+r['path']+':'+str(r['line'])+']('+r['url']+')' if 'line' in r else '`'+r['path']+'` exact anchor unknown' for r in item['sourceReferences'])
 doc+='| '+item['id']+' | '+item['portablePhase']+' | '+item['sourceStatus']+' | '+item['currentSourceNote'].replace('|','\\|')+' | '+links+' |\n'
doc+='''
## 保留的原native／DOM／驗收契約

既有DOM ID、native values、typed sources、快捷鍵、原返回／保存／Undo/Redo、I8/I8a候選預覽／明確確認／取消／原子回滾不變。孔洞R和原形狀語義、投影R7–R15／cut-strip與no-op／完整交易、outer/hole/vertex-key、custom rational以及格距／像素讀值不重造。C1是呈現，nearby RC、額外snapping與未定案row-removal是決策點。原五layer groups／empty入口、GEO216狀態區分與#119完整性診斷保留。

C-review可攜適用要點仍是：不能在原native impact前加第二confirm；G3 normal caller要先開唯一delete disclosure再沿原preview/cancel/history；網格preview/main先於settings以對齊DOM/Tab，sticky猜想不是修復；B6不能用不同已讀／選取狀態互換；真label是.fe-dim.fe-edge-dim；marquee browser段經完整CDP，不把單獨unit跑法當UI證據；F6保留confirmBottom<=setup-scroll.bottom及44px而非縮字取得通過；F5已量smCanvas不代表face toolbar量過。

新版仍須依AGENTS與正式gates核完整CDP／Space、桌面與390px真pointer／Tab／Enter／Space、hit與focus、pending raw／invalid rows／Review/Confirm、same-ID owner／stale回覆與inert cleanup、native preview取消／Undo/Redo與完整gcanvas保存重開。正常renderer幾何及既有nativecontract不變；禁止force click／削弱原断言／無限retry。原本準備的S2 supplement只是獨立scope；它的legacy six headers缺少新formal oracle，不替代最新正式六組。測試執行／版本與full完成狀態只依各自原receipt，不相加partial。

真正未定案：私人ZIP與稿件冲突／像素；原issue尺寸32/36/44與稿40、input32/36／座標位置／ID兼容消歧；C5/C7精確刪除、C6 nearby policy、B8/G1/G2私人目標。其他已採納source與必要驗收繼續，不等待已停止作者另釋放。原CDP2207/0/0仍只屬乾淨5174a8dafd8c48329d7166abbd3d104e3c28c0c4；#173 Windows1692/2、exit1、completed:false、未比對golden歷史維持，Windows原件未核收不請原作者重做。

## 640原43逐項註記（原樣保留）

下列只是原audit摘錄，並非243當下判定；原件另存authority/並保留hash。source已修的舊remaining字樣不回寫成歷史當時已修。

'''+history.decode().split('All 43 IDs were examined against available authority and current source:',1)[1].split('The report has not compared',1)[0]
doc+='\n## 可攜原issue S0–S6 原句\n\n'+ '\n'.join(phases.values())+'\n\n原issue完整body與可攜原句在authority/issue123-original.json，来源 '+issue['html_url']+'；此任務沒有重新fetch或聲稱取得private ZIP。\n'
target=OUT/'issue123-43-source-followup-243326.md';save(target,doc.encode())
structured={'schema':'geometry-issue123-43-source-followup/1','sourceSHA':BASE,'historicalAuditSHA':HIST,'fiveCorrectionSHA':FIVE,'items':items,'sourcePending':titlePending,'limited243ReadEvidence':limited,'fullSpace243':fullSpace,'portableOriginalPhases':phases,'originalIssueURL':issue['html_url'],'authorityQualification':'Retained portable original issue and historic handoff/self-authored summaries; private ZIP not received','browserAcceptedAt243':False,'all43ProductAccepted':False,'nativeContractsChanged':False}
save(OUT/'source-followup.json',(json.dumps(structured,ensure_ascii=False,indent=2)+'\n').encode())
beforeHashes={str(historyPath):sha(history),str(issuePath):sha(issueBytes)}
checkHistorical={path:sha(Path(path).read_bytes())==digest for path,digest in beforeHashes.items()}
assert all(checkHistorical.values())
receipt={'schema':'geometry-issue123-43-source-followup-preparation/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requestedFullSourceSHA':BASE,'observedHeadBefore':head,'dirtyBefore':dirty,'observedHeadAfter':git('rev-parse','HEAD').decode().strip(),'dirtyAfter':git('status','--short').decode(),'sourceMode':'immutable git show full243; no checkout or Git write','sources':records,'authority':[{'path':str(historyPath),'sha256':sha(history),'retainedPath':str(OUT/'authority/issue123-43-current640-source-audit.md')},{'path':str(issuePath),'sha256':sha(issueBytes),'retainedPath':str(OUT/'authority/issue123-original.json')}],'evidenceSourcesRead':evidenceSources,'originalAuthorityUnchanged':checkHistorical,'historicalAMapFullSourceSHA':BASE,'historicalAMapChanged':False,'itemCount':43,'ids':ids,'sourcePending':titlePending,'report':str(target),'reportSHA256':sha(target.read_bytes()),'structured':str(OUT/'source-followup.json'),'structuredSHA256':sha((OUT/'source-followup.json').read_bytes()),'command':[sys.executable,str(Path(__file__))],'cwd':str(OUT),'exitCode':0,'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__).read_bytes())},'executionFile':{'path':str(Path(sys.executable).resolve()),'sha256':sha(Path(sys.executable).resolve().read_bytes()),'version':sys.version},'browserExecuted':False,'nativeExecuted':False,'serviceExecuted':False,'repoWrites':False,'formalTestWrites':False,'gitWrites':False,'newHeadBrowserPassClaimed':False,'unknownSourceAnchors':[r for item in items for r in item['sourceReferences'] if 'line' not in r]}
save(OUT/'source-preparation-receipt.json',(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'report':str(target),'reportSHA256':receipt['reportSHA256'],'fullSourceSHA':BASE,'sourceFiles':len(records),'ids':len(ids),'sourcePending':'X2/B1 title vertical bounds','unknownAnchors':len(receipt['unknownSourceAnchors']),'newHeadBrowserPassClaimed':False},ensure_ascii=False))
