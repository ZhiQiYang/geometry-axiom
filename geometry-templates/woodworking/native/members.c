#include "members.h"

/* Local axes are length, A, B; A0 is the contact face. K owns the walk. */
static const struct {
    unsigned char axis;
    unsigned char side;
} WOOD_MEMBER_FACE_SPEC[WOOD_MEMBER_FACE_COUNT] = {
    [WOOD_MEMBER_FACE_A0]    = { 2, 0 },
    [WOOD_MEMBER_FACE_A1]    = { 2, 1 },
    [WOOD_MEMBER_FACE_B0]    = { 1, 0 },
    [WOOD_MEMBER_FACE_B1]    = { 1, 1 },
    [WOOD_MEMBER_FACE_START] = { 0, 0 },
    [WOOD_MEMBER_FACE_END]   = { 0, 1 }
};

static const struct {
    const char *full;
    const char *brief;
} WOOD_MEMBER_FACE_NAMES[WOOD_MEMBER_FACE_COUNT] = {
    [WOOD_MEMBER_FACE_A0]    = { "A0（接觸面）",     "A0"    },
    [WOOD_MEMBER_FACE_A1]    = { "A1（另一個 A 面）", "A1"    },
    [WOOD_MEMBER_FACE_B0]    = { "B0",              "B0"    },
    [WOOD_MEMBER_FACE_B1]    = { "B1",              "B1"    },
    [WOOD_MEMBER_FACE_START] = { "START 端面",       "START" },
    [WOOD_MEMBER_FACE_END]   = { "END 端面",         "END"   }
};

bool wood_member_face_valid(WoodMemberFace face)
{
    return face >= WOOD_MEMBER_FACE_A0 && face < WOOD_MEMBER_FACE_COUNT;
}

const char *wood_member_face_name(WoodMemberFace face)
{
    return wood_member_face_valid(face)
        ? WOOD_MEMBER_FACE_NAMES[face].full
        : "UNKNOWN_FACE";
}

const char *wood_member_face_short_name(WoodMemberFace face)
{
    return wood_member_face_valid(face)
        ? WOOD_MEMBER_FACE_NAMES[face].brief
        : "?";
}

const char *wood_member_role_name(WoodMemberRole role)
{
    switch (role) {
        case WOOD_MEMBER_ROLE_BOUNDARY:  return "boundary";
        case WOOD_MEMBER_ROLE_PRIMARY:   return "primary";
        case WOOD_MEMBER_ROLE_SECONDARY: return "secondary";
        case WOOD_MEMBER_ROLE_CUSTOM:    return "custom";
        default:                    return "?";
    }
}

bool wood_member_construct(
    uint32_t id,
    GeoCoord length,
    GeoCoord size_a,
    GeoCoord size_b,
    bool auto_length,
    WoodMemberRole role,
    GeoCoord custom_priority,
    WoodMember *out_timber
)
{
    if (out_timber == NULL ||
        size_a <= 0 ||
        size_b <= 0 ||
        !auto_length ||
        (auto_length && length != 0) ||
        (role == WOOD_MEMBER_ROLE_CUSTOM && custom_priority < 1)) {
        return false;
    }

    *out_timber = (WoodMember){
        .id = id,
        .length = length,
        .size_a = size_a,
        .size_b = size_b,
        .auto_length = auto_length,
        .placed = false,
        .role = role,
        .cut_priority = role == WOOD_MEMBER_ROLE_CUSTOM
            ? custom_priority
            : (GeoCoord)role + 1,

        /* 尚未放置前，先使用標準局部框架。 */
        .origin = { 0, 0, 0 },
        .axis_length = { 1, 0, 0 },
        .axis_a = { 0, 1, 0 },
        .axis_b = { 0, 0, 1 }
    };

    return true;
}

bool wood_member_face_room(
    const WoodMember *timber,
    WoodMemberFace face,
    GeoQuad3 *out_face
)
{
    if(!timber||!out_face||!timber->placed||!wood_member_face_valid(face))return false;
    GeoBox3 box={{timber->origin,timber->axis_length,timber->axis_a,timber->axis_b},{timber->length,timber->size_a,timber->size_b}};
    return geo_box_face(&box,WOOD_MEMBER_FACE_SPEC[face].axis,WOOD_MEMBER_FACE_SPEC[face].side,out_face);
}
