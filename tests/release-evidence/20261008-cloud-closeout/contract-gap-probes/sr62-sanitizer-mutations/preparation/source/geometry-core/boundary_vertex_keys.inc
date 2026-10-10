/* D30 / I37: boundary-local vertex identities. Included after engineering.inc.
 * Geometry order is not identity: ordinary edits may only match old coordinates;
 * moving an identified point requires the complete, hash-guarded keyed command. */
static bool g_boundary_keyed_update;
static uint32_t g_boundary_keyed_id;

static const PolygonLoop2 *boundary_keys_loop(const SpaceBoundarySurface *b,size_t loop)
{
    return loop ? &b->holes[loop-1] : &b->outline;
}

static const BoundaryVertexKeys *world_find_vertex_keys(const World *w,uint32_t bid)
{
    if (!w) return NULL;
    for (size_t i=0;i<w->vertex_key_count;++i)
        if (w->vertex_keys[i].boundary_id==bid) return &w->vertex_keys[i];
    return NULL;
}

static bool boundary_keys_has(const BoundaryVertexKeys *keys,uint32_t key)
{
    if (!keys || !key) return false;
    for (size_t l=0;l<keys->loop_count;++l)
        for (size_t i=0;i<keys->counts[l];++i)
            if (keys->keys[l][i]==key) return true;
    return false;
}

static bool boundary_keys_valid(const SpaceBoundarySurface *b,const BoundaryVertexKeys *keys)
{
    if (!b || !keys || keys->boundary_id!=b->id || b->hole_count>POLY_MAX_HOLES ||
        keys->loop_count!=b->hole_count+1) return false;
    for (size_t l=0;l<keys->loop_count;++l) {
        const PolygonLoop2 *loop=boundary_keys_loop(b,l);
        if (loop->count>POLY_MAX_VERTICES || keys->counts[l]!=loop->count) return false;
        for (size_t i=0;i<keys->counts[l];++i) {
            uint32_t key=keys->keys[l][i];
            if (!key || (keys->next_key && key>=keys->next_key)) return false;
            for (size_t ol=0;ol<=l;++ol) {
                size_t stop=ol==l?i:keys->counts[ol];
                for (size_t oi=0;oi<stop;++oi)
                    if (keys->keys[ol][oi]==key) return false;
            }
        }
    }
    return true;
}

static bool boundary_vertex_by_key(const World *w,uint32_t bid,uint32_t key,SurfacePoint2 *out)
{
    const SpaceBoundarySurface *b=world_find_boundary(w,bid);
    const BoundaryVertexKeys *keys=world_find_vertex_keys(w,bid);
    if (!key || !boundary_keys_valid(b,keys)) return false;
    for (size_t l=0;l<keys->loop_count;++l)
        for (size_t i=0;i<keys->counts[l];++i)
            if (keys->keys[l][i]==key) {
                if (out) *out=boundary_keys_loop(b,l)->v[i];
                return true;
            }
    return false;
}

static void boundary_geometry_hash(const SpaceBoundarySurface *b,char out[65])
{
    /* Decimal integers and explicit separators avoid platform/padding/endianness
     * dependencies. Neither the boundary id nor vertex keys are geometry. */
    char canonical[128+(POLY_MAX_HOLES+1)*(64+POLY_MAX_VERTICES*64)];
    size_t used=0;
    out[0]='\0';
    if (!b || b->hole_count>POLY_MAX_HOLES) return;
    int n=snprintf(canonical,sizeof canonical,"boundary-geometry/1|kind=%u|loops=%u\n",
        (unsigned)b->kind,(unsigned)(b->hole_count+1));
    if (n<0 || (size_t)n>=sizeof canonical) return;
    used=(size_t)n;
    for (size_t l=0;l<=b->hole_count;++l) {
        const PolygonLoop2 *loop=boundary_keys_loop(b,l);
        if (loop->count>POLY_MAX_VERTICES) return;
        n=snprintf(canonical+used,sizeof canonical-used,"%s|count=%u\n",l?"hole":"outer",(unsigned)loop->count);
        if (n<0 || (size_t)n>=sizeof canonical-used) return;
        used+=(size_t)n;
        for (size_t i=0;i<loop->count;++i) {
            n=snprintf(canonical+used,sizeof canonical-used,"%lld,%lld,%u\n",
                (long long)loop->v[i].u,(long long)loop->v[i].v,(unsigned)loop->fixity[i]);
            if (n<0 || (size_t)n>=sizeof canonical-used) return;
            used+=(size_t)n;
        }
    }
    eng_sha256(canonical,used,out);
}

