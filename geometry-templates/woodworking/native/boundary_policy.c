#include "boundary_policy.h"
void wood_boundary_default_fixity(WoodEdgeFixity *fixity,size_t count)
{
    for(size_t i=0;i<count;++i)fixity[i]=WOOD_EDGE_FIXED;
}
