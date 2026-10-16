/* Existing woodworking end-contact policy. The consumer resolves geometry,
 * preserves face order and decides which eligible contact to check. */
#ifndef GEOMETRY_WOODWORKING_CONTACTS_H
#define GEOMETRY_WOODWORKING_CONTACTS_H
#include "members.h"
#include "supports.h"

/* self is the same non-null member supplied to the original placement check.
 * Acceptance leaves err unchanged; refusal preserves the existing wording,
 * truncation and optional err==NULL behavior. */
bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
);

/* self and face are non-null. The consumer has already checked coordinate,
 * full width, FREE, this member's end-extension exemption and shadowing.
 * owner is the original resolved member pointer (or NULL), not an ID copy;
 * pointer identity retains the existing self-owner exemption. The consumer
 * computes owner_extension only where the original owner branch queried it.
 * The outer contact iteration and first-error ordering remain with it. */
bool wood_member_end_contact_check(
    const WoodMember *self, const WoodStopFace *face,
    const WoodMember *owner, bool owner_extension,
    char *err, size_t err_cap
);
#endif
