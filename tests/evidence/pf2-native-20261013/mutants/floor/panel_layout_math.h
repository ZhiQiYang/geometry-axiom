/* D10a/D10b/D29/D43: shared integer panel lattice; finite callers retain their own enumeration limits. */
#ifndef GEOMETRY_PANEL_LAYOUT_MATH_H
#define GEOMETRY_PANEL_LAYOUT_MATH_H
static Coord panel_layout_pitch(Coord panel,Coord gap) { return panel+gap; }
static Coord panel_layout_body(Coord anchor,Coord panel,Coord gap,int64_t k)
{ return anchor+k*panel_layout_pitch(panel,gap); }
static Coord panel_layout_center(Coord anchor,Coord panel,Coord gap,int64_t k)
{ return panel_layout_body(anchor,panel,gap,k)+panel+gap; }
static Coord panel_layout_shift(bool set,Coord delta,int64_t row)
{ return set&&(row&1)?delta:0; }
#endif
