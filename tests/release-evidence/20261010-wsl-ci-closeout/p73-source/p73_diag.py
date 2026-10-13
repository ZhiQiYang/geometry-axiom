import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
start_marker = "check('選已知邊一半產生引用式，位置與走向用語一致',await read(`"
i = s.find(start_marker)
assert i >= 0, 'start not found'
end_marker = "})`));"
j = s.find(end_marker, i)
assert j >= 0, 'end not found'
j += len(end_marker)
stmt = s[i:j]
diag = ("{const __dg=await read(`(async()=>{"
        "const snap=()=>({"
        "feGuides:(typeof fe!=='undefined'?fe.guides:[]).map(g=>({id:g.id,axis:g.axis,off:g.off})),"
        "loadSeq:(typeof fe!=='undefined'?fe.guidesLoadSeq:-1),"
        "busy:oc.busy,"
        "rows:[...document.querySelectorAll('[data-edit-guide]')].map(e=>e.dataset.editGuide)"
        "});"
        "const t0=snap();await new Promise(r=>setTimeout(r,1000));const t1=snap();"
        "const r=await apiRequest('references');"
        "return {t0,t1,guides:r.guides.map(g=>({id:g.id,expression:g.expression,axis:g.axis,off:g.off}))};"
        "})()`);console.log('DIAG-P73 '+JSON.stringify(__dg));")
s = s[:i] + diag + stmt + "}" + s[j:]
open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched')
