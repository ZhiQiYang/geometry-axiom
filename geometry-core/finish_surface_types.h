/* PF-1 (D41 / I52 / I55 / I56): finish surfaces are POD definitions owned by World/history.
 * Layout is padding-free so world_definitions_equal (memcmp) stays deterministic. */
#ifndef GEOMETRY_FINISH_SURFACE_TYPES_H
#define GEOMETRY_FINISH_SURFACE_TYPES_H
#define FS_CAPABILITY "panel-fill/1"
#define FS_NATIVE_CAPABILITY "panel-fill-native/1"
#define FS_MAX 16
#define FS_OBSTACLE_MAX 64
#define FS_NAME_MAX 96
enum { FS_OBSTACLE_COLUMN = 0, FS_OBSTACLE_BEAM = 1 };
typedef struct {
    uint32_t kind;          /* FS_OBSTACLE_COLUMN (c<id>) or FS_OBSTACLE_BEAM (b<id>) */
    uint32_t id;
} FinishObstacleRef;
typedef struct {
    SurfaceFrame frame;     /* D2: origin O and unit integer axes U, V, N (I1) */
    uint32_t id, boundary_id;
    int32_t side;           /* s in {-1,+1}; structure side n = s*N */
    uint32_t obstacle_count;
    FinishObstacleRef obstacles[FS_OBSTACLE_MAX]; /* R41 source order: columns by id, then beams by id */
    char name[FS_NAME_MAX + 8]; /* not identity; NUL-terminated UTF-8, at most FS_NAME_MAX bytes */
} FinishSurface;
typedef struct {
    uint32_t id, finish_id;
    EngVersionRef panel;
    int32_t length_axis, stagger_axis; /* 0=u,1=v; stagger -1 means straight */
    Coord origin[2], gap, stagger;
    ParameterRef gap_ref, stagger_ref, threshold;
    char definition[1024]; /* canonical D42 definition, never derived geometry */
} PanelFill;
typedef struct {
    uint32_t id, fill_id;
    EngDimensionSource h;
    char definition[1024]; /* D4 sources only; no frame, outline, holes or fixity. */
} DerivedPlacement;
typedef struct {
    FinishSurface items[FS_MAX];
    uint64_t count;
    PanelFill fills[FS_MAX];
    uint64_t fill_count;
    DerivedPlacement hosts[FS_MAX];
    uint64_t host_count;
} FinishSurfaceState;
#endif
