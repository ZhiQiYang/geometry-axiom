/* Historical include API for existing codec clients. Algorithms live only in
 * the neutral kernel; production uses its public API and the host parse seam. */
#ifndef ENGINEERING_JSON_INCLUDED
#define ENGINEERING_JSON_INCLUDED
#include "kernel/codec.c"
#include "../geometry-app/native/legacy_json.inc"
#define eng_json_sorted_keys geo_json_sorted_keys
#define eng_json_free geo_json_free
#define eng_utf8_scalar geo_utf8_scalar
#define eng_json_parse_n app_json_parse_n
#define eng_json_parse app_json_parse
#define eng_json_valid_token geo_json_valid_token
#define eng_json_is_object geo_json_is_object
#define eng_json_is_array geo_json_is_array
#define eng_json_is_null geo_json_is_null
#define eng_json_size geo_json_size
#define eng_json_member geo_json_member
#define eng_json_at geo_json_at
#define eng_json_string geo_json_string
#define eng_json_integer geo_json_integer
#define eng_json_boolean geo_json_boolean
#define eng_json_csv_has geo_json_csv_has
#define eng_json_keys geo_json_keys
#define eng_json_quote geo_json_quote
#define eng_json_canonical geo_json_canonical
#define eng_sha256 geo_sha256
#define eng_base64_encode geo_base64_encode
#define eng_base64_decode geo_base64_decode
#define EngJson GeoJson
#define EngJsonToken GeoJsonToken
#define EngJsonKey GeoJsonKey
#define ENG_J_STRING GEO_J_STRING
#define ENG_JSON_MAX_DEPTH GEO_JSON_MAX_DEPTH
#define ENG_J_NULL GEO_J_NULL
#define ENG_JSON_MAX_INPUT GEO_JSON_MAX_INPUT
#define ENG_J_OBJECT GEO_J_OBJECT
#define ENG_J_INTEGER GEO_J_INTEGER
#define ENG_J_BOOL GEO_J_BOOL
#define ENG_J_ARRAY GEO_J_ARRAY
#endif
