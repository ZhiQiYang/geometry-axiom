/* Compatibility build entry only: standalone clients compile the .c files.
 * Do not compile them separately on a link line that includes this entry. */
#ifndef GEOMETRY_KERNEL_UNITY_INCLUDED
#define GEOMETRY_KERNEL_UNITY_INCLUDED
#ifdef GEOMETRY_KERNEL_EXTERNAL
#include "codec.h"
#include "exact.h"
#include "geometry.h"
#else
#include "codec.c"
#include "exact.c"
#include "geometry.c"
#endif
#endif
