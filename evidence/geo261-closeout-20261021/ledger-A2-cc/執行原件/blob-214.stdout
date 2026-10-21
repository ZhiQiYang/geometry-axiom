/* Strict integer JSON, canonical UTF-8, hashes and base64. No domain policy.
 * Parsed documents own tokens/decoded strings; text is borrowed until free.
 * Traversal tokens and sorted keys are read-only views. The caller frees the
 * allocated sorted-key array. Parsing initializes even a failed document;
 * always call geo_json_free after a parse attempt. */
#ifndef GEOMETRY_KERNEL_CODEC_H
#define GEOMETRY_KERNEL_CODEC_H
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
#define GEO_JSON_MAX_INPUT (1024u * 1024u)
#define GEO_JSON_MAX_DEPTH 128
enum { GEO_J_OBJECT=1, GEO_J_ARRAY, GEO_J_STRING, GEO_J_INTEGER, GEO_J_BOOL, GEO_J_NULL };
typedef struct {
    int type, size, next;
    char *string;
    int64_t number;
} GeoJsonToken;
typedef struct {
    const char *text;
    GeoJsonToken *tokens;
    int count;
    char error[192];
} GeoJson;
typedef struct { const char *key; int token; } GeoJsonKey;

GeoJsonKey *geo_json_sorted_keys(const GeoJson *j,int token);
void geo_json_free(GeoJson *j);
size_t geo_utf8_scalar(const unsigned char *s, size_t n);
int geo_json_parse_n(GeoJson *j, const char *text, size_t length);
int geo_json_parse(GeoJson *j, const char *text);
int geo_json_valid_token(const GeoJson *j,int token);
int geo_json_is_object(const GeoJson *j,int token);
int geo_json_is_array(const GeoJson *j,int token);
int geo_json_is_null(const GeoJson *j,int token);
int geo_json_size(const GeoJson *j,int token);
int geo_json_member(const GeoJson *j,int token,const char *key);
int geo_json_at(const GeoJson *j,int token,int index);
int geo_json_string(const GeoJson *j,int token,char *out,size_t capacity);
int geo_json_integer(const GeoJson *j,int token,int64_t *out);
int geo_json_boolean(const GeoJson *j,int token,int *out);
int geo_json_csv_has(const char *csv,const char *key);
int geo_json_keys(GeoJson *j,int token,const char *required,const char *optional);
int geo_json_quote(const char *text,char *out,size_t capacity);
int geo_json_canonical(const GeoJson *j,int token,char *out,size_t capacity);
void geo_sha256(const void *data,size_t length,char out[65]);
int geo_base64_encode(const void *data,size_t length,char *out,size_t capacity,size_t *out_length);
int geo_base64_decode(const char *data,size_t length,void *out,size_t capacity,size_t *out_length);
bool geo_utf8_name_valid(const unsigned char *name,size_t length,size_t maximum);
#endif
