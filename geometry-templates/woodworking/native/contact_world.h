/* Ordered contact policy over same-candidate geometry and member facts. */
#ifndef GEOMETRY_WOODWORKING_CONTACT_WORLD_H
#define GEOMETRY_WOODWORKING_CONTACT_WORLD_H
#include "contacts.h"
#include "domain_values.h"
#define WOOD_CONTACT_COMPONENT_CAPACITY 8
#define WOOD_CONTACT_MEMBER_CAPACITY 64
#define WOOD_CONTACT_FACE_CAPACITY (WOOD_CONTACT_COMPONENT_CAPACITY*GEO_LOOP_MAX_VERTICES*(GEO_REGION_MAX_HOLES+1)+WOOD_CONTACT_MEMBER_CAPACITY*2)
typedef struct {
    const WoodMember *member; /* Identity is the original candidate pointer. */
    uint32_t placement_id;
    uint64_t order;
    bool along_v,footprint_valid;
    GeoRect2 footprint;
} WoodContactMemberFact;
typedef struct {
    uint32_t placement_id;
    const WoodBoundaryRegion *regions[WOOD_CONTACT_COMPONENT_CAPACITY];
    size_t region_count;
    /* The caller-selected effective component used by the original role
     * derivation; stop collection separately visits every component. */
    const WoodBoundaryRegion *role_boundary;
    const WoodContactMemberFact *members;
    size_t member_count;
} WoodContactWorld;
typedef enum {
    WOOD_BOUNDARY_END_ORDINARY,
    WOOD_BOUNDARY_END_PARTIAL,
    WOOD_BOUNDARY_END_BARE_RC
} WoodBoundaryEndAdmission;
/* I19 exception three is W policy. A PARTIAL endpoint still requires all
 * caller footprint, boundary-role and collision validation. BARE_RC is an
 * explicit refusal and must never fall back to complete-face admission.
 * An optional required_contact points into faces: a between selector may
 * claim partial support only if that named returned face itself contacts. */
bool wood_contact_boundary_end_uses_member_facts(const WoodMember *);
WoodBoundaryEndAdmission wood_contact_boundary_end_admission(
    const WoodContactWorld *,const WoodMember *,bool,
    GeoCoord,GeoCoord,GeoCoord,GeoCoord,int,const WoodStopFace *,size_t,const WoodStopFace *);
/* Common R6(d/e) decision for a collector that must retain independent
 * failures. H can report the result without duplicating W admission policy. */
bool wood_contact_end_support_check(WoodBoundaryEndAdmission,size_t,bool,char *,size_t);
size_t wood_contact_collect_stops(const WoodContactWorld *,bool,const WoodMember *,WoodStopFace *,size_t);
/* Positioning edge of a footprint (D16/R18): pure geometry. The interval on the length axis comes from the
 * footprint alone and never from how the member was placed (at-face, at or through give the same fixed
 * segment for the same footprint); the dump keeps references and placement order (R4) but not the method.
 * Only the outer loop counts: hole edges are column stop faces without extension semantics (I20/I21). */
/* The positioning edge of a footprint: its interval on the length axis and its outline edge id ("e<i>",
 * index into the outer loop of the role boundary). out_edge may be NULL; no output is written when no
 * positioning edge is found. wood_contact_boundary_interval is the same without the id. */
bool wood_contact_boundary_edge(const WoodBoundaryRegion *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,GeoCoord *,GeoCoord *,int *);
bool wood_contact_boundary_interval(const WoodBoundaryRegion *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,GeoCoord *,GeoCoord *);
/* True when the contact range [lo,hi] (on the owner's length axis) lies on the owner's extension part (I22:
 * an extension side counts as priority 2 when used as a stop). Only a boundary member located by an outline
 * edge has a fixed part and an extension part; every other owner returns false. */
bool wood_contact_owner_extension(const WoodContactWorld *,const WoodMember *,GeoCoord,GeoCoord);
bool wood_contact_end_faces(const WoodContactWorld *,const WoodMember *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,char *,size_t);
/* The optional resolver runs at the original collection point, after span
 * extension checks. A rejected source is not treated as an empty face list. */
typedef bool (*WoodContactStopResolver)(void *,bool,const WoodMember *,WoodStopFace *,size_t,size_t *);
bool wood_contact_end_faces_with_sources(const WoodContactWorld *,const WoodMember *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,
    WoodContactStopResolver,void *,char *,size_t);
#endif