static bool boundary_geometry_hash_matches(const SpaceBoundarySurface *b,const char *value)
{
    char expected[65];
    if (!value || strlen(value)!=64) return false;
    boundary_geometry_hash(b,expected);
    if (!expected[0]) return false;
    for (size_t i=0;i<64;++i) {
        char c=value[i];
        if (c>='A' && c<='F') c=(char)(c-'A'+'a');
        if (c!=expected[i]) return false;
    }
    return true;
}

static bool boundary_keys_initialize(World *w,uint32_t bid)
{
    const SpaceBoundarySurface *b=world_find_boundary(w,bid);
    const BoundaryVertexKeys *existing=world_find_vertex_keys(w,bid);
    if (existing) return boundary_keys_valid(b,existing);
    if (!b || b->hole_count>POLY_MAX_HOLES || w->vertex_key_count>=WORLD_MAX_BOUNDARIES) return false;
    BoundaryVertexKeys keys={0};
    keys.boundary_id=bid; keys.loop_count=b->hole_count+1; keys.next_key=1;
    for (size_t l=0;l<keys.loop_count;++l) {
        keys.counts[l]=boundary_keys_loop(b,l)->count;
        if (keys.counts[l]>POLY_MAX_VERTICES) return false;
        for (size_t i=0;i<keys.counts[l];++i) keys.keys[l][i]=keys.next_key++;
    }
    if (!boundary_keys_valid(b,&keys)) return false;
    w->vertex_keys[w->vertex_key_count++]=keys;
    return true;
}

static bool boundary_keys_error(char *error,size_t cap,const char *message)
{
    if (error && cap) snprintf(error,cap,"D30/I37: %s",message);
    return false;
}

