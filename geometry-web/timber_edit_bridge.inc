/* H-116-TIMBER/1: bounded host adapter over the existing W timber definitions.
 * Recipes and pending metadata are process-local, never a World or saved file.
 * No kernel/source/support rule is implemented here. */
#define TIMBER_EDIT_MAX WORLD_MAX_TIMBERS
#define TIMBER_RECIPE_MAX 64
typedef struct {
    bool sourced, has_override;
    Coord direct;
    EngDimensionSource source, override_value;
} TimberEditDimension;
typedef struct {
    TimberEditDimension dimensions[2];
    WoodMemberRole role;
    Coord priority;
} TimberEditDefinition;
typedef struct {
    bool used;
    char key[65];
    uint64_t revision;
    uint32_t boundary;
    TimberEditDefinition definition;
} TimberEditRecipe;
typedef struct {
    uint32_t id;
    bool dimension_set[2], role_set, priority_set, direction_set;
    TimberEditDimension dimensions[2];
    WoodMemberRole role;
    Coord priority;
    int direction;
} TimberEditPatch;
typedef struct {
    uint32_t boundary, ids[TIMBER_EDIT_MAX], created_id;
    size_t count;
    bool creating;
} TimberEditPending;
typedef struct {
    TimberEditPending pending;
    TimberEditPatch patches[TIMBER_EDIT_MAX];
    TimberEditDefinition recipe;
    char placement[4096];
    const World *before;
} TimberEditCall;
static TimberEditRecipe g_timber_recipes[TIMBER_RECIPE_MAX];
static size_t g_timber_recipe_next;
static char g_timber_context_key[65];
static TimberEditPending g_timber_pending;

