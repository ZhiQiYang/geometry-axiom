/* D10a/D10b/D29/D43: shared integer panel lattice; finite callers retain their own enumeration limits. */
#ifndef GEOMETRY_PANEL_LAYOUT_MATH_H
#define GEOMETRY_PANEL_LAYOUT_MATH_H
static Coord panel_layout_pitch(Coord panel,Coord gap) { return geo_period_pitch(panel,gap); }
static Coord panel_layout_body(Coord anchor,Coord panel,Coord gap,int64_t k)
{ return geo_period_body(anchor,panel,gap,k); }
static Coord panel_layout_center(Coord anchor,Coord panel,Coord gap,int64_t k)
{ return geo_period_center(anchor,panel,gap,k); }
static Coord panel_layout_shift(bool set,Coord delta,int64_t row)
{ return geo_alternating_shift(set,delta,row); }
#endif
