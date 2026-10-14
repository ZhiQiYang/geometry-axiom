/* D31/I38: definitions remain POD so World snapshots own every byte. */
#define PARAM_CARD_MAX 64
#define PARAM_FIELD_MAX 256
#define PARAM_FIELDS_PER_CARD 16
#define PARAM_NAME_MAX 97
#define PARAM_EXPR_MAX 2048
#define PARAM_NODE_MAX 128
#define PARAM_DEPTH_MAX 64
#define PARAM_RETIRED_MAX 256
#define PARAM_DELETED_VALUE_MAX (PARAM_RETIRED_MAX * PARAM_FIELDS_PER_CARD + PARAM_FIELD_MAX)
typedef struct { int64_t num, den; int unit; } ParamValue;
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
    ParamValue value; /* deterministic cache, never a serialized definition */
} ParameterField;
typedef struct {
    uint32_t parameter_id, field_id;
    int type;
    ParamValue value;
} DeletedParameterValue;
typedef struct {
    ParameterSet cards[PARAM_CARD_MAX]; size_t card_count;
    ParameterField fields[PARAM_FIELD_MAX]; size_t field_count;
    /* I38/I39: card identities deleted earlier in the operation sequence that is editing this World. Candidate-owned scratch:
     * copied with the candidate, cleared when the sequence ends (batch_preview / engineering archive), never serialized. */
    uint32_t retired[PARAM_RETIRED_MAX]; size_t retired_count;
    /* P-062/P-065: last-valid values before a card or its upstream disappears.
     * Live fields may be captured, but only explicitly unbound deleted sources can consume them.
     * Both arrays and counts are cleared before comparison, staging, or history. */
    DeletedParameterValue deleted_values[PARAM_DELETED_VALUE_MAX]; size_t deleted_value_count;
    bool loading; /* only native full-scene loading may stage a parameter block */
} ParameterState;
