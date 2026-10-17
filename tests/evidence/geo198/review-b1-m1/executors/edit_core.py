from pathlib import Path
p=Path('/workspace/geometry-axiom/current_geometry.c')
data=p.read_bytes()
def change(old,new):
    global data
    a=old.replace('\n','\r\n').encode();b=new.replace('\n','\r\n').encode()
    assert data.count(a)==1,old[:80]
    data=data.replace(a,b)
change('/* 0 = disjoint; 1 = exact single rectangular contact; -1 = R7 degeneration.\n', '''/* Closed contact suffices for R14 ownership of an R12 uncut strip. It need
 * not be representable as a single cutting rectangle. */
static bool proj_rect_outline_touches(const PolygonLoop2 *loop,
    Coord u0, Coord v0, Coord u1, Coord v1)
{
    if (poly_contains_point(loop, (SurfacePoint2){u0,v0})) return true;
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i], b = loop->v[(i+1)%loop->count];
        if (coord_max(coord_min(a.u,b.u),u0) <= coord_min(coord_max(a.u,b.u),u1) &&
            coord_max(coord_min(a.v,b.v),v0) <= coord_min(coord_max(a.v,b.v),v1))
            return true;
    }
    return false;
}

/* 0 = disjoint; 1 = exact single rectangular contact; -1 = R7 degeneration.
''')
change('    int flush = 0;\n    bool f[4];', '''    /* Open slabs omit zero-area components. Every closed edge contact with
     * the original footprint must also lie in the positive-area rectangle. */
    for (size_t i = 0; i < loop->count; ++i) {
        SurfacePoint2 a = loop->v[i], b = loop->v[(i+1)%loop->count];
        Coord l = coord_max(coord_min(a.u,b.u),in_u0);
        Coord r = coord_min(coord_max(a.u,b.u),in_u1);
        Coord bottom = coord_max(coord_min(a.v,b.v),in_v0);
        Coord top = coord_min(coord_max(a.v,b.v),in_v1);
        if (l <= r && bottom <= top &&
                (l < u0 || r > u1 || bottom < v0 || top > v1)) return -1;
    }

    int flush = 0;
    bool f[4];''')
change('''                int contact = classify_rect_outline(&pb[j]->outline,
                        items[i].u_lo, items[i].v_lo,
                        items[i].u_hi, items[i].v_hi,
                        &pc, &t0, &t1, &t2, &t3);''','''                int contact;
                if (items[i].cls == OBSTACLE_STRIP && !cut_strip) {
                    /* R12 skips cutting, not R14 ownership or later R15 items. */
                    contact = proj_rect_outline_touches(&pb[j]->outline,
                            items[i].u_lo, items[i].v_lo,
                            items[i].u_hi, items[i].v_hi) ? 1 : 0;
                } else {
                    contact = classify_rect_outline(&pb[j]->outline,
                            items[i].u_lo, items[i].v_lo,
                            items[i].u_hi, items[i].v_hi,
                            &pc, &t0, &t1, &t2, &t3);
                }''')
assert b'\x00' not in data and data.replace(b'\r\n',b'').count(b'\n')==0
p.write_bytes(data)
