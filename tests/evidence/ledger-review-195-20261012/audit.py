import hashlib,json,pathlib,subprocess,sys
root=pathlib.Path.cwd();base='ef719904913a50803c20fe632d93c0954042ea2e';mode=sys.argv[1]
original=subprocess.check_output(['git','show',base+':BACKLOG.md']).decode('utf-8')
current=(root/'BACKLOG.md').read_text();value=original if mode=='before' else current
def protected(text):return [s for s in text.splitlines() if '🔒' in s or '使用者' in s]
indices=[i for i,s in enumerate(value.splitlines()) if '🔒' in s or '使用者' in s]
if mode.startswith('mutant-'):
    lines=value.splitlines();a=indices[0];b=next(i for i in indices if lines[i]!=lines[a])
    if mode=='mutant-modify':lines[a]+=' mutation'
    elif mode=='mutant-delete':del lines[a]
    elif mode=='mutant-reorder':lines[a],lines[b]=lines[b],lines[a]
    else:raise ValueError(mode)
    value='\n'.join(lines)
issues=[];facts=[]
for issue,pr in ((257,192),(258,193)):
    live=json.loads(pathlib.Path(f'/tmp/geometry-195-pr{pr}.json').read_text());assert live['state']=='OPEN' and live['isDraft']
    begin=value.index(f'### GEO-{issue}');end=value.find('\n### ',begin+1);section=value[begin:end if end>=0 else None]
    row=next(s for s in value.splitlines() if s.startswith(f'| GEO-{issue} |'))
    heading=section.splitlines()[0];state=next(s for s in section.splitlines() if s.startswith('- **狀態**'))
    for location,text in (('table',row),('heading',heading),('state',state)):
        ok=f'#{pr}' in text and 'draft' in text and '進行中' in text and '未開始' not in text
        facts.append({'issue':issue,'pr':pr,'head':live['headRefOid'],'location':location,'text':text,'consistent':ok})
        if not ok:issues.append(f'GEO-{issue} {location}: active PR #{pr} is not recorded as in-progress draft')
begin=value.index('### GEO-248');end=value.index('\n### ',begin+1);section=value[begin:end]
excluded=section.split('- **不在採納範圍的 issue 驗收項**',1)[1]
excluded=excluded.split('\n- **',1)[0]
query=next(s for s in section.splitlines() if 'grid-rule-query' in s)
if 'exact／sample' in excluded or '已採納' not in query or '另案確認' in query:
    issues.append('exact/sample query already adopted by I25a/I37/R32 is still labelled outside adoption')
ssot=(root/'公理層.md').read_text();assert '來源規則唯讀查詢：grid-rule-query' in ssot and 'mode exact|sample limit N' in ssot
same=protected(value)==protected(original)
if not same:issues.append('Protected locked/user text or ordering changed')
payload={'mode':mode,'scope':'Ledger/source/remote-state audit only; no product or seven-job execution',
    'source_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'facts':facts,'query_line':query,
    'lock_lines':sum('🔒' in s for s in original.splitlines()),'user_mention_lines':sum('使用者' in s for s in original.splitlines()),
    'protected_union_lines':len(protected(original)),'protected_equal':same,'issues':issues,
    'protected_original_sha256':hashlib.sha256('\n'.join(protected(original)).encode()).hexdigest(),
    'protected_current_sha256':hashlib.sha256('\n'.join(protected(value)).encode()).hexdigest()}
print(json.dumps(payload,ensure_ascii=False,indent=2));sys.exit(1 if issues else 0)
