#ifndef GEO_KERNEL_SOURCE_H
#define GEO_KERNEL_SOURCE_H
#include "geometry.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct GeoEvalContext GeoEvalContext;
typedef uint32_t GeoProviderToken;
/* Keys are exact bytes, not text or hashes. K copies them before evaluation. */
typedef struct { GeoProviderToken provider; const void *key; size_t key_size; } GeoSourceRef;
typedef enum {
    GEO_SOURCE_QUANTITY=0, GEO_SOURCE_AXIS_POSITION, GEO_SOURCE_FRAME,
    GEO_SOURCE_REGION_SET, GEO_SOURCE_BOX, GEO_SOURCE_FEATURE, GEO_SOURCE_DEFINITION
} GeoSourceValueKind;
typedef struct { bool has_placement; uint32_t placement; int axis; } GeoSourceContext;
typedef struct { GeoCoord coordinate; GeoSourceContext context; } GeoAxisPosition;
/* Feature keys and geometric views borrow the same candidate's storage until
 * the context is destroyed. Provider definitions and opaque source keys do not. */
typedef struct { const void *key; size_t key_size; GeoSegment3 segment; } GeoFeatureValue;
/* Schema and canonical content belong to a registered provider's candidate.
 * K retains the typed definition identity without parsing a domain schema. */
typedef struct { const char *schema; const void *content; size_t content_size; } GeoDefinitionValue;
typedef struct {
    GeoSourceValueKind kind;
    union {
        GeoQuantity quantity;
        GeoAxisPosition position;
        GeoFrame frame;
        GeoRegionSetView regions;
        GeoBox3 box;
        GeoFeatureValue feature;
        GeoDefinitionValue definition;
    } as;
} GeoSourceValue;
typedef struct {
    GeoSourceValueKind kind;
    GeoQuantityUnit unit;
    GeoSourceContext context;
    /* A policy for an evaluator whose failure has observable diagnostics.
     * Successful values always memoize. Active recursion always reports cycle. */
    bool retry_failure;
    /* AXIS_POSITION only: context depends on evaluated geometry. Description
     * remains metadata-only. A successful value supplies a valid axis 0..2;
     * K publishes that exact context and clears this flag atomically with the
     * value. Failure preserves the unresolved descriptor for a possible retry. */
    bool context_from_value;
} GeoSourceDescriptor;
typedef enum {
    GEO_SOURCE_OK=0, GEO_SOURCE_MISSING, GEO_SOURCE_FAILED, GEO_SOURCE_CYCLE,
    GEO_SOURCE_INVALID, GEO_SOURCE_MEMORY
} GeoSourceStatus;
typedef enum {
    GEO_DEPENDENCY_VALUE_REQUIRED=0, GEO_DEPENDENCY_DEFINITION_REQUIRED,
    GEO_DEPENDENCY_EVALUATE_BEFORE
} GeoDependencyKind;
typedef enum { GEO_NODE_NEW=0, GEO_NODE_ACTIVE, GEO_NODE_VALID, GEO_NODE_FAILED } GeoSourceState;
typedef struct {
    GeoProviderToken token;
    const char *name_space;
    const char *implementation_fingerprint;
    void *candidate_state;
    bool (*describe)(void *,const GeoSourceRef *,GeoSourceDescriptor *);
    bool (*evaluate)(void *,GeoEvalContext *,const GeoSourceRef *,GeoSourceValue *);
} GeoSourceProvider;
typedef struct {
    GeoSourceRef source;
    GeoSourceDescriptor descriptor;
    GeoSourceState state;
    GeoSourceStatus status;
    const GeoSourceValue *value;
    bool described;
} GeoSourceNodeView;
typedef struct { size_t consumer, source; GeoDependencyKind kind; } GeoSourceEdge;

GeoEvalContext *geo_eval_create(uint64_t candidate_id,uint64_t base_revision);
void geo_eval_destroy(GeoEvalContext *);
/* Registration closes when the first source is requested. Each token and
 * namespace must be unique; callbacks stay bound to one candidate snapshot. */
bool geo_eval_register(GeoEvalContext *,const GeoSourceProvider *);
/* A provider family is admitted atomically. Validation/allocation failure
 * leaves every existing provider and its candidate binding unchanged. */
bool geo_eval_register_many(GeoEvalContext *,const GeoSourceProvider *,size_t);
uint64_t geo_eval_candidate_id(const GeoEvalContext *);
uint64_t geo_eval_base_revision(const GeoEvalContext *);
size_t geo_eval_provider_count(const GeoEvalContext *);
const GeoSourceProvider *geo_eval_provider_at(const GeoEvalContext *,size_t);
GeoSourceStatus geo_eval_source(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
/* Records an identity dependency without evaluating it. The caller retains
 * its domain's policy for inactive values and evaluation-before failures. */
GeoSourceStatus geo_eval_depend(GeoEvalContext *,GeoSourceRef,GeoDependencyKind);
/* Obtain metadata without evaluating a value or adding an edge. A successful
 * first description leaves the node NEW. Sealed graphs permit metadata reads
 * only for already described nodes. The output is unchanged on failure. */
GeoSourceStatus geo_eval_describe(GeoEvalContext *,GeoSourceRef,GeoSourceDescriptor *);
size_t geo_eval_node_count(const GeoEvalContext *);
bool geo_eval_node_at(const GeoEvalContext *,size_t,GeoSourceNodeView *);
size_t geo_eval_edge_count(const GeoEvalContext *);
bool geo_eval_edge_at(const GeoEvalContext *,size_t,GeoSourceEdge *);
/* Sealing makes the graph and provider set immutable. Existing valid values
 * remain readable; missing/rejected values cannot trigger new evaluation. */
bool geo_eval_seal(GeoEvalContext *);
bool geo_eval_is_sealed(const GeoEvalContext *);
/* Restart a complete rebuild in the same candidate identity. No evaluation
 * may be active and a sealed graph cannot be reset. */
bool geo_eval_reset(GeoEvalContext *);
#endif
