/* Original spelling is application data, separate from the core's typed
 * definitions. Dumps and legacy edit fields retain these exact source bytes. */
#ifndef GEOMETRY_APP_DEFINITION_TEXTS_H
#define GEOMETRY_APP_DEFINITION_TEXTS_H
#include <stdint.h>
#define APP_REFERENCE_TEXT_BYTES 1536
typedef struct {uint32_t id;int axis;char expression[APP_REFERENCE_TEXT_BYTES];} AppDatumInput;
typedef struct {uint32_t id;char expression[APP_REFERENCE_TEXT_BYTES];} AppDatumText;
typedef struct {uint32_t id;char expression[APP_REFERENCE_TEXT_BYTES];} AppGuideText;
#endif
