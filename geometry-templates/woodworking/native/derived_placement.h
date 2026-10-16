/* D4/R41 woodworking reconstruction and persistent edge identity. Geometry
 * is supplied through public K, and H only reads/stages caller-owned values. */
#ifndef GEOMETRY_WOODWORKING_DERIVED_PLACEMENT_H
#define GEOMETRY_WOODWORKING_DERIVED_PLACEMENT_H
#include "finish.h"
#ifndef GEO_KERNEL_PLACEMENTS_H
#include "placements.h"
#endif

#define WOOD_DERIVED_COMPONENT_MAX GEO_PLACEMENT_COMPONENT_CAPACITY
typedef struct {
    uint32_t id,derived_fill_id;
    GeoCoord derived_h;
    GeoFrame frame;
    size_t component_count;
    WoodBoundaryRegion components[WOOD_DERIVED_COMPONENT_MAX];
} WoodDerivedValue;
typedef struct {
    void *user;
    bool (*value)(void *,const DerivedPlacement *,WoodDerivedValue *);
    bool (*height)(void *,const DerivedPlacement *,GeoCoord *);
    bool (*frame)(void *,const DerivedPlacement *,const WoodFinishLayout *,GeoFrame *);
} WoodDerivedEvaluation;
typedef struct {
    WoodFinishContext finish;
    /* Finish/fill definitions and boundary facts are validated before D4
     * reconstruction, as in the product candidate pipeline. All callbacks
     * observe the same stable candidate throughout one operation. */
    /* Read returns existence for either variant. Normal placements have
     * derived_fill_id=0; all derived fields are copied for derived values.
     * Writes stage the supplied complete value without selecting policy. */
    bool (*placement_read)(void *,uint32_t,WoodDerivedValue *);
    bool (*placement_write)(void *,const WoodDerivedValue *);
    bool (*placement_remove)(void *,uint32_t);
    size_t (*placement_count)(void *);
    size_t placement_capacity;
    void (*remove_canvas_position)(void *,uint32_t);
    const WoodDerivedEvaluation *evaluation;
} WoodDerivedContext;

const DerivedPlacement *wood_dp_find(const WoodDerivedContext *,uint32_t);
bool wood_dp_parse(const WoodDerivedContext *,GeoJson *,int,DerivedPlacement *);
bool wood_dp_operation(WoodDerivedContext *,GeoJson *,int,bool);
bool wood_dp_rebuild(WoodDerivedContext *);
bool wood_dp_value_direct(const WoodDerivedContext *,const DerivedPlacement *,WoodDerivedValue *);
bool wood_dp_height_direct(const WoodDerivedContext *,const DerivedPlacement *,GeoCoord *);
bool wood_dp_frame_direct(const WoodDerivedContext *,const WoodFinishLayout *,GeoFrame *);
bool wood_dp_edge_key(const WoodDerivedContext *,const WoodDerivedValue *,size_t,int,size_t,char *,size_t);
bool wood_dp_edge_resolve(const WoodDerivedContext *,const WoodDerivedValue *,const char *,int *,int *);
/* Atomic scene admission preserves the old codec's diagnostics: admission
 * errors return a message without changing the transient FS diagnostic kind;
 * write failure has no extra message, and rebuild failure uses finish.error. */
bool wood_dp_load(WoodDerivedContext *,uint32_t,const DerivedPlacement *,const char **);
#endif