static bool timber_edit_random_key(char out[65])
{
    unsigned char bytes[32];
#ifdef _WIN32
    for(size_t i=0;i<sizeof bytes;i+=sizeof(unsigned int)){
        unsigned int value;if(rand_s(&value))return false;
        memcpy(bytes+i,&value,sizeof value);
    }
#else
    FILE *random=fopen("/dev/urandom","rb");if(!random)return false;
    size_t n=fread(bytes,1,sizeof bytes,random);bool ok=n==sizeof bytes&&!ferror(random);
    fclose(random);if(!ok)return false;
#endif
    for(size_t i=0;i<sizeof bytes;++i)snprintf(out+2*i,3,"%02x",bytes[i]);
    return true;
}
static bool timber_edit_revision(GeoJson *j,int token,uint64_t *out)
{
    char text[21];if(!geo_json_string(j,token,text,sizeof text)||!text[0]||(text[0]=='0'&&text[1]))return false;
    uint64_t value=0;
    for(const char *p=text;*p;++p){
        if(*p<'0'||*p>'9'||value>(UINT64_MAX-(uint64_t)(*p-'0'))/10)return false;
        value=value*10+(uint64_t)(*p-'0');
    }
    *out=value;return true;
}
static bool timber_edit_priority(GeoJson *j,int token,Coord *out)
{
    int64_t value;if(geo_json_integer(j,token,&value)){if(value<1)return false;*out=value;return true;}
    uint64_t exact;if(!timber_edit_revision(j,token,&exact)||!exact||exact>INT64_MAX)return false;
    *out=(Coord)exact;return true;
}
static void timber_edit_json_priority(Coord priority)
{
    printf("\"%lld\"",(long long)priority);
}
static bool timber_edit_document(const char *path,GeoJson *j,char **text)
{
    size_t size;*text=eng_read_file(path,&size);
    if(!*text){eng_bridge_error("TIMBER_INPUT",g_engineering_error);return false;}
    if(memchr(*text,0,size)||!utf8_is_valid(*text)){
        eng_bridge_error("TIMBER_ENCODING","Timber input must be complete UTF-8 without NUL");free(*text);*text=NULL;return false;
    }
    if(!app_json_parse_n(j,*text,size)){
        eng_bridge_error("TIMBER_JSON",j->error);geo_json_free(j);free(*text);*text=NULL;return false;
    }
    /* Decoded control characters are not part of any field in this protocol. */
    for(int i=0;i<j->count;++i)if(j->tokens[i].type==GEO_J_STRING)
        for(const unsigned char *p=(unsigned char*)j->tokens[i].string;*p;++p)if(*p<32||*p==127){
            eng_bridge_error("TIMBER_JSON","Timber strings cannot contain control characters");geo_json_free(j);free(*text);*text=NULL;return false;
        }
    return true;
}
static const char *timber_edit_eligibility(const World *w,uint32_t boundary,uint32_t id)
{
    int index=reference_timber_index(w,id);
    if(index<0)return "The selected timber no longer exists";
    const Timber *t=&w->wood.timbers[index];const TimberAnchor *a=&w->wood.anchors[index];
    if(assembly_owned(w,id))return "I42: edit the owning assembly; ordinary timber reuse and batch edits are unavailable";
    if(!t->placed||!t->auto_length)return "Only ordinary placed D7 timbers are supported";
    const PlacementSurface *p=world_find_placement(w,a->placement_id);
    if(!p||p->boundary_id!=boundary)return "Every selected timber must be on the selected face";
    /* This base World has no #335 group records. Reject unsupported definitions,
     * rather than accepting a client-supplied ownership/group eligibility flag. */
    if(t->role<TIMBER_ROLE_BOUNDARY||t->role>TIMBER_ROLE_CUSTOM||a->span_mode!=SPAN_AUTO||
        (a->anchor_kind!=ANCHOR_AT_LINE&&a->anchor_kind!=ANCHOR_AT_GRID&&a->anchor_kind!=ANCHOR_AT_RULE&&a->anchor_kind!=ANCHOR_AT_EDGE)||
        a->length_direction<0||a->length_direction>3||
        (a->depth_side!=SURFACE_DEPTH_POSITIVE_NORMAL&&a->depth_side!=SURFACE_DEPTH_NEGATIVE_NORMAL)||
        (a->has_through&&a->has_between))return "Unsupported or unknown timber eligibility; the entire selection is blocked";
    return NULL;
}
static void timber_edit_get_definition(const World *w,int index,TimberEditDefinition *out)
{
    memset(out,0,sizeof *out);const Timber *t=&w->wood.timbers[index];
    out->role=t->role;out->priority=t->cut_priority;
    for(int field=0;field<2;++field){
        TimberEditDimension *dimension=&out->dimensions[field];EngTarget target={1,t->id,0,field};
        const EngBinding *binding=eng_binding((World*)w,&target);
        if(binding){dimension->sourced=true;dimension->source=binding->source;dimension->has_override=binding->has_override;dimension->override_value=binding->override_value;}
        else dimension->direct=field?t->size_b:t->size_a;
    }
}
static void timber_edit_json_dimension(const TimberEditDimension *dimension)
{
    if(!dimension->sourced){printf("{\"mode\":\"direct\",\"value\":%lld}",(long long)dimension->direct);return;}
    char source[640];eng_source_json(&dimension->source,source,sizeof source);
    printf("{\"mode\":\"source\",\"source\":%s,\"override\":",source);
    if(dimension->has_override){eng_source_json(&dimension->override_value,source,sizeof source);fputs(source,stdout);}else fputs("null",stdout);
    putchar('}');
}
static void timber_edit_json_row(const World *w,uint32_t boundary,uint32_t id,bool private_id)
{
    int index=reference_timber_index(w,id);if(index<0){fputs("null",stdout);return;}
    const Timber *t=&w->wood.timbers[index];const TimberAnchor *a=&w->wood.anchors[index];
    const char *reason=timber_edit_eligibility(w,boundary,id);
    TimberEditDefinition definition;timber_edit_get_definition(w,index,&definition);
    if(private_id)fputs("{\"handle\":\"new:0\"",stdout);else printf("{\"id\":%u",id);
    printf(",\"eligible\":%s,\"reason\":",reason?"false":"true");if(reason)js_string(reason);else fputs("null",stdout);
    fputs(",\"owner\":",stdout);json_schedule_support_owner(w,id);
    printf(",\"groups\":[],\"groupsKnown\":true,\"placed\":%s,\"placementOrder\":\"%llu\",\"definition\":{\"A\":",t->placed?"true":"false",(unsigned long long)a->order);
    timber_edit_json_dimension(&definition.dimensions[0]);fputs(",\"B\":",stdout);timber_edit_json_dimension(&definition.dimensions[1]);
    fputs(",\"role\":",stdout);js_string(timber_role_name(t->role));printf(",\"priority\":%lld,\"priorityText\":",(long long)t->cut_priority);
    timber_edit_json_priority(t->cut_priority);printf(",\"placement\":{\"on\":%u,\"anchor\":",a->placement_id);
    char anchor[1100],selector[2200];reference_timber_placement_text(a,anchor,sizeof anchor,selector,sizeof selector);
    js_string(anchor);fputs(",\"selector\":",stdout);js_string(selector);fputs(",\"direction\":",stdout);
    const char *directions[]={"+u","-u","+v","-v"};js_string(a->length_direction>=0&&a->length_direction<4?directions[a->length_direction]:"unsupported");
    fputs(",\"side\":",stdout);js_string(a->depth_side==SURFACE_DEPTH_POSITIVE_NORMAL?"+n":"-n");
    printf("}},\"effective\":{\"A\":%lld,\"B\":%lld},\"geometry\":",(long long)t->size_a,(long long)t->size_b);json_reference_geometry(w,index);putchar('}');
}
static bool timber_edit_ids(GeoJson *j,int array,uint32_t ids[TIMBER_EDIT_MAX],size_t *count)
{
    if(!geo_json_is_array(j,array))return false;int n=geo_json_size(j,array);
    if(n<1||n>TIMBER_EDIT_MAX)return false;*count=(size_t)n;
    for(int i=0;i<n;++i){if(!eng_u32(j,geo_json_at(j,array,i),&ids[i],false))return false;
        for(int k=0;k<i;++k)if(ids[k]==ids[i])return false;}
    return true;
}
static void cmd_timber_edit_read(const char *path)
{
    GeoJson j;char *text;if(!timber_edit_document(path,&j,&text))return;
    char schema[40];uint32_t boundary,ids[TIMBER_EDIT_MAX];size_t count;
    if(!geo_json_keys(&j,0,"schema,boundaryId,timberIds","")||!geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||
        strcmp(schema,"timber-edit-read/1")||!eng_u32(&j,geo_json_member(&j,0,"boundaryId"),&boundary,false)||
        !world_find_boundary(&g_world,boundary)||!timber_edit_ids(&j,geo_json_member(&j,0,"timberIds"),ids,&count)){
        eng_bridge_error("TIMBER_SCHEMA","Expected timber-edit-read/1, an existing boundary and 1..64 unique timber ids");goto done;
    }
    const char *reason=NULL;for(size_t i=0;i<count;++i){const char *why=timber_edit_eligibility(&g_world,boundary,ids[i]);if(why&&!reason)reason=why;}
    if(!g_timber_context_key[0]&&!timber_edit_random_key(g_timber_context_key)){
        eng_bridge_error("TIMBER_RANDOM","Cannot create an opaque native session key");goto done;
    }
    TimberEditRecipe *recipe=NULL;
    if(count==1&&!reason){
        recipe=&g_timber_recipes[g_timber_recipe_next%TIMBER_RECIPE_MAX];
        TimberEditRecipe next={0};if(!timber_edit_random_key(next.key)){eng_bridge_error("TIMBER_RANDOM","Cannot create an opaque recipe key");goto done;}
        next.used=true;next.revision=g_definition_revision;next.boundary=boundary;
        timber_edit_get_definition(&g_world,reference_timber_index(&g_world,ids[0]),&next.definition);*recipe=next;++g_timber_recipe_next;
    }
    printf("{\"ok\":true,\"schema\":\"timber-edit-read-result/1\",\"revision\":\"%llu\",\"contextKey\":\"%s\",\"boundaryId\":%u,\"maxOperations\":%d,\"eligible\":%s,\"reason\":",(unsigned long long)g_definition_revision,g_timber_context_key,boundary,TIMBER_EDIT_MAX,reason?"false":"true");
    if(reason)js_string(reason);else fputs("null",stdout);fputs(",\"timbers\":[",stdout);
    for(size_t i=0;i<count;++i){if(i)putchar(',');timber_edit_json_row(&g_world,boundary,ids[i],false);}
    fputs("],\"recipeKey\":",stdout);if(recipe)js_string(recipe->key);else fputs("null",stdout);fputs("}\n",stdout);
done:geo_json_free(&j);free(text);
}
static bool timber_edit_parse_dimension(GeoJson *j,int token,TimberEditDimension *out)
{
    memset(out,0,sizeof *out);char mode[16];
    if(!geo_json_string(j,geo_json_member(j,token,"mode"),mode,sizeof mode))return eng_fail("A/B require an explicit direct or source mode");
    if(!strcmp(mode,"direct")){
        if(!geo_json_keys(j,token,"mode,value","")||!eng_coord(j,geo_json_member(j,token,"value"),&out->direct,true))return eng_fail("Direct A/B requires one positive integer value");
        return true;
    }
    if(strcmp(mode,"source")||!geo_json_keys(j,token,"mode,source,override","")||
        !eng_source_parse(j,geo_json_member(j,token,"source"),&out->source,true))return eng_fail("Source A/B requires its complete typed source and explicit override");
    int override=geo_json_member(j,token,"override");out->sourced=true;out->has_override=!geo_json_is_null(j,override);
    if(out->has_override&&!eng_source_parse(j,override,&out->override_value,false))return false;
    return true;
}
static bool timber_edit_parse_patch(GeoJson *j,int operation,TimberEditPatch *patch)
{
    if(!geo_json_keys(j,operation,"op,id,fields","")||!eng_u32(j,geo_json_member(j,operation,"id"),&patch->id,false))return eng_fail("update-timber-fields needs an id and fields");
    int fields=geo_json_member(j,operation,"fields");
    if(!geo_json_keys(j,fields,"","A,B,role,priority,direction"))return eng_fail("Unknown batch field; only A/B, role, priority and direction are supported");
    for(int field=0;field<2;++field){int token=geo_json_member(j,fields,field?"B":"A");patch->dimension_set[field]=token>=0;
        if(token>=0&&!timber_edit_parse_dimension(j,token,&patch->dimensions[field]))return false;}
    char value[24];int token=geo_json_member(j,fields,"role");patch->role_set=token>=0;
    if(token>=0){if(!geo_json_string(j,token,value,sizeof value))return eng_fail("Invalid timber role");
        if(!strcmp(value,"boundary"))patch->role=TIMBER_ROLE_BOUNDARY;else if(!strcmp(value,"primary"))patch->role=TIMBER_ROLE_PRIMARY;
        else if(!strcmp(value,"secondary"))patch->role=TIMBER_ROLE_SECONDARY;else if(!strcmp(value,"custom"))patch->role=TIMBER_ROLE_CUSTOM;else return eng_fail("Unknown timber role");}
    token=geo_json_member(j,fields,"priority");patch->priority_set=token>=0;
    if(token>=0&&!timber_edit_priority(j,token,&patch->priority))return eng_fail("Priority requires a canonical positive int64 integer or string");
    token=geo_json_member(j,fields,"direction");patch->direction_set=token>=0;
    if(token>=0&&(!geo_json_string(j,token,value,sizeof value)||!lookup_keyword(value,LENGTH_DIRECTION_WORDS,&patch->direction)))return eng_fail("Direction must be +u, -u, +v or -v");
    return true;
}
static bool timber_edit_set_dimension(World *w,int index,int field,const TimberEditDimension *dimension)
{
    EngTarget target={1,w->wood.timbers[index].id,0,field};
    if(dimension->sourced){
        if(!eng_bind(w,&target,&dimension->source))return false;
        EngBinding *binding=eng_binding(w,&target);if(!binding)return eng_fail("Cannot retain dimension source");
        binding->has_override=dimension->has_override;binding->override_value=dimension->override_value;
    }else{
        /* Removing this one binding is explicit; every omitted field stays intact. */
        for(size_t i=0;i<w->wood.engineering.binding_count;++i)if(eng_same_target(&w->wood.engineering.bindings[i].target,&target)){
            size_t left=w->wood.engineering.binding_count-i-1;
            memmove(&w->wood.engineering.bindings[i],&w->wood.engineering.bindings[i+1],left*sizeof(EngBinding));
            --w->wood.engineering.binding_count;break;
        }
        if(field)w->wood.timbers[index].size_b=dimension->direct;else w->wood.timbers[index].size_a=dimension->direct;
    }
    return true;
}
static bool timber_edit_apply_patch(World *w,const TimberEditPatch *patch)
{
    int index=reference_timber_index(w,patch->id);if(index<0)return eng_fail("Selected timber disappeared");
    Timber *timber=&w->wood.timbers[index];
    WoodMemberRole role=patch->role_set?patch->role:timber->role;Coord priority=timber->cut_priority;
    if(role==TIMBER_ROLE_CUSTOM){
        if(patch->role_set&&!patch->priority_set)return eng_fail("An explicitly selected custom role also requires its explicit priority");
        if(patch->priority_set)priority=patch->priority;
    }else{
        if(patch->priority_set)return eng_fail("Only custom timbers can declare priority");
        priority=(Coord)role+1;
    }
    timber->role=role;timber->cut_priority=priority;
    for(int field=0;field<2;++field)if(patch->dimension_set[field]&&!timber_edit_set_dimension(w,index,field,&patch->dimensions[field]))return false;
    if(patch->direction_set)w->wood.anchors[index].length_direction=patch->direction;
    return true;
}
static bool timber_edit_parse_create(GeoJson *j,int operation,TimberEditCall *call)
{
    char key[65],anchor[1100],selector[2200],direction[8],side[8];uint32_t on;
    if(!geo_json_keys(j,operation,"op,recipeKey,placement","")||!geo_json_string(j,geo_json_member(j,operation,"recipeKey"),key,sizeof key))return eng_fail("create-from-recipe needs an opaque recipeKey and placement");
    TimberEditRecipe *recipe=NULL;
    for(size_t i=0;i<TIMBER_RECIPE_MAX;++i)if(g_timber_recipes[i].used&&!strcmp(g_timber_recipes[i].key,key)){recipe=&g_timber_recipes[i];break;}
    if(!recipe||recipe->revision!=g_definition_revision||recipe->boundary!=call->pending.boundary)return eng_fail("Recipe expired or belongs to another native context, revision or face");
    int placement=geo_json_member(j,operation,"placement");
    if(!geo_json_keys(j,placement,"on,anchor,selector,direction,side","")||!eng_u32(j,geo_json_member(j,placement,"on"),&on,false)||
        !geo_json_string(j,geo_json_member(j,placement,"anchor"),anchor,sizeof anchor)||
        !geo_json_string(j,geo_json_member(j,placement,"selector"),selector,sizeof selector)||
        !geo_json_string(j,geo_json_member(j,placement,"direction"),direction,sizeof direction)||
        !geo_json_string(j,geo_json_member(j,placement,"side"),side,sizeof side))return eng_fail("Placement requires an explicit on, anchor, selector, direction and side");
    const PlacementSurface *surface=world_find_placement(&g_world,on);int parsed;
    if(!surface||surface->boundary_id!=call->pending.boundary)return eng_fail("Paste/Repeat must select a placement on the same face");
    if(!lookup_keyword(direction,LENGTH_DIRECTION_WORDS,&parsed)||!lookup_keyword(side,DEPTH_SIDE_WORDS,&parsed))return eng_fail("Invalid placement direction or side");
    if(strncmp(anchor,"at-line ",8)&&strncmp(anchor,"at-face ",8))return eng_fail("Placement needs one complete at-line or at-face anchor");
    if(selector[0]&&strncmp(selector,"through ",8)&&strncmp(selector,"between ",8))return eng_fail("Placement selector must be empty, through or between");
    char anchor_copy[sizeof anchor],selector_copy[sizeof selector];char *parts[16];
    snprintf(anchor_copy,sizeof anchor_copy,"%s",anchor);int n=split_tokens(anchor_copy,parts,16);
    bool clause=n==2&&!strcmp(parts[0],"at-face");
    if(n>=3&&!strcmp(parts[0],"at-line"))clause=
        (!strcmp(parts[1],"guide")&&n==3)||(!strcmp(parts[1],"grid")&&(n==5||(n==7&&!strcmp(parts[5],"band"))))||(!strcmp(parts[1],"rule")&&n==9);
    if(!clause)return eng_fail("Anchor must contain exactly one complete anchor clause");
    snprintf(selector_copy,sizeof selector_copy,"%s",selector);n=split_tokens(selector_copy,parts,16);
    if(n&&!(n==2&&!strcmp(parts[0],"through"))&&!(n==3&&!strcmp(parts[0],"between")))return eng_fail("Selector must contain exactly one complete selector clause");
    if(g_world.wood.timber_count>=WORLD_MAX_TIMBERS)return eng_fail("Timber capacity is full");
    /* The number exists only in the isolated candidate. No live ID is reserved,
     * and preview exposes new:0 instead; publication is the allocation point. */
    WORLD_NEXT_ID(call->pending.created_id,g_world.wood.timbers,g_world.wood.timber_count,false);
    int written=snprintf(call->placement,sizeof call->placement,"place %u on %u %s%s%s %s %s",call->pending.created_id,on,anchor,selector[0]?" ":"",selector,direction,side);
    if(written<0||(size_t)written>=sizeof call->placement)return eng_fail("Placement is too long");
    call->recipe=recipe->definition;return true;
}
static bool timber_edit_evaluate(void *after,GeoEvalContext *sources,void *opaque)
{
    (void)sources;World *candidate=after;TimberEditCall *call=opaque;bool ok=true;
    const World *previous=g_subgrid_before;bool capturing=g_reference_capturing;
    g_subgrid_before=call->before;g_reference_capturing=true;
    if(call->pending.creating){
        size_t index=candidate->wood.timber_count++;
        ok=wood_member_construct(call->pending.created_id,0,1,1,true,call->recipe.role,call->recipe.priority,&candidate->wood.timbers[index]);
        memset(&candidate->wood.anchors[index],0,sizeof candidate->wood.anchors[index]);
        for(int field=0;field<2&&ok;++field)ok=timber_edit_set_dimension(candidate,(int)index,field,&call->recipe.dimensions[field]);
        /* One create operation uses the existing complete placement parser and
         * its common final validation; no derived placement is reconstructed. */
        char command[sizeof call->placement];snprintf(command,sizeof command,"%s",call->placement);
        char *tokens[64];int count=split_tokens(command,tokens,64);
        g_reference_trial=*candidate;
        if(ok)ok=apply_reference_place("timber-edit",1,tokens,count,candidate);
    }else{
        /* I8: all explicit definitions first; no per-member validation/commit. */
        for(size_t i=0;i<call->pending.count&&ok;++i)ok=timber_edit_apply_patch(candidate,&call->patches[i]);
        g_reference_trial=*candidate;
        if(ok)ok=world_revalidate(candidate);
    }
    for(size_t i=0;i<candidate->wood.timber_count&&ok;++i)if(!candidate->wood.timbers[i].placed)ok=eng_fail("I9: candidate contains an unplaced timber");
    if(!ok){*candidate=g_reference_trial;if(!g_engineering_error[0])eng_fail(g_revalidate_error[0]?g_revalidate_error:scene_last_error()[0]?scene_last_error():"I8: timber candidate rejected");}
    g_subgrid_before=previous;g_reference_capturing=capturing;
    return ok;
}
static void timber_edit_json_message(const char *message,const TimberEditPending *pending)
{
    if(!pending->creating){js_string(message);return;}
    /* Native diagnostic strings also name timbers. Map the candidate-local
     * number to its private handle without changing dimensions or clause ids. */
    const char *prefixes[]={"timber ","timber:","角材 ","角材（","角材("};
    char out[4096];size_t used=0;const char *p=message;
    while(*p&&used+1<sizeof out){bool replaced=false;
        for(size_t i=0;i<sizeof prefixes/sizeof prefixes[0];++i){
            char needle[80];int n=snprintf(needle,sizeof needle,"%s%u",prefixes[i],pending->created_id);
            if(n>0&&!strncmp(p,needle,(size_t)n)&&(p[n]<'0'||p[n]>'9')){
                int wrote=snprintf(out+used,sizeof out-used,"%snew:0",prefixes[i]);
                if(wrote<0||(size_t)wrote>=sizeof out-used){out[used]=0;js_string(out);return;}
                used+=(size_t)wrote;p+=n;replaced=true;break;
            }
        }
        if(!replaced)out[used++]=*p++;
    }
    out[used]=0;js_string(out);
}
static void timber_edit_json_preview(const AppWorldCandidate *transaction,const TimberEditPending *pending,bool valid,bool no_op,const char *error)
{
    printf("{\"schema\":\"timber-edit-preview-result/1\",\"token\":");if(no_op)fputs("null",stdout);else printf("%u",g_preview.token);
    printf(",\"valid\":%s,\"revision\":\"%llu\",\"noOp\":%s,\"before\":[",valid?"true":"false",(unsigned long long)g_definition_revision,no_op?"true":"false");
    if(!pending->creating)for(size_t i=0;i<pending->count;++i){if(i)putchar(',');timber_edit_json_row(&transaction->before,pending->boundary,pending->ids[i],false);}
    fputs("],\"after\":[",stdout);
    if(pending->creating)timber_edit_json_row(&transaction->after,pending->boundary,pending->created_id,true);
    else for(size_t i=0;i<pending->count;++i){if(i)putchar(',');timber_edit_json_row(&transaction->after,pending->boundary,pending->ids[i],false);}
    fputs("],\"changes\":[",stdout);
    if(!no_op){if(pending->creating)fputs("{\"op\":\"create-from-recipe\",\"handle\":\"new:0\"}",stdout);
        else for(size_t i=0;i<pending->count;++i)printf("%s{\"op\":\"update-timber-fields\",\"id\":%u}",i?",":"",pending->ids[i]);}
    fputs("],\"dependencies\":{\"timbers\":",stdout);json_candidate_timbers(&transaction->before,&transaction->after,false);
    fputs(",\"guides\":",stdout);json_candidate_guides(&transaction->before,&transaction->after);fputs("},\"violations\":[",stdout);
    if(!valid){fputs("{\"code\":\"TIMBER_INVALID\",\"clause\":\"I8/I8a\",\"message\":",stdout);timber_edit_json_message(error,pending);putchar('}');}
    if(!no_op)for(size_t i=0;i<g_preview.issue_count;++i){const ReferenceIssue *issue=&g_preview.issues[i];printf("%s{",!valid||i?",":"");
        if(pending->creating&&issue->timber==pending->created_id)fputs("\"handle\":\"new:0\"",stdout);else printf("\"timber\":%u",issue->timber);
        fputs(",\"clause\":",stdout);js_string(issue->clause);fputs(",\"message\":",stdout);timber_edit_json_message(issue->actual,pending);putchar('}');}
    fputs("]}",stdout);
}
static void cmd_timber_edit_preview(const char *path)
{
    if(g_history.grouping){eng_bridge_error("HISTORY_GROUP","Finish the existing history group first");return;}
    GeoJson j;char *text;if(!timber_edit_document(path,&j,&text))return;
    TimberEditCall call={0};char schema[40];uint64_t revision;int operations=geo_json_member(&j,0,"operations");
    if(!geo_json_keys(&j,0,"schema,expectedRevision,boundaryId,operations","")||!geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,"timber-edit-transaction/1")||
        !timber_edit_revision(&j,geo_json_member(&j,0,"expectedRevision"),&revision)||!eng_u32(&j,geo_json_member(&j,0,"boundaryId"),&call.pending.boundary,false)||
        !world_find_boundary(&g_world,call.pending.boundary)||!geo_json_is_array(&j,operations)){
        eng_bridge_error("TIMBER_SCHEMA","Expected timber-edit-transaction/1 with canonical uint64 revision string, face and operations");goto done;
    }
    if(revision!=g_definition_revision){eng_bridge_error("STALE","Timber definitions changed; read and preview again");goto done;}
    int count=geo_json_size(&j,operations);if(count<1||count>TIMBER_EDIT_MAX){eng_bridge_error("CAPACITY","Timber batch needs 1..64 operations");goto done;}
    call.pending.count=(size_t)count;g_engineering_error[0]=0;
    for(int i=0;i<count;++i){int operation=geo_json_at(&j,operations,i);char op[32];
        if(!geo_json_string(&j,geo_json_member(&j,operation,"op"),op,sizeof op)){eng_fail("Every operation needs a supported op");goto invalid;}
        if(!strcmp(op,"create-from-recipe")){
            if(count!=1){eng_fail("A reuse transaction creates exactly one timber and cannot mix updates");goto invalid;}
            call.pending.creating=true;if(!timber_edit_parse_create(&j,operation,&call))goto invalid;
        }else if(!strcmp(op,"update-timber-fields")){
            if(!timber_edit_parse_patch(&j,operation,&call.patches[i]))goto invalid;
            call.pending.ids[i]=call.patches[i].id;
            for(int k=0;k<i;++k)if(call.pending.ids[k]==call.pending.ids[i]){eng_fail("Duplicate timber target");goto invalid;}
            const char *reason=timber_edit_eligibility(&g_world,call.pending.boundary,call.pending.ids[i]);if(reason){eng_fail(reason);goto invalid;}
        }else{eng_fail("Unsupported timber edit operation");goto invalid;}
    }
    {
        AppWorldCandidate *transaction=app_world_candidate_create(&g_world);if(!transaction){eng_bridge_error("MEMORY","Cannot allocate timber candidate");goto done;}
        call.before=&transaction->before;g_reference_issue_count=0;g_scene_last_error[0]=0;g_revalidate_error[0]=0;
        bool valid=app_world_candidate_evaluate(transaction,timber_edit_evaluate,&call)==GEO_CANDIDATE_OK;
        if(valid&&!app_world_candidate_seal(transaction)){valid=false;eng_fail("I8: cannot seal timber candidate");}
        char error[512];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:"Candidate rejected");
        bool no_op=valid&&world_definitions_equal(&transaction->before,&transaction->after);
        if(!no_op){char *label="timber-edit-transaction";reference_stage(transaction,&label,1,valid);
            g_preview.engineering_batch=true;g_preview.timber_batch=true;g_timber_pending=call.pending;}
        fputs("{\"ok\":true,\"preview\":",stdout);timber_edit_json_preview(transaction,&call.pending,valid,no_op,error);fputs("}\n",stdout);
        if(no_op)app_world_candidate_destroy(transaction);
    }
    goto done;
