"""Check already recorded integer inputs/dumps; never launch/import the product."""
from pathlib import Path
import json
import re

D = Path(__file__).parent
def cells(poly):
    assert all(a[0] == b[0] or a[1] == b[1] for a,b in zip(poly,poly[1:]+poly[:1]))
    out = set()
    for x in range(min(p[0] for p in poly), max(p[0] for p in poly)):
        for y in range(min(p[1] for p in poly), max(p[1] for p in poly)):
            crossings = 0
            for a,b in zip(poly,poly[1:]+poly[:1]):
                if a[0] == b[0] and 2*a[0] > 2*x+1 and 2*min(a[1],b[1]) < 2*y+1 < 2*max(a[1],b[1]):
                    crossings += 1
            if crossings % 2:
                out.add((x,y))
    return out

def components(points):
    remaining = set(points)
    found = []
    while remaining:
        todo = [remaining.pop()]
        seen = set(todo)
        while todo:
            x,y = todo.pop()
            for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if p in remaining:
                    remaining.remove(p); seen.add(p); todo.append(p)
        found.append(seen)
    return found

def polygon(text):
    return [tuple(map(int, p.split(','))) for p in text.split()]
before = json.loads((D/'original-before-probe/stdout.bin').read_bytes())
after = json.loads((D/'original-after-probe/stdout.bin').read_bytes())
rows = []
for b,a in zip(before['cases'],after['cases']):
    assert b['name'] == a['name']
    cmds = b['commands']
    outline = polygon(cmds[1]['input'].split(' outline ',1)[1])
    match = re.fullmatch(r'line column 1 at (-?\d+) (-?\d+) size (\d+) (\d+) z 0 100',cmds[2]['input'])
    x,y,w,h = map(int,match.groups())
    footprint = {(u,v) for u in range(x,x+w) for v in range(y,y+h)}
    room = cells(outline); intersection = room & footprint
    parts = components(intersection)
    row = {'case':b['name'], 'original_area_mm2':len(room), 'footprint_area_mm2':len(footprint),
           'intersection_area_mm2':len(intersection), 'component_areas_mm2':sorted(map(len,parts)),
           'component_bounds':sorted([min(u for u,v in p),min(v for u,v in p),max(u for u,v in p)+1,max(v for u,v in p)+1] for p in parts)}
    if b['name'] == 'A':
        assert len(intersection)==600 and len(parts)==2 and sorted(map(len,parts))==[300,300]
        assert row['component_bounds']==[[30,50,40,80],[60,50,70,80]]
        assert a['commands'][3]['output']['text']==a['commands'][6]['output']['text']
        row['saved_dump_after_rejection_identical']=True
    else:
        assert len(intersection)==200 and row['component_bounds']==[[40,70,60,80]]
        dump=a['commands'][6]['output']['text']
        boundaries={}; plane_ids=[]
        for line in dump.splitlines():
            m=re.fullmatch(r'boundary (\d+) outline (.+)',line)
            if m:boundaries[int(m[1])]=polygon(m[2])
            m=re.fullmatch(r'placement (\d+) on boundary (\d+) origin 0 0 (-?\d+) u \+x v \+y',line)
            if m and int(m[3])==0:plane_ids.append(int(m[2]))
        assert plane_ids==[1,2], plane_ids
        saved=[cells(boundaries[n]) for n in plane_ids]
        assert not (saved[0]&saved[1])
        union=set().union(*saved)
        expected=room-intersection
        assert union==expected and len(union)==5600
        row.update({'saved_z0_boundary_ids':plane_ids,'saved_component_areas_mm2':list(map(len,saved)),
                    'saved_union_mm2':len(union),'saved_components_disjoint':True,
                    'saved_union_equals_original_minus_intersection':True,
                    'excluded_from_same_plane_comparison':'boundary 3 has placement origin z=70 in the recorded dump'})
    rows.append(row)
result={'exit_code':0,'cases':rows,
        'scope':'derived analysis of historical recorded integer geometry; no new C/native run, no new fixture or semantic decision',
        'limits':['Integer open-cell area/interior equality only; not a proof of zero-area boundary topology, metadata, renderer ghosts, or current-source execution.',
                  'No application success inferred from positive contact alone; successful B application comes from the preserved after probe.']}
(D/'RECORDED_GEOMETRY_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
