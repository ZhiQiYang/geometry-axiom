#include "contacts.h"
#include <stdio.h>

bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
)
{
    if (has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&
        (span_lo < edge_lo || span_hi > edge_hi)) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_EXTENSION：非 boundary 角材（%u）的 "
                     "footprint 超出定位邊範圍", (unsigned)self->id);
        }
        return false;
    }
    return true;
}

bool wood_member_end_contact_check(
    const WoodMember *self, const WoodStopFace *f,
    const WoodMember *owner, bool owner_extension,
    char *err, size_t err_cap
)
{
    if (f->kind == WOOD_STOP_OUTLINE_EDGE) {
        if (self->role != WOOD_MEMBER_ROLE_BOUNDARY) {
            if (err != NULL) {
                snprintf(err, err_cap,
                         "V_CUT_PRIORITY：角材 %u 端面頂到"
                         "外輪廓邊（RC）——那條邊還沒鋪邊界材；"
                         "只有 boundary 可頂 RC",
                         (unsigned)self->id);
            }
            return false;
        }
        return true;
    }

    if (f->kind == WOOD_STOP_MEMBER_SIDE) {
        GeoCoord owner_prio;

        if (owner == NULL || owner == self) {
            return true;
        }

        if (self->role == WOOD_MEMBER_ROLE_BOUNDARY &&
            owner->role == WOOD_MEMBER_ROLE_BOUNDARY) {
            return true;
        }

        owner_prio = owner->cut_priority;
        if (owner_extension) {
            owner_prio = 2;
        }

        if (owner_prio >= self->cut_priority) {
            if (err != NULL) {
                snprintf(err, err_cap,
                         "V_CUT_PRIORITY：角材 %u（優先級 %d）"
                         "端面頂到角材 %u（優先級 %d）側面——"
                         "擋面擁有者優先級必須嚴格小於自己",
                         (unsigned)self->id, (int)self->cut_priority,
                         (unsigned)owner->id, (int)owner_prio);
            }
            return false;
        }
    }
    return true;
}
