/* Woodworking structural obstacle records. Each box keeps its authored
 * coordinates and optional room membership in the candidate value store. */
#ifndef GEOMETRY_WOODWORKING_OBSTACLES_H
#define GEOMETRY_WOODWORKING_OBSTACLES_H
#ifndef GEOMETRY_KERNEL_GEOMETRY_H
#include "geometry.h"
#endif

typedef struct {
    uint32_t id;
    uint32_t space_id;          /* 0 = no room membership */
    GeoCoord x_lo, x_hi, y_lo, y_hi, z_lo, z_hi;
} WoodColumn;

typedef struct {
    uint32_t id;
    uint32_t space_id;          /* 0 = no room membership */
    int axis;                   /* 0 = along x, 1 = along y */
    GeoCoord x_lo, x_hi, y_lo, y_hi, z_lo, z_hi;
} WoodBeam;

#endif
