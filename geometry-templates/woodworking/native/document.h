/* Inline woodworking document state. All fields belong to the woodworking
 * template; neutral geometry stores and application metadata are separate.
 * The aggregate retains every bounded slot, cache and inactive field so a
 * candidate snapshot can copy the complete value without reconstruction. */
#ifndef GEOMETRY_WOODWORKING_DOCUMENT_H
#define GEOMETRY_WOODWORKING_DOCUMENT_H
#include "boundary_policy.h"
#include "grid_application.h"
#include "members.h"
#include "member_placement.h"
#include "obstacles.h"
#include "section_profile.h"
#include "assembly.h"
#include "engineering.h"
#include "finish.h"

enum {
    WOOD_DOCUMENT_BOUNDARY_CAPACITY = 16,
    WOOD_DOCUMENT_PLACEMENT_CAPACITY = 16,
    WOOD_MEMBER_CAPACITY = 64,
    WOOD_OBSTACLE_CAPACITY = 32
};

typedef struct {
    WoodBoundaryPolicy boundary_policy[WOOD_DOCUMENT_BOUNDARY_CAPACITY];
    WoodPlacementPolicy placement_policy[WOOD_DOCUMENT_PLACEMENT_CAPACITY];
    WoodGridState grid_applications;

    WoodMember timbers[WOOD_MEMBER_CAPACITY];
    WoodMemberPlacement anchors[WOOD_MEMBER_CAPACITY];
    size_t timber_count;

    WoodColumn columns[WOOD_OBSTACLE_CAPACITY];
    size_t column_count;

    WoodBeam beams[WOOD_OBSTACLE_CAPACITY];
    size_t beam_count;

    SectionProfileState section_profiles;
    AssemblyState assembly;
    EngineeringState engineering;
    FinishSurfaceState finish_surfaces;
} WoodDocument;

#endif
