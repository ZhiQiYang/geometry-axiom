/* K-private storage. The H aggregate includes this during the POD transition;
 * template code consumes only the const public views and mutation operations. */
#ifndef GEOMETRY_KERNEL_PARAMETER_STORE_H
#define GEOMETRY_KERNEL_PARAMETER_STORE_H
#include "../parameters.h"
struct GeoParameterStore {
    GeoParameterCard cards[GEO_PARAMETER_CARD_MAX];size_t card_count;
    GeoParameterField fields[GEO_PARAMETER_FIELD_MAX];size_t field_count;
};
#endif
