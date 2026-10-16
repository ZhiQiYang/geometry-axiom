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
    /* H initializes the corresponding source/placement record after W has
     * admitted and constructed this member at the supplied candidate slot. */
    void (*member_created)(void *,size_t);
} WoodEngineeringOperations;
bool wood_engineering_operation(WoodEngineeringOperations *,GeoJson *,int,const char *);
bool wood_engineering_restore_member(WoodEngineeringOperations *,GeoJson *,int);
#endif
