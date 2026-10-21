/* Woodworking grid applications, role preferences and child-cell policy.
 * K owns the reusable source/rule/binding definitions and exact arithmetic.
 * Contexts bind all reads/writes to one candidate; before is explicit. */
#ifndef GEOMETRY_WOODWORKING_GRID_APPLICATION_H
#define GEOMETRY_WOODWORKING_GRID_APPLICATION_H
#ifndef GEO_KERNEL_GRID_STORE_H
#include "grid_store.h"
#endif
#ifndef GEO_KERNEL_PLACEMENTS_H
#include "placements.h"
#endif
#include "domain_values.h"
#include "engineering.h"
#define WOOD_GRID_MAX 16
#define WOOD_GRID_MAX_LINES GEO_GRID_COORDINATE_CAPACITY
#define WOOD_GRID_CELL_MIN (-1)
#define WOOD_GRID_CELL_MAX (-2)
typedef struct {
    uint32_t id, placement_id;
    bool from_system, from_binding;
    uint32_t binding_id;
    GeoCoord lattice_base[2], lattice_step[2];
    int64_t lattice_index[2];
    bool lattice_cell;
    int64_t lattice_cell_index[2];
    uint32_t system_id;
    GeoCoord system_origin[2];
    GeoGridAxisDef axis[2];
    int main_along;
    bool is_subgrid;
    uint32_t parent_id;
    int cell_ref[2][2];
    unsigned divisions[2];
} WoodGridApplication;
typedef struct { uint32_t source_id; int main_along; } WoodGridSourceRole;
typedef struct {
    WoodGridApplication items[WOOD_GRID_MAX];
    size_t count;
    WoodGridSourceRole roles[GEO_GRID_SYSTEM_CAPACITY];
    size_t role_count;
} WoodGridState;
typedef struct {
    uint32_t id, boundary_id;
    GeoRect2 bounds;
    bool bounds_valid;
    WoodBoundaryRegion components[GEO_PLACEMENT_COMPONENT_CAPACITY];
    size_t component_count;
} WoodGridHost;
typedef enum { WOOD_GRID_REFERENCE_GUIDE, WOOD_GRID_REFERENCE_TIMBER } WoodGridReferenceKind;
typedef struct {
    WoodGridReferenceKind kind;
    uint32_t id;
    bool active, is_rule;
    uint32_t grid_id;
    GeoGridRuleLineRef rule;
    const char *expression; /* H text fact; lifetime covers the W call. */
} WoodGridReference;
typedef struct WoodGridContext WoodGridContext;
typedef struct WoodGridRuleTarget WoodGridRuleTarget;
typedef struct {
    void *user;
    bool (*system)(void *,uint32_t,char *,size_t);
    bool (*binding)(void *,const GeoGridBinding *,WoodGridApplication *,char *,size_t);
    bool (*application)(void *,WoodGridApplication *,char *,size_t);
    bool (*dimension)(void *,const WoodGridApplication *,int,int,GeoCoord *,char *,size_t);
    bool (*rule_line)(void *,const GeoGridRuleLineRef *,uint32_t,GeoCoord *,GeoRect2 *,char *,size_t);
    bool (*rule_cell)(void *,uint32_t,uint32_t,const int64_t[2],WoodGridRuleTarget *,char *,size_t);
    const GeoGridRule *(*rule_definition)(void *,const GeoGridSystem *,uint32_t,char *,size_t);
    bool (*world_valid)(void *,const WoodGridContext *,char *,size_t);
    bool (*rules_valid)(void *,const WoodGridContext *,char *,size_t);
} WoodGridEvaluation;
struct WoodGridContext {
    WoodGridState *state;
    GeoGridStore *sources;
    WoodEngineeringContext engineering;
    void *user;
    bool (*host)(void *,uint32_t,WoodGridHost *);
    GeoGridCoordinateResolver coordinate;
    GeoGridVertexResolver vertex;
    bool (*reference)(void *,size_t,WoodGridReference *);
    const char *parameter_error;
    const WoodGridContext *before;
    const WoodGridEvaluation *evaluation;
};
const WoodGridApplication *wood_grid_find(const WoodGridState *,uint32_t);
WoodGridApplication *wood_grid_find_mut(WoodGridState *,uint32_t);
bool wood_grid_stage(WoodGridState *,const WoodGridApplication *);
int wood_grid_source_main_along(const WoodGridState *,uint32_t);
bool wood_grid_source_main_valid(const GeoGridSystem *,int);
bool wood_grid_source_put(WoodGridContext *,const GeoGridSystem *,int);
bool wood_grid_source_redeclare(WoodGridContext *,const GeoGridSystem *,int,GeoGridStoreError *);
bool wood_grid_source_remove(WoodGridContext *,uint32_t);
bool wood_grid_begin_direct(const WoodGridContext *,uint32_t,uint32_t,WoodGridApplication *,char *,size_t);
bool wood_grid_direct_declared(const WoodGridContext *,const WoodGridApplication *,int,bool,char *,size_t);
bool wood_grid_direct_check(const WoodGridContext *,const WoodGridApplication *,char *,size_t);
bool wood_grid_apply_system(WoodGridContext *,const WoodGridApplication *,char *,size_t);
bool wood_grid_apply_binding(WoodGridContext *,const WoodGridApplication *,char *,size_t);
bool wood_grid_prepare_child(const WoodGridContext *,WoodGridApplication *,bool,unsigned,unsigned,char *,size_t);
bool wood_grid_child_check(const WoodGridContext *,const WoodGridApplication *,char *,size_t);
bool wood_grid_systems_rebuild(WoodGridContext *,char *,size_t);
/* D64/I74 card-reference diagnostics for a K grid store status. Returns false
 * without writing when the status is not a card-reference status. The system
 * supplies the card's parameter and field ids; parameter_error the source cause. */
