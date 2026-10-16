#ifndef WOOD_ENGINEERING_SOURCES_H
#define WOOD_ENGINEERING_SOURCES_H
#include "engineering.h"
#ifndef GEO_KERNEL_SOURCE_H
#include "source.h"
#endif
typedef struct WoodEngineeringSources WoodEngineeringSources;
typedef struct {
    GeoProviderToken dimension,binding,definition,named,parameter;
} WoodEngineeringSourceTokens;
/* The context and its stores borrow the same isolated candidate as evaluation.
 * Destroy this binding before releasing that candidate; K owns copied keys. */
WoodEngineeringSources *wood_engineering_sources_register(GeoEvalContext *,const WoodEngineeringContext *,WoodEngineeringSourceTokens);
void wood_engineering_sources_destroy(WoodEngineeringSources *);
void wood_engineering_sources_bind(WoodEngineeringSources *,WoodEngineeringContext *);
const EngineeringState *wood_engineering_sources_state(const WoodEngineeringSources *);
GeoEvalContext *wood_engineering_sources_context(const WoodEngineeringSources *);
#endif
