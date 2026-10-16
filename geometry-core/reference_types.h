/* D6a/D6b/I13: persistent definitions; evaluated geometry is only a cache. */
#define REF_EXPR_MAX 1536
#define SPEC_NAME_MAX 96
#define WORLD_MAX_SPECS 64
#define WORLD_MAX_DATUMS 64
/* D6c: only axis and spec expression are persistent; position is a cache. */
typedef struct { uint32_t id; int axis; char expression[REF_EXPR_MAX]; Coord position; } DatumPlane;
typedef enum { GUIDE_LOCAL = 0, GUIDE_DATUM = 1 } GuideSource;
typedef GeoNamedValue SpecValue;
typedef struct { int kind, hole, edge; TimberId timber; char key[512]; } ReferenceFace;
