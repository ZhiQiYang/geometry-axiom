#include "contacts.h"
#include <stdio.h>

/* I22 (W): a non-boundary member must stay inside its locating edge. The refusal keeps the
 * original wording as an exact prefix and then names the locating edge ("e<edge_index>" and its
 * interval on the length axis) and each exceeded interval: the low end [span_lo,edge_lo] and/or
 * the high end [edge_hi,span_hi], all in mm. Capacity, truncation and err==NULL behave as before. */
bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge, int edge_index,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
)
{
    if (has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&
        (span_lo < edge_lo || span_hi > edge_hi)) {
        if (err != NULL) {
            char low_note[64] = "", high_note[64] = "";
            if (edge_lo > span_lo) {
                snprintf(low_note, sizeof low_note, "，低端超出 [%lld,%lld] mm",
                         (long long)span_lo, (long long)edge_lo);
            }
            if (edge_hi < span_hi) {
                snprintf(high_note, sizeof high_note, "，高端超出 [%lld,%lld] mm",
                         (long long)edge_hi, (long long)span_hi);
            }
            snprintf(err, err_cap,
                     "V_EXTENSION：非 boundary 角材（%u）的 "
                     "footprint 超出定位邊範圍"
                     "——定位邊 e%d [%lld,%lld] mm%s%s",
                     (unsigned)self->id, edge_index,
                     (long long)edge_lo, (long long)edge_hi, low_note, high_note);
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
