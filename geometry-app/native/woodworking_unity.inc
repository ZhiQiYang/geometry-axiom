/* H composition only. W can also compile independently against K public APIs. */
#ifndef GEOMETRY_WOODWORKING_UNITY_INCLUDED
#define GEOMETRY_WOODWORKING_UNITY_INCLUDED
#ifdef GEOMETRY_WOODWORKING_EXTERNAL
#include "../../geometry-templates/woodworking/native/members.h"
#include "../../geometry-templates/woodworking/native/supports.h"
#include "../../geometry-templates/woodworking/native/contacts.h"
#include "../../geometry-templates/woodworking/native/engineering.h"
#include "../../geometry-templates/woodworking/native/panel_layout.h"
#include "../../geometry-templates/woodworking/native/panel_support.h"
#else
#include "../../geometry-templates/woodworking/native/members.c"
#include "../../geometry-templates/woodworking/native/supports.c"
#include "../../geometry-templates/woodworking/native/contacts.c"
#include "../../geometry-templates/woodworking/native/engineering.c"
#include "../../geometry-templates/woodworking/native/panel_layout.c"
#include "../../geometry-templates/woodworking/native/panel_support.c"
#endif
#endif
