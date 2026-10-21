/* Host-only compatibility wording for the existing JSON command surfaces. */
#ifndef GEOMETRY_APP_LEGACY_JSON_INCLUDED
#define GEOMETRY_APP_LEGACY_JSON_INCLUDED
#include "../../geometry-core/kernel/codec.h"
#include <stdio.h>
#include <string.h>
static int app_json_parse_n(GeoJson *json,const char *text,size_t length)
{
    int ok=geo_json_parse_n(json,text,length);
    if(!ok&&!strcmp(json->error,"NUL is not allowed in JSON"))
        snprintf(json->error,sizeof json->error,"NUL is not allowed in engineering JSON");
    return ok;
}
static int app_json_parse(GeoJson *json,const char *text)
{return app_json_parse_n(json,text,text?strlen(text):0);}
#endif
