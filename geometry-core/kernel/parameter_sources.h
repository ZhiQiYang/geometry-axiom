#ifndef GEOMETRY_KERNEL_PARAMETER_SOURCES_H
#define GEOMETRY_KERNEL_PARAMETER_SOURCES_H
#include "parameters.h"
#include "source.h"

/* The composition root assigns the registry identity. Keys are exactly two
 * uint32_t values: card id then field id. The store and resolver must outlive
 * this binding; the binding must outlive every evaluation using its provider. */
typedef struct GeoParameterSources GeoParameterSources;
GeoParameterSources *geo_parameter_sources_register(GeoEvalContext *,GeoParameterStore *,
    GeoProviderToken,const char *name_space,const char *implementation_fingerprint);
/* Full registration retains the compatible quantity provider/key and adds
 * core.parameter.definition atomically. Every quantity consumes its returned
 * field definition through the original parameter evaluator. Quantity
 * descriptions freeze authored metadata and use the same canonical record's
 * unit, without evaluating a source value. Authored store bytes stay unchanged;
 * only successful quantity caches are written back. */
GeoParameterSources *geo_parameter_sources_register_with_definitions(GeoEvalContext *,GeoParameterStore *,
    GeoProviderToken value_token,GeoProviderToken definition_token,
    const char *value_namespace,const char *value_implementation_fingerprint);

typedef enum {
    GEO_PARAMETER_DEFINITION_CARD=1,GEO_PARAMETER_DEFINITION_FIELD=2
} GeoParameterDefinitionKind;
typedef struct {unsigned char bytes[12];} GeoParameterDefinitionKey;
/* Three BE32 fields: kind, card id, field id. A card key reserves field=0.
 * Identifiers and exhausted next_field_id may be zero. Failed decodes leave
 * every output unchanged; the quantity key remains two native uint32_t. */
GeoSourceRef geo_parameter_definition_source_ref(GeoProviderToken,GeoParameterDefinitionKind,
    uint32_t card_id,uint32_t field_id,GeoParameterDefinitionKey *);
bool geo_parameter_definition_source_decode(const GeoSourceRef *,GeoParameterDefinitionKind *,
    uint32_t *card_id,uint32_t *field_id);

#define GEO_PARAMETER_CARD_CONTENT_MAX (16+GEO_PARAMETER_NAME_MAX-1+4*GEO_PARAMETER_FIELDS_PER_CARD)
#define GEO_PARAMETER_FIELD_CONTENT_MAX (21+GEO_PARAMETER_NAME_MAX-1+GEO_PARAMETER_EXPR_MAX-1)
/* geometry.parameter-card/1: BE32 id, next_field_id, name byte length, name,
 * field count, then each ordered field id. No inactive array bytes/padding.
 * geometry.parameter-field/1: BE32 card, field, type, name byte length, name,
 * one canonical-JSON flag, BE32 expression byte length, complete expression.
 * Valid JSON uses K's canonical JSON; an unparseable expression retains its
 * exact input with flag=0 so rejected input keeps the original diagnostics.
 * These codecs do not evaluate the AST or read another field. Decode clears
 * the derived field value. Encode/decode leave outputs unchanged on failure. */
size_t geo_parameter_card_definition_encode(const GeoParameterCard *,void *,size_t);
bool geo_parameter_card_definition_decode(const void *,size_t,GeoParameterCard *);
size_t geo_parameter_field_definition_encode(const GeoParameterField *,void *,size_t);
bool geo_parameter_field_definition_decode(const void *,size_t,GeoParameterField *);
/* Enumerate all stored card/field metadata, including unused and empty cards.
 * No quantity is requested and no evaluation cache is changed. Full mode only.
 * After geo_eval_reset, destroy this generation's handle and register anew. */
bool geo_parameter_sources_definitions(GeoParameterSources *,GeoParameterError *);
void geo_parameter_sources_destroy(GeoParameterSources *);
const GeoParameterStore *geo_parameter_sources_store(const GeoParameterSources *);
const GeoEvalContext *geo_parameter_sources_context(const GeoParameterSources *);
bool geo_parameter_sources_rebuild(GeoParameterSources *,GeoParameterError *);
bool geo_parameter_sources_value(GeoParameterSources *,GeoParameterRef,GeoQuantity *,GeoParameterError *);
#endif
