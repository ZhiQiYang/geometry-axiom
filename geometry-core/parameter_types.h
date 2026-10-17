/* H compatibility names for the shared K parameter model. */
#ifndef GEOMETRY_PARAMETER_TYPES_H
#define GEOMETRY_PARAMETER_TYPES_H
#include "kernel/parameters.h"
#define PARAM_CARD_MAX GEO_PARAMETER_CARD_MAX
#define PARAM_FIELD_MAX GEO_PARAMETER_FIELD_MAX
#define PARAM_FIELDS_PER_CARD GEO_PARAMETER_FIELDS_PER_CARD
#define PARAM_NAME_MAX GEO_PARAMETER_NAME_MAX
#define PARAM_EXPR_MAX GEO_PARAMETER_EXPR_MAX
#define PARAM_NODE_MAX GEO_PARAMETER_NODE_MAX
#define PARAM_DEPTH_MAX GEO_PARAMETER_DEPTH_MAX
#define PARAM_DECLARATION_MAX 512
#define PARAM_FIELD_RETIREMENT_MAX (PARAM_FIELD_MAX * PARAM_FIELDS_PER_CARD)
#define PARAM_DELETED_VALUE_MAX (PARAM_FIELD_RETIREMENT_MAX + PARAM_FIELD_MAX)
typedef GeoParameterRef ParameterRef;
typedef GeoParameterCard ParameterSet;
typedef GeoParameterField ParameterField;
typedef struct {
    uint32_t parameter_id, field_id;
    unsigned generation;
    int type;
    GeoQuantity value;
} DeletedParameterValue;

/* Candidate ordering, never incarnation marks or serialized identities. */
typedef struct { uint32_t parameter_id, field_id; unsigned at; } ParameterFieldRetirement;
typedef struct { int kind; uint32_t id; int slot; unsigned at; } ParameterDeclaration;
enum { PARAM_OWNER_CARD, PARAM_OWNER_ENG_GRID, PARAM_OWNER_ENG_TIMBER,
       PARAM_OWNER_ASSEMBLY, PARAM_OWNER_MEMBER, PARAM_OWNER_RUN,
       PARAM_OWNER_GUIDE, PARAM_OWNER_DATUM, PARAM_OWNER_GRID_SYSTEM, PARAM_OWNER_GRID,
       PARAM_OWNER_PANEL_FILL };
/* P-062/P-065/P-121: H-owned scratch for exactly one tracked candidate
 * evaluation (the bridge batch transaction or one interactive archive record).
 * It is allocated beside the candidate, never inside World, a K store, a seal,
 * history or an exchange format. Last-valid values before a card or its
 * upstream disappears may be captured, but only explicitly unbound deleted
 * sources can consume them. `world` is the candidate snapshot it belongs to. */
typedef struct {
    const void *world;
    DeletedParameterValue deleted_values[PARAM_DELETED_VALUE_MAX]; size_t deleted_value_count;
    ParameterFieldRetirement field_retirements[PARAM_FIELD_RETIREMENT_MAX]; size_t field_retirement_count;
    ParameterDeclaration declarations[PARAM_DECLARATION_MAX]; size_t declaration_count;
    unsigned candidate_order;
} ParameterCandidateLedger;
#endif
