/* Exact coordinate sequences. Definitions own indices; query windows never
 * change their identity. No placement, material, role or persistence types. */
#ifndef GEOMETRY_KERNEL_GRID_H
#define GEOMETRY_KERNEL_GRID_H
#include "geometry.h"

typedef enum {
    GEO_GRID_OK=0, GEO_GRID_INVALID, GEO_GRID_INDEX_RANGE,
    GEO_GRID_CAPACITY, GEO_GRID_NO_SOURCE, GEO_GRID_SOURCE_UNSUPPORTED,
    GEO_GRID_BODY_GAP_INVALID, GEO_GRID_ORDER, GEO_GRID_BOUNDS,
    GEO_GRID_NOT_DIVISIBLE
} GeoGridStatus;
/* A bounded input anchor plus body and half-gap may put the derived base
 * outside the output coordinate domain. Such a base is valid: other signed
 * indices can still lie inside the domain. Derived bases allow +/-3*limit. */
typedef struct {GeoCoord base,pitch;int64_t index;} GeoLattice;
typedef struct {int64_t index;GeoCoord coordinate;} GeoLatticeLine;
typedef struct {
    bool defined;int64_t first,last;uint64_t total,stride;
    size_t count;GeoLatticeLine *lines;size_t capacity;
} GeoLatticeWindow;
typedef enum {GEO_SEQUENCE_NONE=0,GEO_SEQUENCE_EXPLICIT,GEO_SEQUENCE_SERIES,GEO_SEQUENCE_BODY_GAP} GeoSequenceKind;
typedef struct {
    GeoSequenceKind kind;const GeoCoord *coordinates;size_t count;
    GeoCoord start,step,body,gap,anchor;
} GeoFiniteSequence;

bool geo_i64_add(int64_t a,int64_t b,int64_t *out);
/* Divisor must be positive. */
int64_t geo_floor_div(int64_t a,int64_t b);
int64_t geo_ceil_div(int64_t a,int64_t b);
/* Formula helpers require representable intermediate values. Callers first
 * validate their definition and use lattice evaluation for arbitrary indices. */
GeoCoord geo_period_pitch(GeoCoord body,GeoCoord gap);
GeoCoord geo_period_body(GeoCoord anchor,GeoCoord body,GeoCoord gap,int64_t k);
GeoCoord geo_period_center(GeoCoord anchor,GeoCoord body,GeoCoord gap,int64_t k);
GeoCoord geo_alternating_shift(bool set,GeoCoord delta,int64_t band);
bool geo_lattice_coord(const GeoLattice *lattice,int64_t k,GeoCoord *out);
GeoGridStatus geo_lattice_window(const GeoLattice *lattice,GeoCoord lo,GeoCoord hi,
    size_t limit,bool sample,GeoLatticeWindow *out);
bool geo_coordinates_increasing(const GeoCoord *coordinates,size_t count);
/* Definition dimensions/start/anchor are bounded coordinates, body positive,
 * gap nonnegative. The caller retains the meaning of omitted sources. */
GeoGridStatus geo_finite_sequence(const GeoFiniteSequence *definition,GeoCoord lo,GeoCoord hi,
    GeoCoord *coordinates,size_t capacity,size_t *count);
GeoGridStatus geo_interval_subdivide(GeoCoord lo,GeoCoord hi,unsigned divisions,
    GeoCoord *coordinates,size_t capacity,size_t *count);
#endif
