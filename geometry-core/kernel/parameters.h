#ifndef GEOMETRY_KERNEL_PARAMETERS_H
#define GEOMETRY_KERNEL_PARAMETERS_H
#include "geometry.h"
#include "exact.h"
#define GEO_PARAMETER_CARD_MAX 64
#define GEO_PARAMETER_FIELD_MAX 256
#define GEO_PARAMETER_FIELDS_PER_CARD 16
#define GEO_PARAMETER_NAME_MAX 97
#define GEO_PARAMETER_EXPR_MAX 2048
#define GEO_PARAMETER_NODE_MAX 128
#define GEO_PARAMETER_DEPTH_MAX 64

typedef struct GeoParameterStore GeoParameterStore;
typedef struct {bool set;uint32_t parameter_id,field_id;} GeoParameterRef;
typedef enum {GEO_PARAMETER_DIMENSION=0,GEO_PARAMETER_COUNT=1,GEO_PARAMETER_RATIO=2} GeoParameterFieldType;
typedef struct {
    uint32_t id,next_field_id;
    char name[GEO_PARAMETER_NAME_MAX];
    uint32_t fields[GEO_PARAMETER_FIELDS_PER_CARD];size_t count;
} GeoParameterCard;
typedef struct {
    uint32_t parameter_id,id;
    char name[GEO_PARAMETER_NAME_MAX];
    int type;
    char expression[GEO_PARAMETER_EXPR_MAX];
    GeoQuantity value;
} GeoParameterField;
typedef enum {
    GEO_PARAMETER_OK=0,GEO_PARAMETER_MISSING_CARD,GEO_PARAMETER_MISSING_FIELD,
    GEO_PARAMETER_NOT_DIMENSION,GEO_PARAMETER_COORDINATE,GEO_PARAMETER_AST_CAPACITY,
    GEO_PARAMETER_AST_OPERATION_MISSING,GEO_PARAMETER_AST_LITERAL,GEO_PARAMETER_INTEGER,
    GEO_PARAMETER_DENOMINATOR,GEO_PARAMETER_LITERAL_UNIT,GEO_PARAMETER_AST_REFERENCE,
    GEO_PARAMETER_UNSUPPORTED_OPERATION,GEO_PARAMETER_AST_ARITHMETIC,GEO_PARAMETER_CYCLE,
    GEO_PARAMETER_DEPTH,GEO_PARAMETER_JSON,GEO_PARAMETER_FIELD_UNIT,GEO_PARAMETER_COUNT_VALUE,
    GEO_PARAMETER_MEMORY,GEO_PARAMETER_EXACT,GEO_PARAMETER_DUPLICATE_FIELD,
    GEO_PARAMETER_REUSED_FIELD,GEO_PARAMETER_NEXT_ID,GEO_PARAMETER_CAPACITY,
    GEO_PARAMETER_INVALID_DEFINITION,GEO_PARAMETER_NAME
} GeoParameterStatus;
typedef struct {
    GeoParameterStatus status;GeoExactStatus exact;
    GeoParameterRef source;GeoQuantity quantity;
    char detail[256];
    /* Innermost-to-outermost failed field evaluations, exact identities. */
    GeoParameterRef trace[GEO_PARAMETER_DEPTH_MAX];size_t trace_count;
} GeoParameterError;

GeoParameterStore *geo_parameters_create(void);
GeoParameterStore *geo_parameters_clone(const GeoParameterStore *store);
void geo_parameters_destroy(GeoParameterStore *store);
bool geo_parameters_equal(const GeoParameterStore *a,const GeoParameterStore *b);
size_t geo_parameters_card_count(const GeoParameterStore *store);
size_t geo_parameters_field_count(const GeoParameterStore *store);
const GeoParameterCard *geo_parameters_cards(const GeoParameterStore *store);
const GeoParameterField *geo_parameters_fields(const GeoParameterStore *store);
const GeoParameterCard *geo_parameters_find(const GeoParameterStore *store,uint32_t id);
int geo_parameters_field_index(const GeoParameterStore *store,uint32_t id,uint32_t field);
bool geo_parameters_dimension_value(const GeoParameterStore *store,GeoParameterRef ref,GeoQuantity *out,GeoParameterError *error);
bool geo_parameters_coordinate(const GeoParameterStore *store,GeoParameterRef ref,GeoCoord *out,GeoParameterError *error);
bool geo_parameters_rebuild(GeoParameterStore *store,GeoParameterError *error);

/* Definition builders preserve field identities and the exhausted high-water
 * mark. No mutation occurs until put; callers keep their candidate isolated. */
void geo_parameters_begin_definition(const GeoParameterStore *store,uint32_t id,GeoParameterCard *card);
bool geo_parameters_accept_field(const GeoParameterStore *store,GeoParameterCard *card,
    const GeoParameterField *fields,size_t index,GeoParameterError *error);
bool geo_parameters_next_field(GeoParameterCard *card,uint32_t next,GeoParameterError *error);
bool geo_parameters_put(GeoParameterStore *store,const GeoParameterCard *card,
    const GeoParameterField *fields,GeoParameterError *error);
bool geo_parameters_remove(GeoParameterStore *store,uint32_t id,GeoParameterError *error);
/* Atomic-input staging only: H owns the enclosing load transaction and must
 * finish/rebuild it before publishing. The store has no loading flag. */
bool geo_parameters_stage_card(GeoParameterStore *store,const GeoParameterCard *card);
bool geo_parameters_stage_field(GeoParameterStore *store,const GeoParameterField *field);
#endif