invalid:eng_bridge_error("TIMBER_INPUT",g_engineering_error[0]?g_engineering_error:"Invalid timber request");
done:geo_json_free(&j);free(text);
}
static void cmd_timber_edit_confirm(const char *arg)
{
    uint32_t token;
    if(!arg||!parse_u32(arg,&token)||!g_preview.ready||!g_preview.timber_batch||g_preview.token!=token||!g_preview.valid){eng_bridge_error("TOKEN","Missing, invalid or unrelated timber preview token");return;}
    if(g_history.grouping||g_preview.revision!=g_definition_revision||!app_world_candidate_current(g_preview.transaction,&g_world)){
        g_preview.ready=false;eng_bridge_error("STALE","Timber preview expired; read and preview again");return;
    }
    if(!g_timber_pending.creating)for(size_t i=0;i<g_timber_pending.count;++i){const char *reason=timber_edit_eligibility(&g_world,g_timber_pending.boundary,g_timber_pending.ids[i]);
        if(reason){g_preview.ready=false;eng_bridge_error("TIMBER_ELIGIBILITY",reason);return;}}
    if(!app_world_candidate_revalidate(g_preview.transaction,&g_world)){
        g_preview.ready=false;eng_bridge_error("INVALID",g_revalidate_error);return;
    }
    if(world_definitions_equal(&g_world,&g_preview.transaction->after)){
        g_preview.ready=false;eng_bridge_error("NO_OP","No-op timber edits have no commit token");return;
    }
    if(g_definition_revision==UINT64_MAX){g_preview.ready=false;eng_bridge_error("CAPACITY","Definition revision capacity is exhausted; World unchanged");return;}
    uint64_t before=g_definition_revision;history_record(&g_world);
    if(!app_world_candidate_publish(g_preview.transaction,&g_world,true)){
        history_unrecord();g_preview.ready=false;eng_bridge_error("STALE","Timber candidate changed before publication");return;
    }
    ++g_definition_revision;g_preview.ready=false;
    printf("{\"ok\":true,\"history_changed\":true,\"revision\":\"%llu\",\"before_revision\":\"%llu\",\"transaction_id\":%u,\"changedIds\":[",(unsigned long long)g_definition_revision,(unsigned long long)before,token);
    if(!g_timber_pending.creating)for(size_t i=0;i<g_timber_pending.count;++i)printf("%s%u",i?",":"",g_timber_pending.ids[i]);
    fputs("],\"created\":[",stdout);if(g_timber_pending.creating)printf("{\"handle\":\"new:0\",\"kind\":\"timber\",\"id\":%u}",g_timber_pending.created_id);fputs("]}\n",stdout);
}
static void cmd_timber_edit_cancel(const char *arg)
{
    uint32_t token;if(!arg||!parse_u32(arg,&token)){eng_bridge_error("TOKEN","Cancel requires a timber preview token");return;}
    bool cancelled=g_preview.ready&&g_preview.timber_batch&&g_preview.token==token;
    if(cancelled){g_preview.ready=false;app_candidate_discard(g_preview.transaction->control);}
    printf("{\"ok\":true,\"cancelled\":%s,\"revision\":\"%llu\"}\n",cancelled?"true":"false",(unsigned long long)g_definition_revision);
}