static bool boundary_keys_reconcile(World *candidate,const World *before,char *error,size_t cap)
{
    if (candidate->vertex_key_count>WORLD_MAX_BOUNDARIES)
        return boundary_keys_error(error,cap,"too many boundary vertex identity tables");
    if (before) for (size_t i=0;i<before->vertex_key_count;++i) {
        uint32_t bid=before->vertex_keys[i].boundary_id;
        if (world_find_boundary(candidate,bid) && !world_find_vertex_keys(candidate,bid))
            return boundary_keys_error(error,cap,"an existing boundary identity table cannot be removed");
    }
    for (size_t m=0;m<candidate->vertex_key_count;) {
        BoundaryVertexKeys *keys=&candidate->vertex_keys[m];
        const SpaceBoundarySurface *b=world_find_boundary(candidate,keys->boundary_id);
        for (size_t other=0;other<m;++other)
            if (candidate->vertex_keys[other].boundary_id==keys->boundary_id)
                return boundary_keys_error(error,cap,"duplicate boundary identity table");
        if (!b) {
            for (size_t j=0;j<candidate->grid_binding_count;++j)
                if (candidate->grid_bindings[j].boundary_id==keys->boundary_id)
                    return boundary_keys_error(error,cap,"cannot delete a boundary referenced by a grid binding");
            memmove(keys,keys+1,(candidate->vertex_key_count-m-1)*sizeof *keys);
            memset(&candidate->vertex_keys[--candidate->vertex_key_count],0,sizeof *keys);
            continue;
        }
        const BoundaryVertexKeys *old=world_find_vertex_keys(before,keys->boundary_id);
        const SpaceBoundarySurface *old_boundary=before?world_find_boundary(before,keys->boundary_id):NULL;
        bool keyed=g_boundary_keyed_update && g_boundary_keyed_id==keys->boundary_id;
        if (old && !boundary_keys_valid(old_boundary,old))
            return boundary_keys_error(error,cap,"the previous boundary identity table is invalid");
        if (old && !keyed) {
            /* Always derive from the transaction baseline, so repeated validation
             * of one candidate cannot allocate another set of keys. */
            BoundaryVertexKeys remapped={0};
            remapped.boundary_id=b->id; remapped.loop_count=b->hole_count+1;
            remapped.next_key=old->next_key;
            if (b->hole_count>POLY_MAX_HOLES)
                return boundary_keys_error(error,cap,"too many boundary loops");
            for (size_t l=0;l<remapped.loop_count;++l) {
                remapped.counts[l]=boundary_keys_loop(b,l)->count;
                if (remapped.counts[l]>POLY_MAX_VERTICES)
                    return boundary_keys_error(error,cap,"too many boundary vertices");
            }
            for (size_t ol=0;ol<old->loop_count;++ol) for (size_t oi=0;oi<old->counts[ol];++oi) {
                SurfacePoint2 p=boundary_keys_loop(old_boundary,ol)->v[oi];
                size_t matches=0,match_loop=0,match_index=0;
                for (size_t l=0;l<remapped.loop_count;++l) {
                    const PolygonLoop2 *loop=boundary_keys_loop(b,l);
                    for (size_t i=0;i<loop->count;++i)
                        if (loop->v[i].u==p.u && loop->v[i].v==p.v) {
                            ++matches; match_loop=l; match_index=i;
                        }
                }
                if (matches!=1 || remapped.keys[match_loop][match_index])
                    return boundary_keys_error(error,cap,"an identified vertex moved, disappeared, or is ambiguous; use boundary-keyed with the current geometry-hash");
                remapped.keys[match_loop][match_index]=old->keys[ol][oi];
            }
            for (size_t l=0;l<remapped.loop_count;++l) for (size_t i=0;i<remapped.counts[l];++i) {
                if (remapped.keys[l][i]) continue;
                if (!remapped.next_key)
                    return boundary_keys_error(error,cap,"boundary vertex key space is exhausted");
                remapped.keys[l][i]=remapped.next_key;
                remapped.next_key=remapped.next_key==UINT32_MAX?0:remapped.next_key+1;
            }
            *keys=remapped;
        }
        if (!boundary_keys_valid(b,keys))
            return boundary_keys_error(error,cap,"invalid, zero, duplicate, or inconsistent boundary vertex keys");
        if (old && keyed) {
            for (size_t l=0;l<keys->loop_count;++l) for (size_t i=0;i<keys->counts[l];++i) {
                uint32_t key=keys->keys[l][i];
                if (!boundary_keys_has(old,key) && (!old->next_key || key<old->next_key))
                    return boundary_keys_error(error,cap,"a retired boundary vertex key cannot be reused");
            }
            if (!old->next_key ? keys->next_key!=0 : (keys->next_key && keys->next_key<old->next_key))
                return boundary_keys_error(error,cap,"boundary vertex key allocation cannot move backwards");
        }
        ++m;
    }
    for (size_t i=0;i<candidate->grid_binding_count;++i) {
        const GridBinding *binding=&candidate->grid_bindings[i];
        if (!boundary_vertex_by_key(candidate,binding->boundary_id,binding->vertex_key,NULL))
            return boundary_keys_error(error,cap,"a grid binding references a missing boundary vertex key");
    }
    return true;
}

static bool boundary_keys_same(const BoundaryVertexKeys *a,const BoundaryVertexKeys *b)
{
    if (a->boundary_id!=b->boundary_id || a->loop_count!=b->loop_count || a->next_key!=b->next_key) return false;
    for (size_t l=0;l<a->loop_count;++l) {
        if (a->counts[l]!=b->counts[l]) return false;
        for (size_t i=0;i<a->counts[l];++i) if (a->keys[l][i]!=b->keys[l][i]) return false;
    }
    return true;
}

