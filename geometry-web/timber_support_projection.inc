/* #47 F4a: read projection only. Include after core and bridge JSON helpers.
 * R6/R21/D11 remain the relationship authority; this never rebuilds a World. */
static const AsmInstance *schedule_support_owner(const World *w,uint32_t timber,uint32_t *member)
{
    const AsmInstance *found=NULL; size_t hits=0;
    for(size_t i=0;i<w->assembly.instance_count;++i)
        for(int m=0;m<3;++m) if(w->assembly.instances[i].timber[m]==timber) {
            found=&w->assembly.instances[i]; *member=found->member[m]; ++hits;
        }
    if(hits!=1) return NULL;
    size_t owned=0;
    for(size_t i=0;i<w->assembly.owner_count;++i) {
        const AsmOwner *o=&w->assembly.owners[i];
        if(o->timber==timber) {
            if(o->instance!=found->id || o->member!=*member) return NULL;
            ++owned;
        }
    }
    return owned==1?found:NULL;
}

static void json_schedule_support_owner(const World *w,uint32_t timber)
{
    uint32_t member=0; const AsmInstance *a=schedule_support_owner(w,timber,&member);
    if(!a) { fputs("null",stdout); return; }
    const AsmBinding *b=NULL;
    for(size_t i=0;i<w->assembly.binding_count;++i)
        if(w->assembly.bindings[i].id==a->binding_id) b=&w->assembly.bindings[i];
    const AsmRuleVersion *r=NULL;
    for(size_t i=0;i<w->assembly.rule_count;++i)
        if(w->assembly.rules[i].id==a->rule_id && w->assembly.rules[i].version==a->rule_version &&
           !strcmp(w->assembly.rules[i].fingerprint,a->rule_hash)) r=&w->assembly.rules[i];
    if(!b || !b->complete || b->rule_id!=a->rule_id || b->rule_version!=a->rule_version || !r) { fputs("null",stdout); return; }
    char instance_hash[65],binding_hash[65];
    geo_sha256(a->content,strlen(a->content),instance_hash);
    geo_sha256(b->content,strlen(b->content),binding_hash);
    printf("{\"instanceId\":%u,\"memberId\":%u,\"bindingId\":%u,\"ruleId\":%u,\"ruleVersion\":%u,"
           "\"ruleFingerprint\":\"%s\",\"instanceFingerprint\":\"%s\",\"bindingFingerprint\":\"%s\"}",
           a->id,member,a->binding_id,a->rule_id,a->rule_version,a->rule_hash,instance_hash,binding_hash);
}

/* StopFace.edge_index is a UV min/max ordinal, never a local B0/B1 label.
 * Match an actual native face plane; this handles direction, depth and frame. */
static int schedule_support_local_face(const Timber *t,const PlacementSurface *p,bool along_v,Coord at)
{
    Vector3 axis=along_v?p->frame.axis_v:p->frame.axis_u;
    int found=-1; size_t hits=0;
    for(int face=0;face<TIMBER_FACE_COUNT;++face) {
        Quad3 quad; if(!timber_get_face_room(t,(TimberFaceId)face,&quad)) continue;
        bool same=true;
        for(int v=0;v<4;++v) {
            Point3 q=quad.vertices[v];
            Coord value=(q.x-p->frame.origin.x)*axis.x+(q.y-p->frame.origin.y)*axis.y+(q.z-p->frame.origin.z)*axis.z;
            if(value!=at) same=false;
        }
        if(same) { found=face; ++hits; }
    }
    return hits==1?found:-1;
}

static void json_schedule_support_face(const World *w,const PlacementSurface *p,bool along_v,const StopFace *f)
{
    if(f->kind==STOP_TIMBER_SIDE) {
        int ti=reference_timber_index(w,f->timber_id);
        int face=ti<0?-1:schedule_support_local_face(&w->timbers[ti],p,along_v,f->fixed);
        if(face<0) { fputs("null",stdout); return; }
        const Timber *t=&w->timbers[ti];
        Vector3 axes[3]={t->axis_length,t->axis_a,t->axis_b};
        unsigned face_axis,face_side;
        if(!wood_member_face_spec((WoodMemberFace)face,&face_axis,&face_side)){fputs("null",stdout);return;}
        Vector3 normal=axes[face_axis];
        if(!face_side) normal=vector_negate(normal);
        printf("{\"kind\":\"timber-face\",\"source\":{\"kind\":\"timber\",\"id\":%u},\"localFace\":",t->id);
        js_string(timber_face_short_name((TimberFaceId)face));
        printf(",\"normalWorld\":[%lld,%lld,%lld],\"owner\":",(long long)normal.x,(long long)normal.y,(long long)normal.z);
        json_schedule_support_owner(w,t->id);
    } else {
        /* Effective self-contained rect edges belong to the placement, not
         * to a fabricated boundary 0. Boundary and placement IDs are typed. */
        if(p->derived_fill_id){
            int hole=f->kind==STOP_HOLE_EDGE?f->hole_index:-1;
            size_t component=hole<0?(size_t)f->edge_index/POLY_MAX_VERTICES:(size_t)hole/POLY_MAX_HOLES;
            size_t edge=hole<0?(size_t)f->edge_index%POLY_MAX_VERTICES:(size_t)f->edge_index;char key[512];
            printf("{\"kind\":\"derived-edge\",\"source\":{\"kind\":\"placement\",\"id\":%u},\"edgeKey\":",p->id);
            if(dp_edge_key(w,p,component,hole<0?-1:hole%POLY_MAX_HOLES,edge,key,sizeof key))fputs(key,stdout);else fputs("null",stdout);
            fputs(",\"localFace\":null,\"normalWorld\":null,\"owner\":null",stdout);
        } else {
        bool embedded=p->boundary_id==0;
        printf("{\"kind\":\"%s\",\"source\":{\"kind\":\"%s\",\"id\":%u},\"edgeIndex\":%d,\"holeIndex\":",
               f->kind==STOP_HOLE_EDGE?"hole-edge":"outline-edge",embedded?"placement":"boundary",
               embedded?p->id:f->boundary_id,f->edge_index);
        if(f->kind==STOP_HOLE_EDGE) printf("%d",f->hole_index); else fputs("null",stdout);
        fputs(",\"localFace\":null,\"normalWorld\":null,\"owner\":null",stdout);
        }
    }
    printf(",\"surface\":%u,\"stop\":{\"axis\":\"%c\",\"at\":%lld,\"range\":[%lld,%lld],\"fixity\":\"fixed\"}}",
           p->id,along_v?'v':'u',(long long)f->fixed,(long long)f->lo,(long long)f->hi);
}

