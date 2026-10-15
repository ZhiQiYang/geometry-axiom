"""Independent R43 test oracle over native panel fragments and D7 footprints.

This is a test consumer, never a PF-3 runtime implementation or a geometry
input bypass. The caller supplies the native bridge's validated readbacks.
The original single-footprint oracle remains separate from E1-legal.
"""
from fractions import Fraction


def footprint(geometry):
    """Map the native D7 anchor and axes into the E1 finish frame (+X,+Y)."""
    u,v=geometry["u"],geometry["v"]
    length,width=geometry["length"],geometry["A"]
    direction,cross,_=geometry["axes"]
    far=(u+length*direction[0]+width*cross[0],v+length*direction[1]+width*cross[1])
    return min(u,far[0]),min(v,far[1]),max(u,far[0]),max(v,far[1])


def _union(intervals):
    result=[]
    for lo,hi in sorted(intervals):
        if result and lo<=result[-1][1]:result[-1]=(result[-1][0],max(hi,result[-1][1]))
        else:result.append((lo,hi))
    return result


def _section(fragment,y):
    # Even/odd crossings include outer and hole rings. Samples are strictly
    # inside an open y band, so no endpoint epsilon or boundary guess is needed.
    xs=sorted(a[0] for ring in [fragment["outer"]]+fragment["holes"]
              for a,b in zip(ring,ring[1:]+ring[:1])
              if a[0]==b[0] and min(a[1],b[1])<y<max(a[1],b[1]))
    return list(zip(xs[::2],xs[1::2]))


def support(native_layout,rectangles,seam=100):
    fragments=[f for tile in native_layout["tiles"] for f in tile["fragments"]]
    ys={v for r in rectangles for v in (r[1],r[3])}
    ys.update(v for f in fragments for ring in [f["outer"]]+f["holes"] for _,v in ring)
    result=[]
    for low,high in zip(sorted(ys),sorted(ys)[1:]):
        y=Fraction(low+high,2)
        timber=_union((u0,u1) for u0,v0,u1,v1 in rectangles if v0<y<v1)
        values=[]
        for left in (True,False):
            board=[(lo,hi) for f in fragments for lo,hi in _section(f,y)
                   if (lo<seam<=hi if left else lo<=seam<hi)]
            covered=_union((max(a,c),min(b,d)) for a,b in timber for c,d in board if max(a,c)<min(b,d))
            values.append(next((seam-a if left else b-seam for a,b in covered
                                if (a<seam<=b if left else a<=seam<b)),0))
        # This witness has one continuous effective seam in (0,300).
        if not 0<=low<high<=300:continue
        if result and result[-1][1]==low and result[-1][2:]==values:result[-1][1]=high
        else:result.append([low,high,*values])
    return result
