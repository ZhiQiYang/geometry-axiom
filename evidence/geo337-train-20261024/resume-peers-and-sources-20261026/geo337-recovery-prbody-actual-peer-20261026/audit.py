from pathlib import Path
from datetime import datetime,timezone
import hashlib,json

OUT=Path('/tmp/geo337-recovery-prbody-actual-peer-20261026')
OWN=Path('/dev/shm/geometry-axiom-geo337-20261025')
ROOT=OWN/'recovery-prbody-root-original-20261026'
INNER=OWN/'recovery-prbody-publication-20261026'
COMMIT='ce0c3f0ad5af51670cbfd5266d3dd4474843026a'
PARENT='9a57aea2128a7bc3985064932c24e2229fd8fcb8'
HEAD='3e4f2560aa11ed2a626db98ba5ed6f129e791052'
BRANCH='refs/heads/codex/train337-recovered-evidence-20261026-prbody'
BODY_PIN='14d3271cc50438aaf82415031044070f2d22065804214c65631aeea08ccc6137'
checks=0;errors=[]
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def check(v,label):
    global checks
    checks+=1
    if not v:errors.append(label)
def stream(row,name='stdout'):return (Path(row['directory'])/(name+'.bin')).read_bytes()
def timestamp(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()

root=read(ROOT/'RESULT.json');inner=read(INNER/'RESULT.json');body=(ROOT/'PR_BODY.md').read_bytes();text=body.decode()
check(root['exit_code']==0 and root['published'] and root['delivered'],'root true delivery0')
check(root['existing_PR_body_updated'] is False,'existing #338 body not updated')
check(root['body_commit']==inner['newCommit']==COMMIT,'exact body commit')
check(inner['expectedParent']==PARENT and inner['branch']==BRANCH,'exact parent/branch')
check(inner['passed'] and inner['published'] and inner['errors']==[] and inner['headAndIndexUnchanged'],'inner pass and preservation')
check(len(body)==root['body_bytes']==4537 and H(body)==root['body_sha256']==inner['bodySha256']==BODY_PIN,'exact delivered body bytes')
blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
check(blob==inner['newBodyBlob']=='b257ccd2769a98b91be01892739ff851db716cf2','body Git blob OID')
before=read(ROOT/'BEFORE.json');after=read(ROOT/'AFTER.json')
check(before==after,'stored physical index and HEAD/train snapshots identical')
check(before['head']==before['train']==HEAD+'\n','existing train HEAD preserved')
check(before['index']=='7a0cdcc3cc447eb2fae06aec47e97cf24f192aa62ed383839dc7b21e18942842','stored exact physical-index hash')
rows_root=read(ROOT/'subcommands.json');rows_inner=read(INNER/'subcommands.json');all_rows=rows_root+rows_inner
catalog=[];total_bytes=0
for r in all_rows:
    p=Path(r['directory']);actual=read(p/'result.json');request=read(p/'request.json')
    check(actual==r,'original aggregate '+str(p))
    for k in ['command','cwd','acceptance_sha','source_sha','source_variant','environment','stdin_provided','stdin_sha256','started_epoch']:
        check(request.get(k)==r.get(k),'stable request/result '+k+' '+str(p))
    check(type(r['actual_process_returncode']) is int and r['actual_process_returncode']==0 and r['timeout_expired'] is False,'actual terminal0 no timeout '+str(p))
    for name in ['stdin','stdout','stderr']:
        b=stream(r,name);total_bytes+=len(b)
        check(H(b)==r[name+'_sha256'],'original stream hash '+name+' '+str(p))
        if name!='stdin':check(len(b)==r[name+'_bytes'],'original stream byte length '+name+' '+str(p))
        catalog.append([str(p/(name+'.bin')),len(b),H(b)])
    cmd=r['command']
    check(not any(x in cmd for x in ['checkout','switch','reset','merge','rebase','clean','--force','--force-with-lease']),'no forbidden Git mutation '+str(p))
    if 'update-ref' in cmd:
        pos=cmd.index('update-ref');check(cmd[pos+1]==BRANCH,'only new prbody ref write')
    if 'push' in cmd:check(cmd[-1].endswith(':'+BRANCH) and not cmd[-1].startswith('+'),'normal only prbody push')
    if cmd[0]=='gh':check(cmd==['gh','api','--hostname','github.com','-H','Accept: application/vnd.github.raw+json','repos/ZhiQiYang/geometry-axiom/git/blobs/'+blob],'only read raw body API')
check(len(rows_root)==10 and len(rows_inner)==21 and len(catalog)==93,'complete31 commands93 raw streams')
remote=next(r for r in rows_root if r['command'][0]=='gh')
check(stream(remote)==body and H(stream(remote))==BODY_PIN,'actual remote full raw body matches original')
remote_refs=[r for r in rows_inner if 'ls-remote' in r['command']]
check(len(remote_refs)==3,'original three branch observations')
check(stream(remote_refs[-1])==(COMMIT+'\t'+BRANCH+'\n').encode(),'last remote resolves exact body commit')
check(all(stream(r)==(PARENT+'\t'+BRANCH+'\n').encode() for r in remote_refs[:-1]),'parent observations before push')
diffrow=next(r for r in rows_inner if 'diff-tree' in r['command']);check(stream(diffrow)==b'PR_BODY.md\0','exact single root PR_BODY leaf diff')
hashrow=next(r for r in rows_inner if 'hash-object' in r['command']);check(stream(hashrow,'stdin')==body and stream(hashrow).decode().strip()==blob,'body stdin stored exact')
commitrow=next(r for r in rows_inner if 'commit-tree' in r['command']);check(stream(commitrow).decode().strip()==COMMIT and commitrow['command'][-2:]==['-p',PARENT],'commit exact parent and result')
def tree(b):
    return {line.split(b'\t',1)[1]:line.split(b'\t',1)[0] for line in b.split(b'\0') if line}
trees=[r for r in rows_inner if 'ls-tree' in r['command']];check(len(trees)==2,'old/new root trees captured')
old=tree(stream(trees[0]));new=tree(stream(trees[1]));new_without_body={k:v for k,v in new.items() if k!=b'PR_BODY.md'};old_without_body={k:v for k,v in old.items() if k!=b'PR_BODY.md'}
check(new_without_body==old_without_body and new[b'PR_BODY.md']==('100644 blob '+blob).encode(),'all other root tree entries/modes/OIDs retained')
for name,key in [('HEAD','head'),('refs/heads/codex/train-337-continue-20261024','train')]:
    observed=[r for r in rows_root if r['command'][-2:]==['rev-parse',name]]
    check(len(observed)==2 and all(stream(r).decode()==before[key] for r in observed),'full original before/after '+key)
for phrase in ['尚未固定；未宣告全綠或 READY-TO-MERGE','已生成，尚未採入產品路徑','不冒S10原件為a6當次執行','完整新final仍UNRUN','保F9來源，不移標','原outer1與原取樣保留，不重抽','原P-189 exact紅燈保留','尚未取得新的原始批准紀錄','自動核准審查拒絕3156葉暫存退役','命令未啟動，刪除0','不拆批或改路徑繞過','未自動覆蓋原#338正文或請求檔']:
    check(phrase in text,'body material limitation '+phrase)
check(text.count('| Gate | 真實結果 | 新 final 的界線 |')==1,'single current-state gate matrix')
report={'schema':'recovery-prbody-delivery-independent-actual-peer/1','reviewed_utc':datetime.now(timezone.utc).isoformat(),
 'exit_code':1 if errors else 0,'blocking_findings':errors,'checks':checks,'body_commit':COMMIT,'body_sha256':BODY_PIN,'body_bytes':len(body),
 'root_result_sha256':H((ROOT/'RESULT.json').read_bytes()),'inner_result_sha256':H((INNER/'RESULT.json').read_bytes()),
 'published':True,'full_remote_body_verified':not errors,'original_writer_HEAD_index_train_unchanged':before==after,
 'original_physical_index_sha256':before['index'],'existing_PR_338_updated':False,'original_command_count':31,'original_raw_stream_count':len(catalog),'original_raw_stream_bytes':total_bytes,
 'original_raw_catalog_sha256':H(json.dumps(catalog,separators=(',',':')).encode()),'remote_body_observed_utc':timestamp(remote['ended_epoch']),
 'current_state_update_notes':[{'item':'a6 三原裁判','severity':'update-next-body','note':'最新已完成的 a6 0/0/0、205/18 零skip尚未寫入此版架構列；應列當次來源/結果，與仍待相符四檔採用及新final分開。','actual_peer':'/tmp/geo337-a6-gates-actual-peer-20261026/REVIEW.json'},
  {'item':'108 個空cache目錄','severity':'approval-scope-detail','note':'正文說3156葉被拒，未明載原executor另會rmdir63子目錄+45白名單cache根目錄。供範圍批准時應同時引用精確批准包；不得默認原批准涵蓋。','approval_scope':'/tmp/geo337-retirement-approval-packet-20261026/SCOPE.json'},
  {'item':'native transition工具focused','severity':'optional-progress-detail','note':'原8case及四組0/1/0現已actual審核，可記工具準備完成；不可寫成native正式通過。'}],
 'limits':['Readonly original capture/bytes review; no network repeat, Git/ref update, body edit or test rerun.',
           'Delivery integrity0 does not certify every historical gate anew or establish a final SHA.',
           'Cleanup denial reason and request revocation are preserved as root/coordinator reported state; these31 publication commands contain no cleanup and do not independently audit every task action.',
           'This review verifies the private publisher HEAD/index/train snapshots, not all possible external Claude environments or remote main writers.']}
OUT.mkdir(exist_ok=True);target=OUT/'REVIEW.json'
if target.exists():raise RuntimeError('refuse overwrite existing review')
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(report['exit_code'])
