#ifndef GEO_KERNEL_GUIDES_INTERNAL_H
#define GEO_KERNEL_GUIDES_INTERNAL_H
#include "../guides.h"
struct GeoGuideStore { GeoGuide values[GEO_GUIDE_CAPACITY]; size_t count; };
#endif