static bool apply_boundary_keys_line(const char *path,int line_no,char **tokens,int count,World *world)
{
    uint32_t id;
    if (count<7 || !parse_u32(tokens[1],&id) || !id || strcmp(tokens[2],"outer")) {
        scene_error(path,line_no,"D30: boundary-vertex-keys requires boundary id and complete outer/hole keys"); return false;
    }
    const SpaceBoundarySurface *boundary=world_find_boundary(world,id);
    if (!boundary) { scene_error(path,line_no,"D30: boundary-vertex-keys boundary does not exist"); return false; }
    BoundaryVertexKeys keys={0}; keys.boundary_id=id; keys.loop_count=boundary->hole_count+1;
    int pos=2; uint32_t highest=0;
    for (size_t l=0;l<keys.loop_count;++l) {
        if (pos>=count || strcmp(tokens[pos++],l?"hole":"outer")) {
            scene_error(path,line_no,"D30: boundary-vertex-keys must describe every loop in geometry order"); return false;
        }
        keys.counts[l]=boundary_keys_loop(boundary,l)->count;
        for (size_t i=0;i<keys.counts[l];++i) {
            uint32_t key;
            if (pos>=count || !parse_u32(tokens[pos++],&key) || !key) {
                scene_error(path,line_no,"D30: boundary vertex keys must be nonzero uint32 values, one per vertex"); return false;
            }
            keys.keys[l][i]=key; if (key>highest) highest=key;
        }
    }
    keys.next_key=highest==UINT32_MAX?0:highest+1;
    const BoundaryVertexKeys *existing=world_find_vertex_keys(world,id);
    if (pos<count) {
        if (pos+2!=count || strcmp(tokens[pos],"next-key") || !parse_u32(tokens[pos+1],&keys.next_key)) {
            scene_error(path,line_no,"D30: only optional next-key uint32 may follow the complete vertex key table"); return false;
        }
        pos+=2;
    } else if (existing) keys.next_key=existing->next_key;
    if (pos!=count || !boundary_keys_valid(boundary,&keys)) {
        scene_error(path,line_no,"D30: invalid or duplicate vertex keys, or next-key below the active keys"); return false;
    }
    if (existing) {
        if (boundary_keys_same(existing,&keys)) return true;
        scene_error(path,line_no,"D30: boundary-vertex-keys cannot rebind an existing identity table; use boundary-keyed"); return false;
    }
    if (world->vertex_key_count>=WORLD_MAX_BOUNDARIES) {
        scene_error(path,line_no,"D30: too many boundary identity tables"); return false;
    }
    World candidate=*world;
    candidate.vertex_keys[candidate.vertex_key_count++]=keys;
    if (!world_revalidate(&candidate)) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:
            "I37: boundary vertex identity replay failed world validation"); return false;
    }
    *world=candidate;
    return true;
}

