/* Host-owned whole-document snapshot layout. Inline K storage preserves the
 * existing value-copy history/preview semantics while stores migrate into K.
 * This file is private to the host aggregate, never a template dependency. */
#ifndef GEOMETRY_APP_KERNEL_STORAGE_H
#define GEOMETRY_APP_KERNEL_STORAGE_H
#include "../../geometry-core/kernel/internal/parameter_store.h"
#include "../../geometry-core/kernel/internal/named_values.h"
#include "../../geometry-core/kernel/internal/datums.h"
#include "../../geometry-core/kernel/internal/regions.h"
#include "../../geometry-core/kernel/internal/guides.h"
#include "../../geometry-core/kernel/internal/grid_store.h"
#include "../../geometry-core/kernel/internal/placements.h"
/* Legacy bridge/impact metadata: a rect supplied beside `on boundary` is
 * inactive geometry, but the historical wire response still exposes it. */
typedef struct { GeoRect2 unused_rect; } AppPlacementMetadata;
#endif
