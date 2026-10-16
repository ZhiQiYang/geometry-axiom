/* D31/I38: definitions remain POD so World snapshots own every byte. */
#define PARAM_CARD_MAX 64
#define PARAM_FIELD_MAX 256
#define PARAM_FIELDS_PER_CARD 16
#define PARAM_NAME_MAX 97
#define PARAM_EXPR_MAX 2048
#define PARAM_NODE_MAX 128
#define PARAM_DEPTH_MAX 64
#include "kernel/types.h"
typedef struct { bool set; uint32_t parameter_id, field_id; } ParameterRef;
typedef struct {
    uint32_t id, next_field_id;
    char name[PARAM_NAME_MAX];
    uint32_t fields[PARAM_FIELDS_PER_CARD];
    size_t count;
} ParameterSet;
typedef struct {
    uint32_t parameter_id, id;
    char name[PARAM_NAME_MAX];
    int type; /* 0=dimension, 1=count, 2=ratio */
    char expression[PARAM_EXPR_MAX];
    GeoQuantity value; /* deterministic cache, never a serialized definition */
} ParameterField;
typedef struct {
    ParameterSet cards[PARAM_CARD_MAX]; size_t card_count;
    ParameterField fields[PARAM_FIELD_MAX]; size_t field_count;
    bool loading; /* only native full-scene loading may stage a parameter block */
} ParameterState;
