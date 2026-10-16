/* D6a/D6b/I13: persistent definitions; evaluated geometry is only a cache. */
#define REF_EXPR_MAX 1536
#define SPEC_NAME_MAX 96
#define WORLD_MAX_SPECS 64
#define WORLD_MAX_DATUMS 64
/* D6c: only axis and spec expression are persistent; position is a cache. */
typedef struct { uint32_t id; int axis; char expression[REF_EXPR_MAX]; } AppDatumInput;
/* Original host wire text is distinct from K's typed linear definition. */
typedef struct { uint32_t id; char expression[REF_EXPR_MAX]; } AppDatumText;
typedef GeoGuideSource GuideSource;
#define GUIDE_LOCAL GEO_GUIDE_LOCAL
#define GUIDE_DATUM GEO_GUIDE_DATUM
typedef struct { uint32_t id; char expression[REF_EXPR_MAX]; } AppGuideText;
typedef GeoNamedValue SpecValue;
typedef struct { int kind, hole, edge; TimberId timber; char key[512]; } ReferenceFace;