static void json_schedule_support_endpoint(const World *w,const PlacementSurface *p,const TimberAnchor *a,
                                         const StopFace *faces,size_t count,bool along_v,Coord at,Coord lo,Coord hi)
{
    const StopFace *found=NULL; size_t hits=0;
    if(a->has_between) {
        /* Stored start/finish are unordered selector slots (R21).
         * At the known native end coordinate, retain only the selected faces
         * that pass the same core full-width/non-FREE candidate filter. */
        for(int k=0;k<2;++k) {
            StopFaceRef ref={a->between[k].kind==1,a->between[k].hole,a->between[k].edge,a->between[k].timber};
            if(a->between[k].kind==2&&!dp_edge_resolve(w,p,a->between[k].key,&ref.hole,&ref.edge))continue;
            const StopFace *candidates[STOP_FACE_MAX]; bool free_edge=false,narrow=false;
            size_t n=stop_ref_candidates(faces,count,&ref,lo,hi,candidates,STOP_FACE_MAX,&free_edge,&narrow);
            for(size_t i=0;i<n;++i) if(candidates[i]->fixed==at) { found=candidates[i]; ++hits; }
        }
    } else {
        hits=pick_stop(faces,count,at,lo,hi,&found);
        if(hits==1 && found->fixity==EDGE_FREE) hits=0;
    }
    if(hits==1 && found->kind==STOP_TIMBER_SIDE) {
        int ti=reference_timber_index(w,found->timber_id);
        if(ti<0 || schedule_support_local_face(&w->timbers[ti],p,along_v,at)<0) hits=0;
    }
    printf("{\"status\":\"%s\",\"at\":%lld,\"crossRange\":[%lld,%lld],\"relation\":",
           hits==1?"exact":"unknown",(long long)at,(long long)lo,(long long)hi);
    if(hits==1) json_schedule_support_face(w,p,along_v,found); else fputs("null",stdout);
    if(hits!=1) fputs(",\"reason\":\"Native support identity is missing or non-unique\"",stdout);
    putchar('}');
}

/* Add to the existing references response as timberSupports, using the same
 * definition fingerprint already computed by cmd_references. No extra read. */
static void json_timber_supports(const World *w,const char fingerprint[65])
{
    printf("{\"schema\":\"native-timber-supports/1\",\"sourceFingerprint\":\"%s\",\"entries\":[",fingerprint);
    bool first=true;
    for(size_t i=0;i<w->timber_count;++i) {
        const Timber *t=&w->timbers[i]; if(!t->placed) continue;
        const TimberAnchor *a=&w->anchors[i]; const PlacementSurface *p=world_find_placement(w,a->placement_id);
        SurfaceRegion2 f;
        printf("%s{\"id\":%u,\"surface\":%u,\"owner\":",first?"":",",t->id,a->placement_id); first=false;
        json_schedule_support_owner(w,t->id);
        if(!p || !timber_a0_footprint_uv(p,t,a,&f)) {
            fputs(",\"start\":{\"status\":\"unknown\",\"relation\":null},\"finish\":{\"status\":\"unknown\",\"relation\":null}}",stdout);
            continue;
        }
        bool along_v=a->length_direction==SURFACE_DIRECTION_POS_V || a->length_direction==SURFACE_DIRECTION_NEG_V;
        bool negative=a->length_direction==SURFACE_DIRECTION_NEG_U || a->length_direction==SURFACE_DIRECTION_NEG_V;
        Coord ends[2]={along_v?f.min_v:f.min_u,along_v?f.max_v:f.max_u};
        Coord lo=along_v?f.min_u:f.min_v,hi=along_v?f.max_u:f.max_v;
        StopFace faces[STOP_FACE_MAX];
        size_t count=collect_stop_faces(w,p,world_placement_boundary(w,p),along_v,t,faces,STOP_FACE_MAX);
        fputs(",\"start\":",stdout); json_schedule_support_endpoint(w,p,a,faces,count,along_v,ends[negative?1:0],lo,hi);
        fputs(",\"finish\":",stdout); json_schedule_support_endpoint(w,p,a,faces,count,along_v,ends[negative?0:1],lo,hi);
        putchar('}');
    }
    fputs("]}",stdout);
}
