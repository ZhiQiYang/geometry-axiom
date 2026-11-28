"""D13/D14 research construction plus an independent inverse-interval checker.

No imports from the product; exact decimal observations use Fraction. The
checker inspects supplied intervals, their widths/centres and vertical relation
directly; it never calls construct() or compares to a second constructed box.
"""
import copy
import hashlib
import itertools
import json
import re
from fractions import Fraction

LIMIT = 100000000
FIELDS = {'rc-column': ['x','y','width','depth','bottom','top','height'],
          'rc-beam': ['start','end','center','width','depth','bottom','top']}

def scalar(raw, unit, positive=False):
    assert isinstance(raw, str) and re.fullmatch(r'[-+]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)', raw), 'N1_LITERAL'
    assert unit in ('mm','cm'), 'N1_UNIT'
    exact=Fraction(raw)*(10 if unit=='cm' else 1)
    assert exact.denominator==1 and abs(exact)<=LIMIT and (not positive or exact>0), 'N1_EXACT_MM'
    return int(exact)

def construct(case):
    v=case['values'];k=case['kind']
    assert k in FIELDS and set(v)==set(FIELDS[k]), 'N1_FIELDS'
    assert all(type(x) is int and abs(x)<=LIMIT for x in v.values()), 'N1_DOMAIN'
    assert all(v[x]>0 for x in ('width','depth')+ (('height',) if k=='rc-column' else ())), 'N1_POSITIVE'
    if k=='rc-column':
        assert v['bottom']+v['height']==v['top'], 'N1_VERTICAL'
        rect=[v['x'],v['y'],v['x']+v['width'],v['y']+v['depth']]
    else:
        assert case['axis'] in ('x','y') and v['end']>v['start'], 'N1_BEAM_AXIS'
        assert v['bottom']+v['depth']==v['top'], 'N1_VERTICAL'
        sides=[v['center']-v['width']//2,v['center']+(v['width']+1)//2]
        rect=[v['start'],sides[0],v['end'],sides[1]] if case['axis']=='x' else [sides[0],v['start'],sides[1],v['end']]
    assert all(abs(x)<=LIMIT for x in rect) and max(rect[2]-rect[0],rect[3]-rect[1],v['top']-v['bottom'])<=LIMIT, 'N1_ENDPOINT'
    return {'id':case['id'],'type':'column' if k=='rc-column' else 'beam','rect':rect,'bottom_z':v['bottom'],'top_z':v['top']}

def check(case, result):
    def need(ok, code):
        assert ok, code
    need(type(result) is dict and set(result)=={'id','type','rect','bottom_z','top_z'}, 'N1_CHECK_SHAPE')
    v=case['values'];r=result['rect']
    need(result['id']==case['id'] and result['type']==('column' if case['kind']=='rc-column' else 'beam'), 'N1_CHECK_ID_TYPE')
    need(isinstance(r,list) and len(r)==4 and all(type(x) is int and abs(x)<=LIMIT for x in r), 'N1_CHECK_DOMAIN')
    need(all(type(result[k]) is int and abs(result[k])<=LIMIT for k in ('bottom_z','top_z')), 'N1_CHECK_Z_DOMAIN')
    need(0<r[2]-r[0]<=LIMIT and 0<r[3]-r[1]<=LIMIT and 0<result['top_z']-result['bottom_z']<=LIMIT, 'N1_CHECK_INTERVAL')
    need(result['bottom_z']==v['bottom'] and result['top_z']==v['top'], 'N1_CHECK_Z')
    if case['kind']=='rc-column':
        need((r[0],r[1])==(v['x'],v['y']), 'N1_CHECK_COLUMN_ORIGIN')
        need((r[2]-r[0],r[3]-r[1])==(v['width'],v['depth']), 'N1_CHECK_COLUMN_EXTENT')
        need(result['top_z']-result['bottom_z']==v['height'], 'N1_CHECK_COLUMN_HEIGHT')
    else:
        along=(r[0],r[2]) if case['axis']=='x' else (r[1],r[3]);cross=(r[1],r[3]) if case['axis']=='x' else (r[0],r[2])
        need(along==(v['start'],v['end']), 'N1_CHECK_BEAM_AXIS')
        need(cross[1]-cross[0]==v['width'] and cross[0]<=v['center']<=cross[1], 'N1_CHECK_BEAM_WIDTH')
        need(0<=cross[1]+cross[0]-2*v['center']<=1, 'N1_CHECK_ODD_POSITIVE')
        need(result['top_z']-result['bottom_z']==v['depth'], 'N1_CHECK_BEAM_DEPTH')
    return True

def cases():
    rows=[]
    for x,y,w,d,b,h in itertools.product(range(-1,2),range(-1,2),range(1,4),range(1,4),range(-1,2),range(1,4)):
        rows.append(dict(id='rd-1',kind='rc-column',axis=None,values=dict(x=x,y=y,width=w,depth=d,bottom=b,top=b+h,height=h)))
    for a,c,w,s,length in itertools.product(('x','y'),range(-1,2),range(1,6),range(-1,2),range(1,4)):
        rows.append(dict(id='rd-1',kind='rc-beam',axis=a,values=dict(start=s,end=s+length,center=c,width=w,depth=31,bottom=-20,top=11)))
    return rows

def main():
    rows=[];rejected=0
    for case in cases():
        out=construct(case);check(case,out);rows.append(dict(case=case,expected=out))
        corrupt=copy.deepcopy(out);corrupt['rect'][0]+=1
        try: check(case,corrupt)
        except AssertionError: rejected+=1
        else: raise AssertionError('N1_CHECKER_CORRUPTION_SURVIVED')
    typed_rejected=0
    example=next(row for row in rows if row['case']['kind']=='rc-column' and row['expected']['bottom_z']==0 and row['expected']['top_z']==1)
    for key,bad in [('bottom_z',False),('top_z',True)]:
        corrupt=copy.deepcopy(example['expected']);corrupt[key]=bad
        try: check(example['case'],corrupt)
        except AssertionError as error:
            assert str(error)=='N1_CHECK_Z_DOMAIN', 'N1_BOOLEAN_Z_REJECTION_REASON'
            typed_rejected+=1
        else: raise AssertionError('N1_BOOLEAN_Z_CORRUPTION_SURVIVED')
    raw=json.dumps(rows,sort_keys=True,separators=(',',':'))
    print(json.dumps(dict(schema='r13-n1-geometry-oracle/1',rows=rows,count=len(rows),corruptionsRejected=rejected,typedCorruptionsRejected=typed_rejected,sha256=hashlib.sha256(raw.encode()).hexdigest()),separators=(',',':')))

if __name__=='__main__':main()
