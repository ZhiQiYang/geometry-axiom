from pathlib import Path
p=Path('/tmp/train337-adversarial/review_L_timber_actual_package.py')
s=p.read_text().replace('timber','canvas').replace('TIMBER','CANVAS')
s=s.replace("O=Path('/tmp/train337-adversarial')", "O=Path('/workspace/train337-canvas-peer-resume')")
s=s.replace('a0765752370609ad48816af7b94989074bfc51ce5af6d52782011fdb440c1b37','4153cafa4e1a24b75368a31c4fe8c71ab7b8bb5dde056c55880820bb41b78dbc').replace('26c52274af2a3e0c57caae6d1d28c6a961d15608cef11c0312f59ca33abb61b5','9c2d80ce5aabe9791895275a2244ed170a836868639f332f941744826ec1b96b')
s=s.replace('len(inv)==659','len(inv)==741').replace("p['memberCount']==660","p['memberCount']==742").replace('len(ms)==660','len(ms)==742')
s=s.replace("r['ci_timeout_minutes']==20", "r['ci_timeout_minutes']==35").replace("r['seconds']<1200", "r['seconds']<2100").replace("original CI20 unrelaxed", "original CI35 unrelaxed").replace("]['timeout']==20", "]['timeout']==35").replace('workflow canvas20','workflow canvas35')
a=s.index("stdout=(J/'steps/03.stdout').read_text();")
b=s.index("env=r['environment'];",a)
s=s[:a]+'''stdout=(J/'steps/03.stdout').read_text();lines=[x for x in stdout.splitlines() if x.startswith('CDP_RESULT ')];ck(len(lines)==1,'one original full CDP_RESULT');result=json.loads(lines[0].split(' ',1)[1])
ck(result['completed'] and result['passedAssertions']==2267 and result['failedAssertions']==0 and result['skipped']==[] and result['goldenCompare']=='matched','2267/0 complete no skip golden matched')
ck(result['scope']['mode']=='full' and result['scope']['filters']==[] and result['scope']['modifiers']==[] and result['scope']['cdpPort']==9333,'full unfiltered canvas CDP9333')
golden_path='geometry-web/cdp_sections.golden.json'
golden_git=subprocess.run(['git','-C','/workspace/geometry-axiom','show',L+':'+golden_path],capture_output=True)
golden=json.loads(golden_git.stdout)
ck(golden_git.returncode==0 and golden_git.stdout==(Path(r['checkout_before']['root'])/golden_path).read_bytes(),'original Git L golden exact bytes')
ck(golden['sections']==result['sections'] and golden['total']==2267 and len(golden['sections'])==85 and sum(result['sections'].values())==2267,'all85 original golden section counts exact')
ck(result['sections']['P88']==143 and result['sections']['P73']==69,'original P88/P73 counts')
ck(result['uncaughtBrowserExceptions']==1 and stdout.count('[EXPECTED EXCEPTION] Error: fb-auto-probe')==1 and '[UNEXPECTED EXCEPTION]' not in stdout,'one original intentional P38 exception; not claimed zero exceptions')
ck('P38 預期的單次例外確實抵達 ✓' in stdout and 'P38 未捕捉的 JS 例外自動存一筆 kind=auto ✓' in stdout,'original expected exception checked')
ck('[CDP FLOOR] 與 golden 逐段相符(85 段)' in stdout and (J/'steps/03.stderr').read_bytes()==b'','strict golden original marker and empty stderr')
artifact_paths=[x for x in r['files'] if x.startswith('artifacts/')]
ck(len(artifact_paths)==5 and len([x for x in artifact_paths if x.endswith('.png')])==4,'five original local artifact files, four screenshots')
trace=read(J/'artifacts/04/geometry-wait-trace-artifact/receipt.json')
ck(trace['status']=='trace-disabled-for-this-runner' and trace['records']==0 and trace['head']==L and trace['effectiveEnvironment']['GEOMETRY_WAIT_TRACE'] is None,'original nonWSL trace disabled receipt; no trace claimed')
''' + s[b:]
s=s.replace("http://127.0.0.1:19086/", "http://127.0.0.1:19081/").replace("==80,'threeELF/80cache explicit exclusions'", "==82,'threeELF/82cache explicit exclusions'")
a=s.index("ck(result['scope']['mode']=='partial'")
s=s[:a]+'''report={'schema':'independent-final-L-canvas-actual-package-peer/1','checks':checks,'exit_code':int(bool(findings)),'findings':findings,'source_sha':L,'original_exit':0,'wrapper_exit':0,'passed_assertions':2267,'failed_assertions':0,'skipped':[],'golden_sections':85,'golden_compare':'matched','P88':143,'P73':69,'recorded_browser_exceptions':1,'exception_classification':'Exactly one original intentional P38 fb-auto-probe; expected marker and P38 assertions passed, no UNEXPECTED EXCEPTION marker. Transport/network failure receipts are original fault-injection diagnostics retained, not hidden.','workflow_local_artifact_files':5,'workflow_screenshot_files':4,'elapsed_seconds':r['seconds'],'ci_timeout_minutes':35,'archive_sha256':p['archiveSHA256'],'member_count':742,'raw_original_bytes':p['originalLogicalBytes'],'limits':s['limits'],'scope':'All archived members compared with immutable original bytes/symlinks; exact L workflow, original job/launcher/reaper raw, closed pool guards, source fingerprint inputs and declared exclusions verified. No browser/test rerun. Native and specialist results are not inferred.'}
q=O/'FINAL_L_CANVAS_ACTUAL_PACKAGE_PEER.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\\n');print(json.dumps({'checks':checks,'exit_code':report['exit_code'],'findings':findings,'report':str(q),'sha256':h(q)},ensure_ascii=False));sys.exit(report['exit_code'])
'''
out=Path('/workspace/train337-canvas-peer-resume/review_L_canvas_actual_package.py');out.write_text(s)
