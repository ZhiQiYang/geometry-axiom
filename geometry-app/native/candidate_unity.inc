/* H composition; isolated product clients link this implementation once. */
#ifndef GEO_APP_CANDIDATE_UNITY_INCLUDED
#define GEO_APP_CANDIDATE_UNITY_INCLUDED
#ifdef GEOMETRY_HOST_CANDIDATE_EXTERNAL
#include "app_candidate.h"
#else
#include "app_candidate.c"
#endif
#endif
