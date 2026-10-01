/* D32/D33: bounded canonical definitions copied with native World/history. */
#ifndef GEOMETRY_ASSEMBLY_TYPES_H
#define GEOMETRY_ASSEMBLY_TYPES_H
#define ASM_NAME_MAX 97
#define ASM_ID_MAX 65
#define ASM_RULE_MAX 32
#define ASM_SLOT_MAX 8
#define ASM_MEMBER_MAX 12
#define ASM_JOINT_MAX 16
#define ASM_BINDING_MAX 64
#define ASM_RECORD_MAX 8192
#define ASM_SCHEMA "assembly-rule/1"
#define ASM_CAPABILITY "assembly-rule-authoring/1"

typedef enum { ASM_JOINT_END_TO_SIDE = 1, ASM_JOINT_ORTHO_SPLIT = 2 } AsmJointKind;
typedef enum { ASM_END_START = 1, ASM_END_FINISH = 2 } AsmEnd;
typedef enum { ASM_SIDE_POS_U = 1, ASM_SIDE_NEG_U = 2, ASM_SIDE_POS_V = 3, ASM_SIDE_NEG_V = 4 } AsmSide;
typedef enum { ASM_DIR_U = 1, ASM_DIR_V = 2 } AsmDir;
typedef enum { ASM_SRC_UNSET = 0, ASM_SRC_MATERIAL = 1, ASM_SRC_PARAMETER = 2, ASM_SRC_LITERAL = 3 } AsmSourceKind;
typedef enum { ASM_FACE_UNSET = 0, ASM_FACE_A = 1, ASM_FACE_B = 2 } AsmContactFace;
typedef enum { ASM_ORIENT_UNSET = 0, ASM_ORIENT_A = 1, ASM_ORIENT_B = 2 } AsmSectionOrient;

typedef struct { uint32_t id; char name[ASM_NAME_MAX]; } AsmSlot;
typedef struct { uint32_t id; uint32_t slot_id; } AsmMember;
typedef struct {
    uint32_t id;
    int kind;
    uint32_t members[4];
    int member_count;
    uint32_t continuous_member;
    uint32_t terminated_member;
    int term_end;
    int target_side;
    int relative_dir;
} AsmJoint;
typedef struct {
    uint32_t id, version;
    char name[ASM_NAME_MAX];
    char fingerprint[65];
    char content[ASM_RECORD_MAX];
} AsmRuleVersion;
typedef struct {
    int kind;
    char material_id[ASM_ID_MAX];
    uint32_t material_version, parameter_id, field_id;
    int64_t literal_mm;
    int contact_face, section_orient;
} AsmSlotBinding;
typedef struct {
    uint32_t id, rule_id, rule_version;
    char name[ASM_NAME_MAX], content[ASM_RECORD_MAX];
    bool complete;
} AsmBinding;
typedef struct {
    AsmRuleVersion rules[ASM_RULE_MAX];
    size_t rule_count;
    AsmBinding bindings[ASM_BINDING_MAX];
    size_t binding_count;
    bool loading;
} AssemblyState;
#endif
