/* Q38 native slice: definitions are POD and belong to World/history. */
#ifndef GEOMETRY_SECTION_PROFILE_TYPES_H
#define GEOMETRY_SECTION_PROFILE_TYPES_H
#define SP_CAPABILITY "section-profile/1"
#define SP_NATIVE_CAPABILITY "section-profile-native/1"
#define SP_PROFILE_MAX 16
#define SP_MEMBER_MAX 128
#define SP_RUN_MAX 32
#define SP_RECORD_MAX 2048
#define SP_NAME_MAX 97
#define SP_PANEL_SPEC "calcium-silicate-6"
typedef struct {
    uint32_t id;
    char name[SP_NAME_MAX], content[SP_RECORD_MAX];
    PolygonLoop2 outline;
} SectionProfile;
typedef struct {
    uint32_t id, profile_id;
    bool panel, rotated;
    Coord u0, v0, width;
    EngDimensionSource a_source, b_source;
    char content[SP_RECORD_MAX];
    /* Rebuilt caches. Never serialized as definitions. */
    Coord a, b;
    SurfaceRegion2 rect;
    bool resolved;
} ProfileMember;
typedef struct {
    uint32_t id, profile_id;
    EngDimensionSource length_source;
    bool placed;
    SurfaceFrame frame;
    char content[SP_RECORD_MAX];
    Coord length;
    bool resolved;
} ProfileRun;
typedef struct {
    SectionProfile profiles[SP_PROFILE_MAX]; size_t profile_count;
    ProfileMember members[SP_MEMBER_MAX]; size_t member_count;
    ProfileRun runs[SP_RUN_MAX]; size_t run_count;
} SectionProfileState;
#endif