static bool apply_boundary_keyed_line(const char *path,int line_no,char **tokens,int count,World *world)
{
    uint32_t id;
    if (count<9 || count>SCENE_MAX_TOKENS || !parse_u32(tokens[1],&id) || !id ||
        strcmp(tokens[2],"geometry-hash") || strcmp(tokens[4],"outline")) {
        scene_error(path,line_no,"D30: boundary-keyed requires id geometry-hash HASH outline K:u,v ..."); return false;
    }
    const SpaceBoundarySurface *previous=world_find_boundary(world,id);
    if (!previous || !boundary_geometry_hash_matches(previous,tokens[3])) {
        scene_error(path,line_no,"D30: boundary-keyed geometry-hash is stale or boundary does not exist"); return false;
    }
    char *plain[SCENE_MAX_TOKENS];
    int plain_count=2;
    plain[0]="boundary"; plain[1]=tokens[1];
    BoundaryVertexKeys keys={0}; keys.boundary_id=id;
    const BoundaryVertexKeys *old=world_find_vertex_keys(world,id);
    uint32_t highest=old && old->next_key?old->next_key-1:0;
    bool exhausted=old && !old->next_key;
    bool reading_vertices=false,seen_kind=false,seen_fixity[POLY_MAX_HOLES+1]={false};
    size_t loop=0;
    for (int pos=4;pos<count;++pos) {
        const char *token=tokens[pos];
        if (!strcmp(token,"outline") || !strcmp(token,"hole")) {
            if (!strcmp(token,"outline")) {
                if (keys.loop_count) { scene_error(path,line_no,"D30: boundary-keyed has more than one outline"); return false; }
                keys.loop_count=1; loop=0;
            } else {
                if (!keys.loop_count || keys.loop_count>=POLY_MAX_HOLES+1) {
                    scene_error(path,line_no,"D30: boundary-keyed has invalid or too many holes"); return false;
                }
                loop=keys.loop_count++;
            }
            plain[plain_count++]=tokens[pos]; reading_vertices=true;
        } else if (!strcmp(token,"kind")) {
            if (seen_kind || pos+1>=count) { scene_error(path,line_no,"D30: boundary-keyed kind must occur at most once"); return false; }
            seen_kind=true; reading_vertices=false;
            plain[plain_count++]=tokens[pos]; plain[plain_count++]=tokens[++pos];
        } else if (!strcmp(token,"fixity")) {
            if (!keys.loop_count || seen_fixity[loop]) { scene_error(path,line_no,"D30: boundary-keyed fixity must occur at most once per loop"); return false; }
            seen_fixity[loop]=true; reading_vertices=false;
            plain[plain_count++]=tokens[pos];
            for (size_t i=0;i<keys.counts[loop];++i) {
                if (++pos>=count) { scene_error(path,line_no,"D30: boundary-keyed fixity must specify every edge"); return false; }
                plain[plain_count++]=tokens[pos];
            }
        } else {
            const char *colon=strchr(token,':');
            char key_text[16]; uint32_t key; SurfacePoint2 point;
            size_t length=colon?(size_t)(colon-token):0;
            if (!reading_vertices || !keys.loop_count || !length || length>=sizeof key_text ||
                keys.counts[loop]>=POLY_MAX_VERTICES) {
                scene_error(path,line_no,"D30: boundary-keyed expects K:u,v vertices after outline/hole"); return false;
            }
            memcpy(key_text,token,length); key_text[length]='\0';
            if (!parse_u32(key_text,&key) || !key || !parse_uv(colon+1,&point)) {
                scene_error(path,line_no,"D30: boundary-keyed requires a nonzero uint32 key and valid u,v coordinates"); return false;
            }
            if (old && !boundary_keys_has(old,key) && (!old->next_key || key<old->next_key)) {
                scene_error(path,line_no,"D30: boundary-keyed cannot reuse a retired vertex key"); return false;
            }
            keys.keys[loop][keys.counts[loop]++]=key;
            if (key>highest) highest=key;
            plain[plain_count++]=(char *)(colon+1);
        }
    }
    keys.next_key=exhausted || highest==UINT32_MAX?0:highest+1;
    SpaceBoundarySurface replacement;
    if (!parse_boundary_body(path,line_no,plain,2,plain_count,&replacement)) return false;
    replacement.id=id;
    if (!boundary_keys_valid(&replacement,&keys)) {
        scene_error(path,line_no,"D30: boundary-keyed contains duplicate, missing, or inconsistent vertex keys"); return false;
    }
    if (!old && world->vertex_key_count>=WORLD_MAX_BOUNDARIES) {
        scene_error(path,line_no,"D30: too many boundary identity tables"); return false;
    }
    World candidate=*world;
    for (size_t i=0;i<candidate.boundary_count;++i)
        if (candidate.boundaries[i].id==id) { candidate.boundaries[i]=replacement; break; }
    size_t slot=old?(size_t)(old-world->vertex_keys):candidate.vertex_key_count++;
    candidate.vertex_keys[slot]=keys;
    bool previous_keyed=g_boundary_keyed_update;
    uint32_t previous_keyed_id=g_boundary_keyed_id;
    const World *previous_baseline=g_subgrid_before;
    g_boundary_keyed_update=true; g_boundary_keyed_id=id; g_subgrid_before=world;
    bool ok=world_revalidate(&candidate);
    g_boundary_keyed_update=previous_keyed; g_boundary_keyed_id=previous_keyed_id; g_subgrid_before=previous_baseline;
    if (!ok) {
        scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:
            "I37: keyed boundary update failed dependency validation (World unchanged)"); return false;
    }
    *world=candidate;
    return true;
}

static void boundary_keys_dump(const World *w,FILE *out)
{
    /* Keep boundary order deterministic, independent of when a first binding
     * happened to initialize its table. High-water state prevents retired keys
     * from being allocated again after a save/reload. */
    for (size_t b=0;b<w->boundary_count;++b) {
        const BoundaryVertexKeys *keys=world_find_vertex_keys(w,w->boundaries[b].id);
        if (!keys) continue;
        fprintf(out,"boundary-vertex-keys %u",keys->boundary_id);
        for (size_t l=0;l<keys->loop_count;++l) {
            fprintf(out," %s",l?"hole":"outer");
            for (size_t i=0;i<keys->counts[l];++i) fprintf(out," %u",keys->keys[l][i]);
        }
        fprintf(out," next-key %u\n",keys->next_key);
    }
}
