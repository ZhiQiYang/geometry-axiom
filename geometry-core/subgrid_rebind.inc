/* R13/I25: evaluate references on each proposed fragment, not at stale cached
 * offsets. All source-face objects are provisionally on that fragment; the
 * selected per-object assignments are then checked together by I8/I9. */
/* -1: allocation failure; 0: invalid geometry; 1: valid candidate. */
static int reference_fragment_candidate(const World *base,SurfaceId source,SurfaceId target,
    bool timber,size_t index,GuideLine *out_guide,Timber *out_timber,TimberAnchor *out_anchor)
{
    World *candidate=malloc(sizeof *candidate);
    if (!candidate) return -1;
    *candidate=*base;
    ReferenceEval ctx={0}; ctx.world=candidate;
    for (size_t i=0;i<candidate->guide_count;++i) {
        if (candidate->guides[i].placement_id==source) candidate->guides[i].placement_id=target;
        candidate->guides[i].resolved=false;
    }
    for (size_t i=0;i<candidate->timber_count;++i) {
        if (candidate->anchors[i].placement_id==source) candidate->anchors[i].placement_id=target;
        ctx.wanted[i]=candidate->timbers[i].placed;
        candidate->timbers[i].placed=false;
    }
    bool capture=g_reference_capturing;
    size_t issues=g_reference_issue_count;
    char previous_error[sizeof g_revalidate_error]; memcpy(previous_error,g_revalidate_error,sizeof previous_error);
    g_reference_capturing=false;
    bool valid=timber?reference_eval_timber(&ctx,index):reference_eval_guide(&ctx,index);
    reference_sources_dispose(&ctx);
    g_reference_capturing=capture; g_reference_issue_count=issues;
    memcpy(g_revalidate_error,previous_error,sizeof previous_error);
    if (!valid) { free(candidate); return false; }
    if (timber) {
        *out_timber=candidate->timbers[index]; *out_anchor=candidate->anchors[index];
    } else {
        const GuideLine *g=&candidate->guides[index];
        const PlacementSurface *p=world_find_placement(candidate,target);
        SurfaceSegment2 segs[GUIDE_MAX_SEGMENTS];
        if (!p || !guide_line_get_local_segments(p,world_placement_boundary(candidate,p),g,segs,GUIDE_MAX_SEGMENTS)) { free(candidate); return false; }
        *out_guide=*g;
    }
    free(candidate);
    return true;
}
