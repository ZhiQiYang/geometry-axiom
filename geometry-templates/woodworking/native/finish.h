/* Woodworking finish/fill/derived authored state and finish/panel policy.
 * Geometry queries use public K; H supplies same-candidate source facts. */
#ifndef GEOMETRY_WOODWORKING_FINISH_H
#define GEOMETRY_WOODWORKING_FINISH_H
#include "engineering.h"
#include "domain_values.h"
#include "panel_layout.h"
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
    GeoFrame frame;     /* D2: origin O and unit integer axes U, V, N (I1) */
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
    GeoCoord origin[2], gap, stagger;
    GeoParameterRef gap_ref, stagger_ref, threshold;
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

typedef enum { FS_DIAGNOSTIC_INVALID, FS_DIAGNOSTIC_CAPACITY } FsDiagnosticKind;
enum { FS_SEPARATE = 0, FS_TOUCH = 1, FS_INTERIOR = 2 };
typedef struct {GeoCoord rect[4],q[2];int relation;} FsObstacleView;
typedef struct {
    WoodPanelLayout layout;GeoCoord t;const FinishSurface *finish;GeoFrame frame;
    const PanelFill *fill; /* Authoritative definition used by this evaluation. */
    FsObstacleView obstacles[FS_OBSTACLE_MAX];bool cuts[FS_OBSTACLE_MAX];bool keep_collinear;
} WoodFinishLayout;
enum { WOOD_PF_LENGTH,WOOD_PF_WIDTH,WOOD_PF_THICKNESS,WOOD_PF_GAP,WOOD_PF_STAGGER,WOOD_PF_THRESHOLD };
typedef struct {
    void *user;
    bool (*check)(void *,const FinishSurface *);
    bool (*values)(void *,const PanelFill *,WoodFinishLayout *);
    bool (*field)(void *,const PanelFill *,int,GeoQuantity *);
    bool (*finish_definition)(void *,uint32_t,const FinishSurface **);
    bool (*boundary)(void *,uint32_t,WoodBoundaryRegion *);
    bool (*obstacle_box)(void *,const FinishObstacleRef *,GeoCoord[3],GeoCoord[3]);
} WoodFinishEvaluation;
/* All callbacks read facts from the very same candidate as state/engineering.
 * The H codec owns resource diagnostics; policy and authored values live in W. */
typedef struct {
    FinishSurfaceState *state;
    WoodEngineeringContext engineering;
    void *user;
    char *error;size_t error_capacity;
    FsDiagnosticKind *diagnostic;
    bool (*boundary)(void *,uint32_t,WoodBoundaryRegion *);
    bool (*obstacle_box)(void *,const FinishObstacleRef *,GeoCoord[3],GeoCoord[3]);
    bool (*parameter_coord)(void *,GeoParameterRef,GeoCoord *);
    bool (*parameter_value)(void *,GeoParameterRef,GeoQuantity *);
    char *parameter_error;size_t parameter_error_capacity;
    bool (*engineering_operation)(void *,GeoJson *,int);
    bool (*derived_operation)(void *,GeoJson *,int,bool);
    const WoodFinishEvaluation *evaluation;
} WoodFinishContext;
bool wood_fs_error(const WoodFinishContext *,const char *,...);
bool wood_fs_capacity_error(const WoodFinishContext *,const char *,...);
bool wood_fs_name_check(const WoodFinishContext *,const unsigned char *,size_t);
bool wood_fs_used(const WoodFinishContext *);
int wood_fs_index(const WoodFinishContext *,uint32_t);
const FinishSurface *wood_fs_find(const WoodFinishContext *,uint32_t);
void wood_fs_obstacle_text(const FinishObstacleRef *,char[16]);
bool wood_fs_obstacle_parse(const char *,FinishObstacleRef *);
int wood_fs_obstacle_compare(const void *,const void *);
bool wood_fs_obstacles_normalize(const WoodFinishContext *,FinishSurface *);
const char *wood_fs_relation_name(int);
int wood_fs_relation(const WoodBoundaryRegion *,const GeoCoord[4]);
bool wood_fs_obstacle_view(const WoodFinishContext *,const FinishSurface *,const FinishObstacleRef *,FsObstacleView *);
bool wood_fs_check(const WoodFinishContext *,const FinishSurface *);
bool wood_fs_check_direct(const WoodFinishContext *,const FinishSurface *);
bool wood_fs_boundary(const WoodFinishContext *,uint32_t,WoodBoundaryRegion *);
bool wood_fs_obstacle_box(const WoodFinishContext *,const FinishObstacleRef *,GeoCoord[3],GeoCoord[3]);
/* Revalidate finish definitions; H runs fill/derived phases immediately after. */
bool wood_fs_rebuild(WoodFinishContext *,char *,size_t);
uint32_t wood_fs_reference_owner(const WoodFinishContext *,const char *,uint32_t);
bool wood_fs_from_json(const WoodFinishContext *,GeoJson *,int,FinishSurface *);
bool wood_fs_put(WoodFinishContext *,GeoJson *,int);
bool wood_fs_delete(WoodFinishContext *,uint32_t);
bool wood_fs_operation(WoodFinishContext *,GeoJson *,int);
bool wood_fs_load(WoodFinishContext *,FinishSurface *,const char **);
const PanelFill *wood_pf_find(const WoodFinishContext *,uint32_t);
void wood_pf_free(WoodFinishLayout *);
bool wood_pf_parse(const WoodFinishContext *,GeoJson *,int,PanelFill *);
bool wood_pf_values(const WoodFinishContext *,const PanelFill *,WoodFinishLayout *);
bool wood_pf_values_direct(const WoodFinishContext *,const PanelFill *,WoodFinishLayout *);
bool wood_pf_field_direct(const WoodFinishContext *,const PanelFill *,int,GeoQuantity *);
GeoRegionView wood_pf_region_view(const WoodBoundaryRegion *,GeoLoop2View *);
size_t wood_pf_selected_cuts(const WoodFinishLayout *,GeoRect2 *);
int wood_pf_point_order(GeoPoint2,GeoPoint2);
bool wood_pf_clip_status(const WoodFinishContext *,GeoClipStatus);
bool wood_pf_clip(const WoodFinishContext *,WoodFinishLayout *,WoodPanelTile *);
bool wood_pf_build(const WoodFinishContext *,const PanelFill *,WoodFinishLayout *);
bool wood_pf_rebuild(const WoodFinishContext *);
bool wood_pf_operation(WoodFinishContext *,GeoJson *,int,bool);
bool wood_pf_load(WoodFinishContext *,uint32_t,const PanelFill *);
#endif
