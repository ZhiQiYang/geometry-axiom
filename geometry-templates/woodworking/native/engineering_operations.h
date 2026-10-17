/* Ordered editing policy over one caller-owned woodworking candidate. */
#ifndef GEOMETRY_WOODWORKING_ENGINEERING_OPERATIONS_H
#define GEOMETRY_WOODWORKING_ENGINEERING_OPERATIONS_H
#include "grid_application.h"
#include "members.h"
typedef struct {
    WoodGridContext grids;
    WoodMember *members;
    size_t *member_count, member_capacity;
    void *user;
    /* I38/R33/P-065: before unbind, H/K resolves exactly the parameter sources of
     * this local binding copy (live sources in their current closure; a source
     * deleted earlier in this candidate as its last valid value). Unrelated
     * fields are not evaluated. The stored binding is not touched here. */
    bool (*unbind_sources)(void *,const EngTarget *,EngBinding *,char *,size_t);
    /* P-121/P-129: an explicit source/override edit declares this owner slot
     * (0 source, 1 override) in the candidate's ordering. */
    bool (*declare_source)(void *,const EngTarget *,int);
    /* H initializes the corresponding source/placement record after W has
     * admitted and constructed this member at the supplied candidate slot. */
    void (*member_created)(void *,size_t);
} WoodEngineeringOperations;
bool wood_engineering_operation(WoodEngineeringOperations *,GeoJson *,int,const char *);
bool wood_engineering_restore_member(WoodEngineeringOperations *,GeoJson *,int);
#endif
