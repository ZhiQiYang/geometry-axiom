/* D6a/D6b/I13: persistent definitions; evaluated geometry is only a cache. */
#include "../geometry-app/native/definition_texts.h"
#include "../geometry-templates/woodworking/native/member_reference.h"
#define REF_EXPR_MAX APP_REFERENCE_TEXT_BYTES
#define SPEC_NAME_MAX 96
#define WORLD_MAX_SPECS 64
#define WORLD_MAX_DATUMS 64
/* D6c: only axis and spec expression are persistent; position is a cache. */

/* Original host wire text is distinct from K's typed linear definition. */

typedef GeoGuideSource GuideSource;
#define GUIDE_LOCAL GEO_GUIDE_LOCAL
#define GUIDE_DATUM GEO_GUIDE_DATUM

typedef GeoNamedValue SpecValue;
typedef WoodMemberReferenceFace ReferenceFace;
