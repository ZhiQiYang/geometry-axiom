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
    bool (*rebuild_parameters)(void *,char *,size_t);
    /* Optional unbind preparation on a local copy of the stored binding. The
     * host may evaluate only that binding's current source closure and may
     * replace an explicitly ended source with its last valid value. The stored
     * binding is never rewritten by this callback. */
    bool (*unbind_sources)(void *,EngBinding *,char *,size_t);
    /* Optional notification after an explicit set-source (0) or
     * set-override (1). The host orders reference redeclarations. */
    bool (*source_declared)(void *,const EngTarget *,int);
    /* H initializes the corresponding source/placement record after W has
     * admitted and constructed this member at the supplied candidate slot. */
    void (*member_created)(void *,size_t);
} WoodEngineeringOperations;
bool wood_engineering_operation(WoodEngineeringOperations *,GeoJson *,int,const char *);
bool wood_engineering_restore_member(WoodEngineeringOperations *,GeoJson *,int);
#endif
