/* H composition; separate clients link history.c directly. */
#ifdef GEOMETRY_HOST_HISTORY_EXTERNAL
#include "history.h"
#else
#include "history.c"
#endif
