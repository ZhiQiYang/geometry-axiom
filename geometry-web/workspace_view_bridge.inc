/* H-116-VIEW/1. Read-only presentation over the existing native DrawTarget.
 * The same walk owns drawing, typed roots and picking; no scene index or label
 * is a public identity. Keys are process-local settings, never write tokens. */
#define WV_ROOT_MAX (WORLD_MAX_PLACEMENTS + WORLD_MAX_GUIDES + WORLD_MAX_TIMBERS + 2 * WORLD_MAX_RC)
#ifndef WV_OP_MAX
#define WV_OP_MAX 131072u
#endif
#define WV_KEY_MAX 64
enum { WV_BOUNDARY=1, WV_PLACEMENT, WV_GUIDE, WV_TIMBER, WV_COLUMN, WV_BEAM };
static const char *const WV_KINDS[]={NULL,"boundary","placement","guide","timber","column","beam"};
static const char *const WV_VIEWS[]={"front","side","bottom","top"};
static const ViewFrame WV_TOP={"俯視圖（X 向右，Y 向上）",{1,0,0},{0,-1,0}};
typedef struct {int kind;uint32_t id;} WorkspaceViewRoot;
typedef struct {
    bool space, focus;uint32_t space_id;int frame;unsigned layers;
    size_t hidden_count;WorkspaceViewRoot hidden[WV_ROOT_MAX];
} WorkspaceViewConfig;
typedef struct {
    bool used;uint64_t revision;char key[65],signature[65];WorkspaceViewConfig config;
} WorkspaceViewKey;
typedef struct {
    WorkspaceViewRoot root;bool placement,boundary;uint32_t placement_id,boundary_id;
    const char *member_face;
} WorkspaceViewTarget;
typedef struct {
    const WorkspaceViewConfig *config;
    WorkspaceViewTarget owner, hit, highlight;
    ViewBounds bounds;ViewPoint2 point;Coord radius;
    size_t count;bool emit,picking,highlighting,degenerate;
} WorkspaceViewOutput;
static WorkspaceViewKey g_workspace_view_keys[WV_KEY_MAX];
static size_t g_workspace_view_next;
static char g_workspace_view_nonce[65];

static void json_workspace_view_capabilities(void)
{
    printf(",\"workspace_view\":{\"schema\":\"workspace-view/1\",\"frames\":[\"front\",\"side\",\"top\",\"bottom\"],"
           "\"maxHiddenRoots\":%u,\"maxOps\":%u,\"maxRequestBytes\":%u}",
           (unsigned)WV_ROOT_MAX,(unsigned)WV_OP_MAX,(unsigned)ENG_INPUT_MAX);
}
static void cmd_workspace_view_capabilities(void)
{
    fputs("{\"ok\":true,\"schema\":\"workspace-view-capabilities/1\",\"capabilities\":[\"workspace-view/1\"]",stdout);
    json_workspace_view_capabilities();fputs("}\n",stdout);
}

