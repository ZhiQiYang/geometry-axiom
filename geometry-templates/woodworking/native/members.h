/* Woodworking member storage and face semantics, extracted from the product.
 * Placement, support, source resolution and World transactions stay with the
 * consumer. Geometry is supplied exclusively through the public K interface. */
#ifndef GEOMETRY_WOODWORKING_MEMBERS_H
#define GEOMETRY_WOODWORKING_MEMBERS_H
#include "geometry.h"

typedef enum {
    WOOD_MEMBER_FACE_A0,
    WOOD_MEMBER_FACE_A1,
    WOOD_MEMBER_FACE_B0,
    WOOD_MEMBER_FACE_B1,
    WOOD_MEMBER_FACE_START,
    WOOD_MEMBER_FACE_END,
    WOOD_MEMBER_FACE_COUNT
} WoodMemberFace;

typedef enum {
    WOOD_MEMBER_ROLE_BOUNDARY = 0,
    WOOD_MEMBER_ROLE_PRIMARY,
    WOOD_MEMBER_ROLE_SECONDARY,
    WOOD_MEMBER_ROLE_CUSTOM
} WoodMemberRole;

typedef struct {
    uint32_t id;

    GeoCoord length;
    GeoCoord size_a;
    GeoCoord size_b;

    /* Declared role and effective cut priority; custom keeps its declared N. */
    WoodMemberRole role;
    GeoCoord cut_priority;

    /* The constructor accepts auto length only. Placement derives length. */
    bool auto_length;
    bool placed;

    GeoPoint3 origin;
    GeoVector3 axis_length;
    GeoVector3 axis_a;
    GeoVector3 axis_b;
} WoodMember;

/* These are the original member constructor's checks. Admission of source
 * values, role tokens and D1 ranges remains with the existing consumer. */
bool wood_member_construct(
    uint32_t id,
    GeoCoord length,
    GeoCoord size_a,
    GeoCoord size_b,
    bool auto_length,
    WoodMemberRole role,
    GeoCoord custom_priority,
    WoodMember *out_timber
);
const char *wood_member_role_name(WoodMemberRole role);
bool wood_member_face_valid(WoodMemberFace face);
const char *wood_member_face_name(WoodMemberFace face);
const char *wood_member_face_short_name(WoodMemberFace face);
bool wood_member_face_room(
    const WoodMember *timber,
    WoodMemberFace face,
    GeoQuad3 *out_face
);
#endif
