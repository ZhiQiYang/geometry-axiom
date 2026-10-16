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
    GEO_SOURCE_REGION_SET, GEO_SOURCE_BOX, GEO_SOURCE_FEATURE
} GeoSourceValueKind;
typedef struct { bool has_placement; uint32_t placement; int axis; } GeoSourceContext;
typedef struct { GeoCoord coordinate; GeoSourceContext context; } GeoAxisPosition;
/* Feature keys and geometric views borrow the same candidate's storage until
 * the context is destroyed. Provider definitions and opaque source keys do not. */
typedef struct { const void *key; size_t key_size; GeoSegment3 segment; } GeoFeatureValue;
typedef struct {
    GeoSourceValueKind kind;
    union {
        GeoQuantity quantity;
        GeoAxisPosition position;
        GeoFrame frame;
        GeoRegionSetView regions;
        GeoBox3 box;
        GeoFeatureValue feature;
    } as;
} GeoSourceValue;
typedef struct {
    GeoSourceValueKind kind;
    GeoQuantityUnit unit;
    GeoSourceContext context;
    /* A policy for an evaluator whose failure has observable diagnostics.
     * Successful values always memoize. Active recursion always reports cycle. */
    bool retry_failure;
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
} GeoSourceNodeView;
typedef struct { size_t consumer, source; GeoDependencyKind kind; } GeoSourceEdge;

GeoEvalContext *geo_eval_create(uint64_t candidate_id,uint64_t base_revision);
void geo_eval_destroy(GeoEvalContext *);
/* Registration closes when the first source is requested. Each token and
 * namespace must be unique; callbacks stay bound to one candidate snapshot. */
bool geo_eval_register(GeoEvalContext *,const GeoSourceProvider *);
uint64_t geo_eval_candidate_id(const GeoEvalContext *);
uint64_t geo_eval_base_revision(const GeoEvalContext *);
size_t geo_eval_provider_count(const GeoEvalContext *);
const GeoSourceProvider *geo_eval_provider_at(const GeoEvalContext *,size_t);
GeoSourceStatus geo_eval_source(GeoEvalContext *,GeoSourceRef,GeoDependencyKind,GeoSourceValue *);
/* Records an identity dependency without evaluating it. The caller retains
 * its domain's policy for inactive values and evaluation-before failures. */
GeoSourceStatus geo_eval_depend(GeoEvalContext *,GeoSourceRef,GeoDependencyKind);
size_t geo_eval_node_count(const GeoEvalContext *);
bool geo_eval_node_at(const GeoEvalContext *,size_t,GeoSourceNodeView *);
size_t geo_eval_edge_count(const GeoEvalContext *);
bool geo_eval_edge_at(const GeoEvalContext *,size_t,GeoSourceEdge *);
#endif