static const ViewFrame *wv_frame(int index){return index==3?&WV_TOP:&VIEW_FRAMES[index];}
static int wv_kind(const char *name){for(int i=1;i<=WV_BEAM;++i)if(!strcmp(name,WV_KINDS[i]))return i;return 0;}
static int wv_view(const char *name){for(int i=0;i<4;++i)if(!strcmp(name,WV_VIEWS[i]))return i;return -1;}
static bool wv_same(WorkspaceViewRoot a,WorkspaceViewRoot b){return a.kind==b.kind&&a.id==b.id;}
static int wv_root_compare(const void *a,const void *b)
{
    const WorkspaceViewRoot *x=a,*y=b;
    return x->kind!=y->kind?(x->kind<y->kind?-1:1):x->id<y->id?-1:x->id>y->id;
}
static void wv_error(bool pick,const char *status,const char *message)
{
    printf("{\"ok\":false,\"schema\":\"workspace-view%s-result/1\",\"status\":",pick?"-pick":"");js_string(status);
    printf(",\"revision\":\"%llu\",\"viewKey\":null,\"error\":",(unsigned long long)g_definition_revision);js_string(message);
    fputs(pick?",\"target\":null,\"hoverOps\":[]}\n":",\"layout\":null,\"ops\":[]}\n",stdout);
}
static bool wv_document(const char *path,GeoJson *j,char **text,bool pick)
{
    size_t size;*text=eng_read_file(path,&size);
    if(!*text){wv_error(pick,"INVALID","Cannot read complete view request (maximum 1 MiB)");return false;}
    if(memchr(*text,0,size)||!utf8_is_valid(*text)){
        wv_error(pick,"INVALID","View requests require complete UTF-8 without NUL");free(*text);*text=NULL;return false;
    }
    if(!app_json_parse_n(j,*text,size)){
        wv_error(pick,"INVALID",j->error);geo_json_free(j);free(*text);*text=NULL;return false;
    }
    for(int i=0;i<j->count;++i)if(j->tokens[i].type==GEO_J_STRING)
        for(const unsigned char *p=(const unsigned char*)j->tokens[i].string;*p;++p)if(*p<32||*p==127){
            wv_error(pick,"INVALID","View strings cannot contain control characters");geo_json_free(j);free(*text);*text=NULL;return false;
        }
    return true;
}
static bool wv_revision(const GeoJson *j,int token,uint64_t *out)
{
    char text[21];if(!geo_json_string(j,token,text,sizeof text)||!text[0]||(text[0]=='0'&&text[1]))return false;
    uint64_t value=0;
    for(const char *p=text;*p;++p){if(*p<'0'||*p>'9'||value>(UINT64_MAX-(uint64_t)(*p-'0'))/10)return false;value=value*10+(uint64_t)(*p-'0');}
    *out=value;return true;
}
static bool wv_root_exists(const Scene *scene,WorkspaceViewRoot root)
{
    if(root.kind==WV_BOUNDARY||root.kind==WV_PLACEMENT){
        for(size_t i=0;i<scene->placement_count;++i){const PlacementSurface *p=scene_placement_at(scene,i);
            bool boundary=p->boundary_id&&!p->derived_fill_id;
            if((root.kind==WV_BOUNDARY&&boundary&&root.id==p->boundary_id)||
               (root.kind==WV_PLACEMENT&&!boundary&&root.id==p->id))return true;}
    }else if(root.kind==WV_GUIDE){
        for(size_t i=0;i<scene->guide_count;++i)if(scene->guides[i].id==root.id)return true;
    }else if(root.kind==WV_TIMBER){
        for(size_t i=0;i<scene->timber_count;++i)if(scene->timbers[i].id==root.id&&scene->timbers[i].placed)return true;
    }else if(root.kind==WV_COLUMN){
        for(size_t i=0;i<scene->column_count;++i)if(scene->columns[i].id==root.id)return true;
    }else if(root.kind==WV_BEAM){
        for(size_t i=0;i<scene->beam_count;++i)if(scene->beams[i].id==root.id)return true;
    }
    return false;
}
static bool wv_config(GeoJson *j,WorkspaceViewConfig *config,uint64_t *revision,const Scene *scene)
{
    char name[48];int token;
    if(!geo_json_keys(j,0,"schema,expectedRevision,scope,presentation,layers,hidden","")||
       !geo_json_string(j,geo_json_member(j,0,"schema"),name,sizeof name)||strcmp(name,"workspace-view/1")||
       !wv_revision(j,geo_json_member(j,0,"expectedRevision"),revision))return false;
    token=geo_json_member(j,0,"scope");
    if(!geo_json_string(j,geo_json_member(j,token,"kind"),name,sizeof name))return false;
    if(!strcmp(name,"project")){if(!geo_json_keys(j,token,"kind",""))return false;}
    else if(!strcmp(name,"space")){
        config->space=true;
        if(!geo_json_keys(j,token,"kind,id","")||!eng_u32(j,geo_json_member(j,token,"id"),&config->space_id,false))return false;
        bool found=false;for(size_t i=0;i<scene->space_count;++i)if(scene->spaces[i].id==config->space_id)found=true;
        if(!found)return false;
    }else return false;
    token=geo_json_member(j,0,"presentation");
    if(!geo_json_keys(j,token,"mode,focus","")||!geo_json_string(j,geo_json_member(j,token,"mode"),name,sizeof name))return false;
    if(!strcmp(name,"three")){if(!geo_json_is_null(j,geo_json_member(j,token,"focus")))return false;}
    else if(!strcmp(name,"focus")){
        config->focus=true;
        if(!geo_json_string(j,geo_json_member(j,token,"focus"),name,sizeof name)||(config->frame=wv_view(name))<0)return false;
    }else return false;
    token=geo_json_member(j,0,"layers");
    if(!geo_json_is_array(j,token)||geo_json_size(j,token)>4)return false;
    for(int i=0;i<geo_json_size(j,token);++i){
        if(!geo_json_string(j,geo_json_at(j,token,i),name,sizeof name))return false;
        unsigned layer=!strcmp(name,"face")?1:!strcmp(name,"guide")?2:!strcmp(name,"timber")?4:!strcmp(name,"rc")?8:0;
        if(!layer)return false;config->layers|=layer;
    }
    token=geo_json_member(j,0,"hidden");
    if(!geo_json_is_array(j,token)||geo_json_size(j,token)>WV_ROOT_MAX)return false;
    for(int i=0;i<geo_json_size(j,token);++i){
        int t=geo_json_at(j,token,i);WorkspaceViewRoot root={0};
        if(!geo_json_keys(j,t,"kind,id","")||!geo_json_string(j,geo_json_member(j,t,"kind"),name,sizeof name)||
           !(root.kind=wv_kind(name))||!eng_u32(j,geo_json_member(j,t,"id"),&root.id,false)||!wv_root_exists(scene,root))return false;
        bool duplicate=false;for(size_t k=0;k<config->hidden_count;++k)if(wv_same(root,config->hidden[k]))duplicate=true;
        if(!duplicate)config->hidden[config->hidden_count++]=root;
    }
    qsort(config->hidden,config->hidden_count,sizeof config->hidden[0],wv_root_compare);
    return true;
}
static bool wv_visible(const WorkspaceViewOutput *out,DrawStyle style)
{
    int kind=out->owner.root.kind;if(!kind)return true;
    unsigned layer=kind==WV_TIMBER?4:kind==WV_COLUMN||kind==WV_BEAM?8:
                   kind==WV_GUIDE||style==STYLE_GUIDE||style==STYLE_GUIDE_LABEL?2:1;
    if(!(out->config->layers&layer))return false;
    for(size_t i=0;i<out->config->hidden_count;++i)if(wv_same(out->owner.root,out->config->hidden[i]))return false;
    return !out->highlighting||wv_same(out->owner.root,out->highlight.root);
}
static void wv_owner(void *ctx,const char *kind,uint32_t id,const PlacementSurface *host,const char *face)
{
    WorkspaceViewOutput *out=ctx;PlacementSurface timber_host;
    out->owner=(WorkspaceViewTarget){.root={wv_kind(kind),id},.member_face=face};
    if(out->owner.root.kind==WV_TIMBER){
        int index=reference_timber_index(&g_world,id);
        if(index>=0&&g_world.wood.timbers[index].placed)
            host=app_placement_read(&g_world,g_world.wood.anchors[index].placement_id,&timber_host);
    }
    if(host){out->owner.placement=true;out->owner.placement_id=host->id;
        out->owner.boundary=host->boundary_id&&!host->derived_fill_id;
        out->owner.boundary_id=out->owner.boundary?host->boundary_id:0;}
}
static void wv_json_root(WorkspaceViewRoot root)
{
    if(!root.kind){fputs("null",stdout);return;}
    fputs("{\"kind\":",stdout);js_string(WV_KINDS[root.kind]);printf(",\"id\":%u}",root.id);
}
static void wv_sep(WorkspaceViewOutput *out)
{
    if(out->count++&&out->emit)putchar(',');
}
static void wv_tail(WorkspaceViewOutput *out)
{
    fputs(",\"owner\":",stdout);wv_json_root(out->owner.root);putchar('}');
}
static bool wv_contains(const ViewPoint2 *points,size_t count,ViewPoint2 point,bool interior)
{
    if(count>POLY_MAX_VERTICES)return false;
    PolygonLoop2 loop={.count=count};
    for(size_t i=0;i<count;++i)loop.v[i]=(SurfacePoint2){points[i].x,points[i].y};
    SurfacePoint2 p={point.x,point.y};
    return poly_contains_point(&loop,p)&&(!interior||!poly_point_on_edge(&loop,p));
}
static void wv_polygon(void *ctx,const ViewPoint2 *points,size_t count,DrawStyle style)
{
    WorkspaceViewOutput *out=ctx;
    if(style==STYLE_SURFACE)out->degenerate=view_poly_area2(points,count)==0;
    if(!wv_visible(out,style))return;
    if(out->picking){
        if(style==STYLE_HOLE){
            if(wv_contains(points,count,out->point,true)&&wv_same(out->hit.root,out->owner.root))memset(&out->hit,0,sizeof out->hit);
        }else if(style==STYLE_SURFACE){
            if(!out->degenerate&&wv_contains(points,count,out->point,false))out->hit=out->owner;
            else if(out->degenerate)for(size_t i=0;i<count;++i)
                if(view_dist2_to_segment(out->point,points[i],points[(i+1)%count])<=out->radius*out->radius)out->hit=out->owner;
        }else if((style==STYLE_TIMBER_FACE||style==STYLE_TIMBER_FACE_NEAR||style==STYLE_RC_COLUMN||style==STYLE_RC_BEAM)&&
                 count==4&&view_quad_contains(points,out->point))out->hit=out->owner;
        return;
    }
    for(size_t i=0;i<count;++i)view_bounds_add(&out->bounds,points[i]);
    wv_sep(out);if(!out->emit)return;
    fputs("{\"op\":\"poly\",\"p\":[",stdout);
    for(size_t i=0;i<count;++i)printf("%s%lld,%lld",i?",":"",(long long)points[i].x,(long long)points[i].y);
    printf("],\"s\":%d",out->highlighting?STYLE_HOVER:style);wv_tail(out);
}
static void wv_line(void *ctx,ViewPoint2 a,ViewPoint2 b,DrawStyle style)
{
    WorkspaceViewOutput *out=ctx;if(!wv_visible(out,style))return;
    if(out->picking){
        if((out->owner.root.kind==WV_GUIDE||(out->degenerate&&(style==STYLE_EDGE||style==STYLE_EDGE_FREE)))&&
           view_dist2_to_segment(out->point,a,b)<=out->radius*out->radius)out->hit=out->owner;
        return;
    }
    view_bounds_add(&out->bounds,a);view_bounds_add(&out->bounds,b);wv_sep(out);if(!out->emit)return;
    printf("{\"op\":\"line\",\"x0\":%lld,\"y0\":%lld,\"x1\":%lld,\"y1\":%lld,\"s\":%d",
           (long long)a.x,(long long)a.y,(long long)b.x,(long long)b.y,out->highlighting?STYLE_HOVER:style);wv_tail(out);
}
static void wv_text(void *ctx,ViewPoint2 at,DrawStyle style,const char *text,int rotate)
{
    WorkspaceViewOutput *out=ctx;if(!wv_visible(out,style)||out->picking||out->highlighting)return;
    wv_sep(out);if(!out->emit)return;
    printf("{\"op\":\"text\",\"x\":%lld,\"y\":%lld,\"s\":%d,\"rot\":%d,\"t\":",(long long)at.x,(long long)at.y,style,rotate);
    js_string(text);wv_tail(out);
}
static void wv_annotated_text(void *ctx,ViewPoint2 at,DrawStyle style,const char *text,int rotate,const DrawTextAnnotation *annotation)
{
    WorkspaceViewOutput *out=ctx;if(!wv_visible(out,style)||out->picking||out->highlighting)return;
    wv_sep(out);if(!out->emit)return;
    printf("{\"op\":\"text\",\"x\":%lld,\"y\":%lld,\"s\":%d,\"rot\":%d,\"t\":",(long long)at.x,(long long)at.y,style,rotate);
    js_string(text);
    if(annotation){fputs(",\"annotation\":{\"kind\":",stdout);js_string(annotation->kind);
        printf(",\"entityId\":%u,\"faceId\":",annotation->entity_id);js_string(annotation->face_id);
        fputs(",\"shortLabel\":",stdout);js_string(annotation->short_label);putchar('}');}
    wv_tail(out);
}
static const DrawTarget WV_TARGET={.polygon=wv_polygon,.line=wv_line,.text=wv_text,.annotated_text=wv_annotated_text,.owner=wv_owner};
static void wv_walk(const DrawTarget *target,const ViewFrame *frame,const Scene *scene)
{
    /* The original emitter always accumulates its own complete-scene bounds;
     * the view target separately measures the visible roots for this request. */
    ViewBounds original_bounds={0};scene_draw_view(target,&original_bounds,frame,scene);
}
static size_t wv_layout(const Scene *scene,const WorkspaceViewConfig *config,SceneLayout *layout)
{
    memset(layout,0,sizeof *layout);size_t count=0,n=config->focus?1:3;
    for(size_t i=0;i<n;++i){WorkspaceViewOutput out={.config=config};DrawTarget target=WV_TARGET;target.ctx=&out;
        wv_walk(&target,wv_frame(config->focus?config->frame:(int)i),scene);
        layout->bounds[i]=out.bounds;view_bounds_pad(&layout->bounds[i],600,250,140);count+=out.count+4;}
    if(config->focus){ViewBounds *b=&layout->bounds[0];layout->tx[0]=-b->min_x;layout->ty[0]=-b->min_y;
        layout->total_w=b->max_x-b->min_x;layout->total_h=b->max_y-b->min_y;return count;}
    ViewBounds *f=&layout->bounds[0],*s=&layout->bounds[1],*b=&layout->bounds[2];
    f->min_x=b->min_x=coord_min(f->min_x,b->min_x);f->max_x=b->max_x=coord_max(f->max_x,b->max_x);
    f->min_y=s->min_y=coord_min(f->min_y,s->min_y);f->max_y=s->max_y=coord_max(f->max_y,s->max_y);
    Coord width=f->max_x-f->min_x,height=f->max_y-f->min_y;
    layout->tx[0]=-f->min_x;layout->ty[0]=-f->min_y;
    layout->tx[1]=width+300-s->min_x;layout->ty[1]=-s->min_y;
    layout->tx[2]=-b->min_x;layout->ty[2]=height+300-b->min_y;
    layout->total_w=width+300+s->max_x-s->min_x;layout->total_h=height+300+b->max_y-b->min_y;
    return count;
}
static WorkspaceViewKey *wv_key(const WorkspaceViewConfig *config)
{
    char signature[65];geo_sha256(config,sizeof *config,signature);
    for(size_t i=0;i<WV_KEY_MAX;++i){WorkspaceViewKey *key=&g_workspace_view_keys[i];
        if(key->used&&key->revision==g_definition_revision&&!strcmp(key->signature,signature))return key;}
    if(!g_workspace_view_nonce[0]&&!timber_edit_random_key(g_workspace_view_nonce))return NULL;
    WorkspaceViewKey next={.used=true,.revision=g_definition_revision,.config=*config};
    memcpy(next.signature,signature,sizeof signature);
    char identity[160];snprintf(identity,sizeof identity,"%s:%llu:%s",g_workspace_view_nonce,(unsigned long long)g_definition_revision,signature);
    geo_sha256(identity,strlen(identity),next.key);
    WorkspaceViewKey *key=&g_workspace_view_keys[g_workspace_view_next++%WV_KEY_MAX];*key=next;return key;
}
static void cmd_workspace_view_read(const char *path)
{
    GeoJson j;char *text;if(!wv_document(path,&j,&text,false))return;
    WorkspaceViewConfig config={0};uint64_t revision;Scene scene=scene_from_world(&g_world);SceneLayout layout;
    if(!wv_config(&j,&config,&revision,&scene)){wv_error(false,"INVALID","Invalid or unavailable typed view settings");goto done;}
    if(revision!=g_definition_revision){wv_error(false,"STALE","View revision changed");goto done;}
    if(wv_layout(&scene,&config,&layout)>WV_OP_MAX){wv_error(false,"CAPACITY","View operation capacity exceeded");goto done;}
    WorkspaceViewKey *key=wv_key(&config);if(!key){wv_error(false,"INVALID","Cannot create a session view key");goto done;}
    printf("{\"ok\":true,\"schema\":\"workspace-view-result/1\",\"status\":\"READY\",\"revision\":\"%llu\",\"viewKey\":",
           (unsigned long long)g_definition_revision);js_string(key->key);
    printf(",\"layout\":{\"w\":%lld,\"h\":%lld,\"views\":[",(long long)layout.total_w,(long long)layout.total_h);
    size_t n=config.focus?1:3;
    for(size_t i=0;i<n;++i){int index=config.focus?config.frame:(int)i;const ViewFrame *f=wv_frame(index);const ViewBounds *b=&layout.bounds[i];
        printf("%s{\"viewId\":\"%s\",\"right\":[%lld,%lld,%lld],\"down\":[%lld,%lld,%lld],\"bounds\":[%lld,%lld,%lld,%lld],\"tx\":%lld,\"ty\":%lld}",
            i?",":"",WV_VIEWS[index],(long long)f->right.x,(long long)f->right.y,(long long)f->right.z,
            (long long)f->down.x,(long long)f->down.y,(long long)f->down.z,(long long)b->min_x,(long long)b->min_y,
            (long long)b->max_x,(long long)b->max_y,(long long)layout.tx[i],(long long)layout.ty[i]);}
    fputs("]},\"ops\":[",stdout);WorkspaceViewOutput out={.config=&config,.emit=true};DrawTarget target=WV_TARGET;target.ctx=&out;
    for(size_t i=0;i<n;++i){int index=config.focus?config.frame:(int)i;const ViewBounds *b=&layout.bounds[i];
        memset(&out.owner,0,sizeof out.owner);wv_sep(&out);
        printf("{\"op\":\"begin\",\"tx\":%lld,\"ty\":%lld,\"viewId\":\"%s\",\"owner\":null}",
               (long long)layout.tx[i],(long long)layout.ty[i],WV_VIEWS[index]);
        wv_sep(&out);printf("{\"op\":\"rect\",\"x0\":%lld,\"y0\":%lld,\"x1\":%lld,\"y1\":%lld,\"s\":%d,\"owner\":null}",
            (long long)b->min_x,(long long)b->min_y,(long long)b->max_x,(long long)b->max_y,STYLE_FRAME);
        wv_text(&out,(ViewPoint2){b->min_x+60,b->min_y+110},STYLE_TITLE,wv_frame(index)->title,0);
        wv_walk(&target,wv_frame(index),&scene);wv_sep(&out);fputs("{\"op\":\"end\",\"owner\":null}",stdout);}
    fputs("]}\n",stdout);
done:geo_json_free(&j);free(text);
}
static void cmd_workspace_view_pick(const char *path)
{
    GeoJson j;char *text;if(!wv_document(path,&j,&text,true))return;
    char schema[40],key_text[65],view_name[16];uint64_t revision;int64_t x,y,radius;int point=geo_json_member(&j,0,"point"),view;
    if(!geo_json_keys(&j,0,"schema,expectedRevision,viewKey,viewId,point,radius","")||
       !geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,"workspace-view-pick/1")||
       !wv_revision(&j,geo_json_member(&j,0,"expectedRevision"),&revision)||
       !geo_json_string(&j,geo_json_member(&j,0,"viewKey"),key_text,sizeof key_text)||strlen(key_text)!=64||
       strspn(key_text,"0123456789abcdef")!=64||!geo_json_string(&j,geo_json_member(&j,0,"viewId"),view_name,sizeof view_name)||
       (view=wv_view(view_name))<0||!geo_json_keys(&j,point,"x,y","")||
       !geo_json_integer(&j,geo_json_member(&j,point,"x"),&x)||!geo_json_integer(&j,geo_json_member(&j,point,"y"),&y)||
       !geo_json_integer(&j,geo_json_member(&j,0,"radius"),&radius)||x < -4*COORD_LIMIT||x>4*COORD_LIMIT||
       y < -4*COORD_LIMIT||y>4*COORD_LIMIT||radius<0||radius>4*COORD_LIMIT){wv_error(true,"INVALID","Invalid typed pick request");goto done;}
    WorkspaceViewKey *key=NULL;
    for(size_t i=0;i<WV_KEY_MAX;++i)if(g_workspace_view_keys[i].used&&!strcmp(g_workspace_view_keys[i].key,key_text))key=&g_workspace_view_keys[i];
    if(revision!=g_definition_revision||!key||key->revision!=g_definition_revision){wv_error(true,"STALE","View key or revision retired");goto done;}
    if(key->config.focus?view!=key->config.frame:view==3){wv_error(true,"INVALID","View frame does not belong to this key");goto done;}
    Scene scene=scene_from_world(&g_world);WorkspaceViewOutput out={.config=&key->config,.picking=true,.point={x,y},.radius=radius};
    DrawTarget target=WV_TARGET;target.ctx=&out;wv_walk(&target,wv_frame(view),&scene);
    printf("{\"ok\":true,\"schema\":\"workspace-view-pick-result/1\",\"status\":\"%s\",\"revision\":\"%llu\",\"viewKey\":",
           out.hit.root.kind?"HIT":"NONE",(unsigned long long)g_definition_revision);js_string(key->key);fputs(",\"target\":",stdout);
    if(out.hit.root.kind){fputs("{\"root\":",stdout);wv_json_root(out.hit.root);fputs(",\"placementId\":",stdout);
        if(out.hit.placement)printf("%u",out.hit.placement_id);else fputs("null",stdout);
        fputs(",\"boundaryId\":",stdout);if(out.hit.boundary)printf("%u",out.hit.boundary_id);else fputs("null",stdout);
        fputs(",\"memberFace\":",stdout);if(out.hit.member_face)js_string(out.hit.member_face);else fputs("null",stdout);putchar('}');
    }else fputs("null",stdout);
    fputs(",\"hoverOps\":[",stdout);
    if(out.hit.root.kind){SceneLayout layout;wv_layout(&scene,&key->config,&layout);int slot=key->config.focus?0:view;
        out.highlight=out.hit;out.highlighting=true;out.emit=true;out.picking=false;out.count=0;
        wv_sep(&out);printf("{\"op\":\"begin\",\"tx\":%lld,\"ty\":%lld,\"viewId\":\"%s\",\"owner\":null}",
            (long long)layout.tx[slot],(long long)layout.ty[slot],WV_VIEWS[view]);
        wv_walk(&target,wv_frame(view),&scene);wv_sep(&out);fputs("{\"op\":\"end\",\"owner\":null}",stdout);}
    fputs("]}\n",stdout);
done:geo_json_free(&j);free(text);
}
