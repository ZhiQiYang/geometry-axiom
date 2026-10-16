/* Compatibility build entry only: standalone clients compile the .c files.
 * Do not compile them separately on a link line that includes this entry. */
#ifndef GEOMETRY_KERNEL_UNITY_INCLUDED
#define GEOMETRY_KERNEL_UNITY_INCLUDED
#ifdef GEOMETRY_KERNEL_EXTERNAL
#include "codec.h"
#include "exact.h"
#include "geometry.h"
#include "grid.h"
#include "parameters.h"
#include "linear.h"
#include "named_values.h"
#include "datums.h"
#include "source.h"
#include "regions.h"
#else
#include "codec.c"
#include "exact.c"
#include "geometry.c"
#include "grid.c"
#include "parameters.c"
#include "linear.c"
#include "named_values.c"
#include "datums.c"
#include "source.c"
#include "regions.c"
#endif
#endif