bool wood_grid_card_error(const GeoGridSystem *system,const GeoGridStoreError *detail,
    const char *parameter_error,char *error,size_t cap);
bool wood_grid_system_evaluate_direct(WoodGridContext *,uint32_t,char *,size_t);
bool wood_grid_binding_cache(const WoodGridContext *,const GeoGridBinding *,WoodGridApplication *,char *,size_t);
bool wood_grid_binding_cache_direct(const WoodGridContext *,const GeoGridBinding *,WoodGridApplication *,char *,size_t);
bool wood_grid_application_evaluate_direct(WoodGridContext *,WoodGridApplication *,char *,size_t);
bool wood_grid_application_dimension_direct(const WoodGridContext *,const WoodGridApplication *,int,int,GeoCoord *,char *,size_t);
bool wood_grid_bindings_rebuild(WoodGridContext *,char *,size_t);
bool wood_grid_delete(WoodGridContext *,const char *,uint32_t,char *,size_t);
bool wood_grid_rule_used(const WoodGridContext *,uint32_t,uint32_t);
bool wood_grid_rules_world_valid(const WoodGridContext *,char *,size_t);
bool wood_grid_rules_world_valid_direct(const WoodGridContext *,char *,size_t);
bool wood_grid_rule_change_allowed(const WoodGridContext *,uint32_t,uint32_t,const GeoGridRule *,bool,char *,size_t);
bool wood_grid_rules_valid(const GeoGridSystem *,char *,size_t);
struct WoodGridRuleTarget {
    WoodGridApplication derived;
    const GeoGridSystem *source;
    const GeoGridRule *rule;
    GeoRect2 bounds;
    uint32_t placement_id,boundary_id;
    bool has_placement,has_boundary;
};
bool wood_grid_rule_target(const WoodGridContext *,const char *,uint32_t,WoodGridRuleTarget *,char *,size_t);
bool wood_grid_rule_cell(const WoodGridContext *,const char *,uint32_t,uint32_t,const int64_t[2],WoodGridRuleTarget *,char *,size_t);
bool wood_grid_rule_cell_direct(const WoodGridContext *,const char *,uint32_t,uint32_t,const int64_t[2],WoodGridRuleTarget *,char *,size_t);
bool wood_grid_rule_edit_begin(const WoodGridContext *,uint32_t,uint32_t,bool,bool,bool,uint32_t *,char *,size_t);
bool wood_grid_rule_edit(WoodGridContext *,uint32_t,const GeoGridRule *,bool,bool,bool,char *,size_t);
bool wood_grid_rule_line(const WoodGridContext *,const GeoGridRuleLineRef *,uint32_t,GeoCoord *,GeoRect2 *,char *,size_t);
bool wood_grid_rule_line_direct(const WoodGridContext *,const GeoGridRuleLineRef *,uint32_t,GeoCoord *,GeoRect2 *,char *,size_t);
bool wood_grid_axis_lines(const WoodGridApplication *,const WoodGridHost *,int,GeoCoord[WOOD_GRID_MAX_LINES],size_t *,char *,size_t);
bool wood_grid_valid(const WoodGridApplication *,const WoodGridHost *);
bool wood_grid_cell_bounds(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,GeoRect2 *,char *,size_t);
typedef bool (*WoodGridCellResolver)(void *,const WoodGridApplication *,const WoodGridHost *,GeoRect2 *,char *,size_t);
bool wood_grid_axis_lines_in(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,int,GeoCoord[WOOD_GRID_MAX_LINES],size_t *,char *,size_t);
bool wood_grid_line_coord_in(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,int,int64_t,GeoCoord *,size_t *,char *,size_t);
bool wood_grid_anchor_line_coord(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,int,int64_t,bool,int64_t,GeoCoord *,char *,size_t);
/* Optional cell resolution runs exactly where the direct algorithm consumes
 * child-cell bounds, after its original axis/band guards. */
bool wood_grid_line_coord_in_resolved(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,int,int64_t,GeoCoord *,size_t *,char *,size_t,WoodGridCellResolver,void *);
bool wood_grid_anchor_line_coord_resolved(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,int,int64_t,bool,int64_t,GeoCoord *,char *,size_t,WoodGridCellResolver,void *);
bool wood_grid_valid_in(const WoodGridApplication *,size_t,const WoodGridApplication *,const WoodGridHost *,char *,size_t);
bool wood_grid_parent_count_valid(const WoodGridContext *,const WoodGridApplication *,const WoodGridHost *,char *,size_t);
bool wood_grid_world_valid(const WoodGridContext *,char *,size_t);
bool wood_grid_world_valid_direct(const WoodGridContext *,char *,size_t);
bool wood_grid_family_fits(const WoodGridContext *,const WoodGridApplication *,const WoodGridHost *);
bool wood_grid_lattice_coord(const WoodGridApplication *,int,int64_t,GeoCoord *);
bool wood_grid_lattice_coord_band(const WoodGridApplication *,int,int64_t,int64_t,GeoCoord *);
bool wood_grid_bind_engineering(WoodGridContext *,GeoJson *,int,uint32_t,const EngApplication *,const EngMethodVersion *);
bool wood_grid_restore_engineering(WoodGridContext *,GeoJson *,int);
bool wood_grid_dimension_read(WoodEngineeringContext *,GeoJson *,int,const EngTarget *,GeoCoord *);
#endif
