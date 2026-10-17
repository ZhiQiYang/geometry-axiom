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
typedef GeoParameterRef ParameterRef;
typedef GeoParameterCard ParameterSet;
typedef GeoParameterField ParameterField;
#endif
