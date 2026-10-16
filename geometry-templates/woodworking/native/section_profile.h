/* W section-profile recipes, materials and placement policy. This bounded
 * value store has no host backpointer and participates in whole-candidate
 * snapshots. Geometry predicates and frame math are provided by public K. */
#ifndef GEOMETRY_WOODWORKING_SECTION_PROFILE_H
#define GEOMETRY_WOODWORKING_SECTION_PROFILE_H
#include "engineering.h"
#include "domain_values.h"
#define SP_CAPABILITY "section-profile/1"
#define SP_NATIVE_CAPABILITY "section-profile-native/1"
#define SP_PROFILE_MAX 16
#define SP_MEMBER_MAX 128
#define SP_RUN_MAX 32
#define SP_RECORD_MAX 2048
#define SP_RUN_RECORD_MAX 8192
#define SP_ERROR_MAX 192
#define SP_OUTSIDE_MAX ((GEO_LOOP_MAX_VERTICES+1)*(GEO_LOOP_MAX_VERTICES/2+1))
#define SP_NAME_MAX 97
#define SP_PANEL_SPEC "calcium-silicate-6"
typedef struct {
    uint32_t id;
    char name[SP_NAME_MAX], content[SP_RECORD_MAX];
    WoodBoundaryLoop outline;
} SectionProfile;
typedef struct {
    uint32_t id, profile_id;
    bool panel, rotated;
    GeoCoord u0, v0, width;
    EngDimensionSource a_source, b_source;
    char content[SP_RECORD_MAX];
    /* Rebuilt caches. Never serialized as definitions. */
    GeoCoord a, b;
    GeoRect2 rect;
    bool resolved;
    char source_error[2][SP_ERROR_MAX];
    bool missing_profile, outside, range_error;
} ProfileMember;
typedef struct {
    uint32_t id, profile_id;
    EngDimensionSource length_source;
    bool placed;
    GeoFrame frame;
    /* Simple placement retains its authored host; frame is rebuilt. */
    bool simple, copied_host;
    uint32_t host_id;
    GeoFrame host_frame;
    WoodBoundaryRegion host_region;
    int dir;
    GeoCoord p,q;
    GeoVector3 up;
    char content[SP_RUN_RECORD_MAX];
    GeoCoord length;
    bool resolved;
    bool length_resolved, placement_resolved, missing_profile, range_error;
    char length_error[SP_ERROR_MAX], placement_error[SP_ERROR_MAX];
} ProfileRun;
typedef struct {
    SectionProfile profiles[SP_PROFILE_MAX]; size_t profile_count;
    ProfileMember members[SP_MEMBER_MAX]; size_t member_count;
    ProfileRun runs[SP_RUN_MAX]; size_t run_count;
} SectionProfileState;

typedef struct {const char *id,*name;GeoCoord thickness,width_max,sheet_length;} WoodSectionPanelSpec;
extern const WoodSectionPanelSpec wood_sp_panel_spec;
typedef struct {
    SectionProfileState *state;
    WoodEngineeringContext engineering;
    void *user;
    char *error;
    size_t error_capacity;
    /* The host resolves the selected parameter closure before W dimensions.
     * The same candidate owns callback facts and the context's W stores. */
    bool (*resolve_dimension)(void *,const EngDimensionSource *,const EngTarget *,GeoCoord *);
    bool (*live_host)(void *,uint32_t,GeoFrame *,WoodBoundaryRegion *,bool *derived);
} WoodSectionProfileContext;
bool wood_sp_used(const WoodSectionProfileContext *);
SectionProfile *wood_sp_profile(WoodSectionProfileContext *,uint32_t);
ProfileMember *wood_sp_member(WoodSectionProfileContext *,uint32_t);
ProfileRun *wood_sp_run(WoodSectionProfileContext *,uint32_t);
bool wood_sp_coord(GeoJson *,int,GeoCoord *);
bool wood_sp_axis(GeoJson *,int,GeoVector3 *);
bool wood_sp_host_json(WoodSectionProfileContext *,GeoJson *,int,ProfileRun *);
bool wood_sp_host(const WoodSectionProfileContext *,const ProfileRun *,GeoFrame *,WoodBoundaryRegion *);
bool wood_sp_resolve_placement(WoodSectionProfileContext *,ProfileRun *);
GeoVector3 wood_sp_scaled(GeoVector3,GeoCoord);
const char *wood_sp_axis_name(GeoVector3);
bool wood_sp_put_profile(WoodSectionProfileContext *,GeoJson *,int);
bool wood_sp_put_member(WoodSectionProfileContext *,GeoJson *,int);
bool wood_sp_put_run(WoodSectionProfileContext *,GeoJson *,int);
GeoPoint3 wood_sp_point(const ProfileRun *,GeoCoord,GeoCoord,GeoCoord);
size_t wood_sp_outside_regions(const WoodBoundaryLoop *,const GeoRect2 *,GeoRect2 out[SP_OUTSIDE_MAX]);
bool wood_sp_intersection(const ProfileMember *,const ProfileMember *,GeoRect2 *);
bool wood_sp_rebuild(WoodSectionProfileContext *,char *,size_t);
bool wood_sp_remove(WoodSectionProfileContext *,const char *,uint32_t);
bool wood_sp_begin_conversion(WoodSectionProfileContext *,uint32_t,bool,ProfileRun *);
bool wood_sp_conversion_fields(WoodSectionProfileContext *,const ProfileRun *,const GeoFrame *,const WoodBoundaryRegion *,int *,GeoCoord *,GeoCoord *,GeoVector3 *);
#endif
