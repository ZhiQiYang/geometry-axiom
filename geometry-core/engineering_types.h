/* D26-D28: fixed-capacity definitions, copied with the native World/history. */
#define ENG_ID_MAX 65
#define ENG_RECORD_MAX 1024
#define ENG_MATERIAL_MAX 64
#define ENG_METHOD_MAX 32
#define ENG_APPLICATION_MAX 16
#define ENG_BINDING_MAX 192
#define ENG_OPERATION_MAX 256
#define ENG_INPUT_MAX (1024u * 1024u)

typedef struct { char id[ENG_ID_MAX]; uint32_t version; } EngVersionRef;
typedef enum { ENG_LITERAL, ENG_SPEC, ENG_MATERIAL, ENG_APPLICATION } EngSourceKind;
typedef enum {
    ENG_WIDTH, ENG_LENGTH, ENG_A, ENG_B,
    ENG_U_PANEL, ENG_V_PANEL, ENG_U_GAP, ENG_V_GAP,
    ENG_BOUNDARY_A, ENG_BOUNDARY_B, ENG_PRIMARY_A, ENG_PRIMARY_B,
    ENG_SECONDARY_A, ENG_SECONDARY_B
} EngField;
typedef struct {
    int kind, field;
    Coord value;
    char ref[SPEC_NAME_MAX];
    uint32_t version;
} EngDimensionSource;
typedef struct {
    int kind; /* 0=grid, 1=timber */
    uint32_t id;
    int axis, field; /* grid: axis 0/1, field 0=panel/1=gap; timber: 0=A/1=B */
} EngTarget;
typedef struct {
    EngTarget target;
    EngDimensionSource source, override_value;
    bool has_override;
} EngBinding;
typedef struct {
    EngVersionRef ref;
    char fingerprint[65], content[ENG_RECORD_MAX];
    int kind; /* 0=panel, 1=timber */
    Coord width, length, a, b;
    bool archived;
} EngMaterialVersion;
typedef struct {
    EngVersionRef ref;
    char fingerprint[65], content[ENG_RECORD_MAX];
    EngVersionRef panel, roles[3];
    bool has_gap, archived;
    Coord gap;
    int long_axis, main_along; /* 0=unset, 1=u, 2=v */
} EngMethodVersion;
typedef struct {
    char id[ENG_ID_MAX], content[ENG_RECORD_MAX];
    uint32_t placement_id;
    EngVersionRef method;
    int long_axis, main_along;
    bool overridden[7]; /* gap then each role A/B */
    EngDimensionSource overrides[7];
    int anchor_kind[2]; /* 0=unset,1=coordinate,2=min,3=max */
    Coord anchor[2]; /* creation preference only, never an effective grid anchor */
} EngApplication;
typedef struct {
    EngMaterialVersion materials[ENG_MATERIAL_MAX]; size_t material_count;
    EngMethodVersion methods[ENG_METHOD_MAX]; size_t method_count;
    EngApplication applications[ENG_APPLICATION_MAX]; size_t application_count;
    EngBinding bindings[ENG_BINDING_MAX]; size_t binding_count;
} EngineeringState;
