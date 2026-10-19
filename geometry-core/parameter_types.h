/* D31/I38: definitions remain POD so World snapshots own every byte. */
#define PARAM_CARD_MAX 64
#define PARAM_FIELD_MAX 256
#define PARAM_FIELDS_PER_CARD 16
#define PARAM_NAME_MAX 97
#define PARAM_EXPR_MAX 2048
#define PARAM_NODE_MAX 128
#define PARAM_DEPTH_MAX 64
#define PARAM_DECLARATION_MAX 512
#define PARAM_FIELD_RETIREMENT_MAX (PARAM_FIELD_MAX * PARAM_FIELDS_PER_CARD)
#define PARAM_DELETED_VALUE_MAX (PARAM_FIELD_RETIREMENT_MAX + PARAM_FIELD_MAX)
typedef struct { int64_t num, den; int unit; } ParamValue;
typedef struct { bool set; uint32_t parameter_id, field_id; } ParameterRef;
#define GRID_CARD_CAPABILITY "grid-card-reference/1"
typedef struct { bool set; uint32_t parameter_id, fields[2]; } GridCardReference;
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
    unsigned generation;
    int type;
    ParamValue value;
} DeletedParameterValue;

/* Candidate ordering, never incarnation marks or serialized identities. */
typedef struct { uint32_t parameter_id, field_id; unsigned at; } ParameterFieldRetirement;
typedef struct { int kind; uint32_t id; int slot; unsigned at; } ParameterDeclaration;
typedef struct { uint32_t id, parameter_id, fields[2]; Coord values[2]; unsigned at; } GridCardCapture;
enum { PARAM_OWNER_CARD, PARAM_OWNER_ENG_GRID, PARAM_OWNER_ENG_TIMBER,
       PARAM_OWNER_ASSEMBLY, PARAM_OWNER_MEMBER, PARAM_OWNER_RUN,
       PARAM_OWNER_GUIDE, PARAM_OWNER_DATUM, PARAM_OWNER_GRID_SYSTEM, PARAM_OWNER_GRID,
       PARAM_OWNER_PANEL_FILL, PARAM_OWNER_GRID_CARD };
typedef struct {
    ParameterSet cards[PARAM_CARD_MAX]; size_t card_count;
    ParameterField fields[PARAM_FIELD_MAX]; size_t field_count;
    /* P-062/P-065: last-valid values before a card or its upstream disappears.
     * Live fields may be captured, but only explicitly unbound deleted sources can consume them.
     * Both arrays and counts are cleared before comparison, staging, or history. */
    DeletedParameterValue deleted_values[PARAM_DELETED_VALUE_MAX]; size_t deleted_value_count;
    ParameterFieldRetirement field_retirements[PARAM_FIELD_RETIREMENT_MAX]; size_t field_retirement_count;
    ParameterDeclaration declarations[PARAM_DECLARATION_MAX]; size_t declaration_count;
    GridCardCapture card_captures[256]; size_t card_capture_count;
    unsigned candidate_order; bool tracking;
    bool loading; /* only native full-scene loading may stage a parameter block */
} ParameterState;
