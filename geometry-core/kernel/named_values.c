#include "internal/named_values.h"
#include "geometry.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

GeoNamedValues *geo_named_values_create(void){return calloc(1,sizeof(GeoNamedValues));}
GeoNamedValues *geo_named_values_clone(const GeoNamedValues *source)
{if(!source)return NULL;GeoNamedValues *copy=malloc(sizeof *copy);if(copy)*copy=*source;return copy;}
void geo_named_values_destroy(GeoNamedValues *store){free(store);}
size_t geo_named_values_count(const GeoNamedValues *store){return store?store->count:0;}
const GeoNamedValue *geo_named_values_at(const GeoNamedValues *store,size_t at)
{return store&&at<store->count?&store->values[at]:NULL;}
const GeoNamedValue *geo_named_values_find(const GeoNamedValues *store,const char *name)
{if(!store||!name)return NULL;for(size_t i=0;i<store->count;++i)if(!strcmp(store->values[i].name,name))return &store->values[i];return NULL;}
bool geo_named_value_name_valid(const char *name)
{
    if(!name||!*name||strlen(name)>=GEO_NAMED_VALUE_NAME_BYTES)return false;
    for(const unsigned char *p=(const unsigned char *)name;*p;++p)
        if(*p<128&&!(isalnum(*p)||*p=='_'))return false;
    return true;
}
bool geo_named_values_put(GeoNamedValues *store,const char *name,GeoCoord value)
{
    if(!store||!geo_named_value_name_valid(name)||!geo_coord_in_range(value))return false;
    size_t at=0;while(at<store->count&&strcmp(store->values[at].name,name))++at;
    if(at>=GEO_NAMED_VALUE_CAPACITY)return false;
    /* Name may be borrowed from this store. Snapshot before clearing. */
    GeoNamedValue next={0};memcpy(next.name,name,strlen(name)+1);next.value=value;
    store->values[at]=next;if(at==store->count)++store->count;return true;
}
bool geo_named_values_remove(GeoNamedValues *store,const char *name)
{
    if(!store||!name)return false;size_t at=0;while(at<store->count&&strcmp(store->values[at].name,name))++at;
    if(at==store->count)return false;
    memmove(store->values+at,store->values+at+1,(store->count-at-1)*sizeof *store->values);
    memset(&store->values[--store->count],0,sizeof *store->values);return true;
}
