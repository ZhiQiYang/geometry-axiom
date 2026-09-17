/* D6a/D6b/I13: persistent definitions; evaluated geometry is only a cache. */
#define REF_EXPR_MAX 512
#define SPEC_NAME_MAX 96
#define WORLD_MAX_SPECS 64
typedef struct { char name[SPEC_NAME_MAX]; Coord value; } SpecValue;
typedef struct { int kind, hole, edge; TimberId timber; } ReferenceFace;
