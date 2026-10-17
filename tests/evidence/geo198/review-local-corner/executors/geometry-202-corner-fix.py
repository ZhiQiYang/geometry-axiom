from pathlib import Path
p=Path('current_geometry.c');data=p.read_bytes()
old=b'''    /* A point-only corner contact is not a hole (R7); do not guess a notch. */
    SurfacePoint2 corners[4] = {{u0,v0},{u1,v0},{u1,v1},{u0,v1}};
    const int adjacent[4][2] = {{0,2},{1,2},{1,3},{0,3}};
    for (int i = 0; i < 4; ++i)
        if (!f[adjacent[i][0]] && !f[adjacent[i][1]] &&
                poly_point_on_edge(loop, corners[i])) return -1;
'''.replace(b'\n',b'\r\n')
new=b'''    /* R7: positive contact must begin at this corner, not elsewhere on its side. */
    SurfacePoint2 corners[4] = {{u0,v0},{u1,v0},{u1,v1},{u0,v1}};
    for (int i = 0; i < 4; ++i) {
        bool local_flush = false;
        for (size_t edge = 0; edge < loop->count; ++edge) {
            SurfacePoint2 a = loop->v[edge], b = loop->v[(edge+1)%loop->count];
            if (a.u == b.u && a.u == corners[i].u &&
                    coord_min(a.v,b.v) <= corners[i].v && corners[i].v <= coord_max(a.v,b.v) &&
                    coord_min(v1,coord_max(a.v,b.v)) > coord_max(v0,coord_min(a.v,b.v)))
                local_flush = true;
            if (a.v == b.v && a.v == corners[i].v &&
                    coord_min(a.u,b.u) <= corners[i].u && corners[i].u <= coord_max(a.u,b.u) &&
                    coord_min(u1,coord_max(a.u,b.u)) > coord_max(u0,coord_min(a.u,b.u)))
                local_flush = true;
        }
        if (!local_flush && poly_point_on_edge(loop, corners[i])) return -1;
    }
'''.replace(b'\n',b'\r\n')
assert data.count(old)==1;p.write_bytes(data.replace(old,new))
