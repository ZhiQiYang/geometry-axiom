from pathlib import Path
root = Path.cwd()

def replace(path, old, new):
    data = path.read_bytes()
    assert data.count(old.encode()) == 1
    path.write_bytes(data.replace(old.encode(), new.encode()))

c = root/'tests/test_core_integrity.c'
block = '''static void test_projection_corner_contact_is_local(void)
{
    const PolygonLoop2 original={.count=12,.v={{0,10},{10,10},{10,0},{20,0},{20,10},{30,10},
        {30,20},{20,20},{20,40},{10,40},{10,20},{0,20}}};
    for (int variant=0; variant<16; ++variant) {
        PolygonLoop2 loop=original;
        Coord offset=(variant&8)?-50:0;
        size_t shift=(variant&4)?original.count-1:0;
        for (size_t i=0;i<loop.count;++i) {
            size_t at=(variant&1)?(shift+loop.count-i)%loop.count:(shift+i)%loop.count;
            SurfacePoint2 p=original.v[at];
            loop.v[i]=(variant&2)?(SurfacePoint2){p.v+offset,p.u+offset}:
                                    (SurfacePoint2){p.u+offset,p.v+offset};
            loop.fixity[i]=EDGE_FIXED;
        }
        CHECK(poly_loop_is_valid(&loop));
        Coord a,b,c,d; ObstacleClass cls;
        int corner_only_despite_remote_side_contact=classify_rect_outline(&loop,
            10+offset,10+offset,(variant&2)?30+offset:20+offset,
            (variant&2)?20+offset:30+offset,&cls,&a,&b,&c,&d);
        CHECK(corner_only_despite_remote_side_contact<0); /* R7: the corner itself has no positive edge. */
        Coord l=(variant&2)?20+offset:10+offset, bottom=(variant&2)?10+offset:20+offset;
        Coord r=(variant&2)?30+offset:20+offset, top=(variant&2)?20+offset:30+offset;
        CHECK(classify_rect_outline(&loop,l,bottom,r,top,&cls,&a,&b,&c,&d)>0);
        CHECK(cls==OBSTACLE_SPLIT); /* Same remote edges, but now positive contact begins at all corners. */
        bool flush[4]; for(int side=0;side<4;++side)flush[side]=side_flush_outline(&loop,side,a,b,c,d);
        PolygonLoop2 p1={0},p2={0};
        CHECK(proj_split_loop(&loop,flush,a,b,c,d,&p1,&p2));
        int area=0;
        CHECK(split_oracle_difference(&loop,&p1,&p2,a,b,c,d,&area));
        CHECK(area==500);
        CHECK(proj_loop_area2(&p1)+proj_loop_area2(&p2)==1000);
    }
}

'''
replace(c, 'static void test_projection_three_residual_components(void)\n', block+'static void test_projection_three_residual_components(void)\n')
replace(c, '    test_projection_three_residual_components();', '    test_projection_corner_contact_is_local();\n    test_projection_three_residual_components();')

p=root/'tests/test_reference_contract.py'
block='''    def test_rect_outline_remote_flush_does_not_excuse_corner_tangency(self):
        original = [(0,10),(10,10),(10,0),(20,0),(20,10),(30,10),
                    (30,20),(20,20),(20,40),(10,40),(10,20),(0,20)]
        for variant in range(16):
            verts = original[::-1] if variant & 1 else original[:]
            if variant & 4:
                verts = verts[-1:] + verts[:-1]
            offset = -50 if variant & 8 else 0
            def point(x,y):
                return ((y+offset,x+offset) if variant & 2 else (x+offset,y+offset))
            outline = ' '.join('%d,%d' % point(x,y) for x,y in verts)
            u0,v0 = point(10,10)
            w,h = (20,10) if variant & 2 else (10,20)
            hx,hy = point(12,2)
            direction = 'x' if variant & 2 else 'y'
            for strip in (False,True):
                for prior_hole in (False,True):
                    with self.subTest(variant=variant,strip=strip,prior_hole=prior_hole):
                        self.ok('reset')
                        self.ok('surface 1 origin 0 0 0 u +x v +y outline '+outline)
                        if strip:
                            self.ok(f'beam 1 along {direction} from {10+offset} to {30+offset} '
                                    f'at {15+offset} width 10 depth 10 top 0')
                        else:
                            self.ok(f'column 1 at {u0} {v0} size {w} {h} z 0 100')
                        if prior_hole:
                            self.ok(f'column 2 at {hx} {hy} size 4 4 z 0 100')
                        before,refs = self.dump(),self.refs()
                        command = 'apply-proj 1 '+('c2 ' if prior_hole else '')
                        command += 'b1 cut-strip' if strip else 'c1'
                        result = self.line(command)
                        self.assertFalse(result['ok'], 'R7: remote flush cannot excuse a point-only corner')
                        self.assertIn('R7',result['error'])
                        self.assertEqual(before,self.dump(), 'whole transaction, including prior hole, must roll back')
                        self.assertEqual(refs,self.refs())
                        self.ok('undo')
                        self.ok('redo')
                        self.assertEqual(before,self.dump(), 'rejected apply must not enter redo history')
                        self.roundtrip()

'''
replace(p,'    def test_rect_outline_three_residual_components_rejects_and_rolls_back(self):\n',block+'    def test_rect_outline_three_residual_components_rejects_and_rolls_back(self):\n')
replace(p,"        fixtures = [\n", "        fixtures = [\n            ('0,10 10,10 10,0 20,0 20,10 30,10 30,20 20,20 20,40 10,40 10,20 0,20',\n             '10 20 size 10 10', (10,20,20,30), 500),\n")

outline='0,10 10,10 10,0 20,0 20,10 30,10 30,20 20,20 20,40 10,40 10,20 0,20'
(root/'_ax_r7_remote_flush_corner.scene').write_text('surface 1 origin 0 0 0 u +x v +y outline '+outline+'\ncolumn 1 at 10 10 size 10 20 z 0 100\napply-proj 1 c1\n')
(root/'_ax_r7_remote_flush_strip.scene').write_text('surface 1 origin 0 0 0 u +x v +y outline '+outline+'\nbeam 1 along y from 10 to 30 at 15 width 10 depth 10 top 0\ncolumn 2 at 12 2 size 4 4 z 0 100\napply-proj 1 c2 b1 cut-strip\n')
replace(root/'tests/run_tests.py','TESTS = [\n',"TESTS = [\n {'scene': '_ax_r7_remote_flush_corner.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},\n {'scene': '_ax_r7_remote_flush_strip.scene', 'expect': 'reject', 'error': 'R7: 投影接觸非單一矩形'},\n")
