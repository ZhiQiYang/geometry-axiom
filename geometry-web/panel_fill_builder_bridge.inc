/* PF-6N host/CLI owner. W owns R45; this closed transport composes explicit
 * before/after D7 operations and publishes only the final sealed candidate.
 * Suggestions and handles are process-local, never persisted in World. */
#define PF6_OUTER_MAX ENG_OPERATION_MAX
typedef struct {
    bool create,on_host,has_a,has_b;
    char key[97],anchor[1100],selector[2200],direction[8],side[8];
    uint32_t id,on;
    EngDimensionSource a,b;
    WoodMemberRole role;
} Pf6OuterOperation;
typedef struct {
    uint64_t revision,generation;
    char key[65];
    char *intent;
    bool analysis_valid;
    World *basis;
    Pf6Input input;
    Pf6OuterOperation operations[PF6_OUTER_MAX];
    size_t pre_count,post_count;
    Pf6Report report;
} Pf6Proposal;
typedef struct {
    const Pf6Proposal *proposal;
    const World *before;
    const char **selected;
    size_t selected_count;
    bool suggesting;
    Pf6Report report;
    uint32_t created[PF6_OUTER_MAX];
} Pf6OuterCall;
typedef struct {
    uint32_t token;
    uint64_t generation;
    Pf6Report report;
    uint32_t created[PF6_OUTER_MAX];
} Pf6Pending;
static Pf6Proposal *g_pf6_proposal;
static Pf6Pending g_pf6_pending;
static uint64_t g_pf6_generation;

static void pf6_proposal_free(Pf6Proposal *proposal)
{
    if(!proposal)return;
    pf6_report_free(&proposal->report);free(proposal->basis);free(proposal->intent);free(proposal);
}
static void pf6_pending_clear(void)
{
    pf6_report_free(&g_pf6_pending.report);memset(&g_pf6_pending,0,sizeof g_pf6_pending);
    if(g_preview.ready&&g_preview.pf6_batch){
        g_preview.ready=false;app_world_candidate_discard(g_preview.transaction);
    }
}
static bool pf6_document(const char *path,GeoJson *j,char **text)
{
    size_t size;*text=eng_read_file(path,&size);
    if(!*text){eng_bridge_error("INPUT",g_engineering_error);return false;}
    if(memchr(*text,0,size)||!utf8_is_valid(*text)){
        eng_bridge_error("ENCODING","PF-6 requires complete UTF-8 without NUL");
        free(*text);*text=NULL;return false;
    }
    if(!app_json_parse_n(j,*text,size)){
        eng_bridge_error("JSON",j->error);geo_json_free(j);free(*text);*text=NULL;return false;
    }
    for(int i=0;i<j->count;++i)if(j->tokens[i].type==GEO_J_STRING)
        for(const unsigned char *p=(unsigned char*)j->tokens[i].string;*p;++p)
            if(*p<32||*p==127){
                eng_bridge_error("SCHEMA","PF-6 strings cannot contain control characters");
                geo_json_free(j);free(*text);*text=NULL;return false;
            }
    return true;
}
static bool pf6_outer_parse(GeoJson *j,int token,Pf6OuterOperation *out)
{
    char op[40];
    if(!geo_json_string(j,geo_json_member(j,token,"op"),op,sizeof op))return eng_fail("PF-6 outer operation needs op");
    if(!strcmp(op,"set-timber-fields")){
        int fields=geo_json_member(j,token,"fields");
        if(!geo_json_keys(j,token,"op,id,fields","")||
           !eng_u32(j,geo_json_member(j,token,"id"),&out->id,false)||
           !geo_json_keys(j,fields,"","A,B"))return eng_fail("PF-6 set-timber-fields needs existing id and only A/B");
        int a=geo_json_member(j,fields,"A"),b=geo_json_member(j,fields,"B");
        out->has_a=a>=0;out->has_b=b>=0;
        if((!out->has_a&&!out->has_b)||(out->has_a&&!eng_source_parse(j,a,&out->a,false))||
           (out->has_b&&!eng_source_parse(j,b,&out->b,false)))return eng_fail("PF-6 set-timber-fields needs explicit typed dimensions");
        return true;
    }
    if(strcmp(op,"create-timber")||!geo_json_keys(j,token,"op,tempKey,A,B,role,placement",""))
        return eng_fail("PF-6 outer operations support only create-timber or set-timber-fields");
    out->create=true;
    if(!geo_json_string(j,geo_json_member(j,token,"tempKey"),out->key,sizeof out->key)||!out->key[0]||
       !eng_source_parse(j,geo_json_member(j,token,"A"),&out->a,false)||
       !eng_source_parse(j,geo_json_member(j,token,"B"),&out->b,false))return eng_fail("PF-6 create needs a nonempty tempKey and typed A/B");
    for(const char *p=out->key;*p;++p)if(!((*p>='a'&&*p<='z')||(*p>='A'&&*p<='Z')||
        (*p>='0'&&*p<='9')||*p=='_'||*p=='-'))return eng_fail("PF-6 tempKey uses ASCII letters, digits, underscore or hyphen");
    char role[16];
    if(!geo_json_string(j,geo_json_member(j,token,"role"),role,sizeof role))return eng_fail("PF-6 create needs explicit role");
    if(!strcmp(role,"boundary"))out->role=TIMBER_ROLE_BOUNDARY;
    else if(!strcmp(role,"primary"))out->role=TIMBER_ROLE_PRIMARY;
    else if(!strcmp(role,"secondary"))out->role=TIMBER_ROLE_SECONDARY;
    else return eng_fail("PF-6 outer create supports boundary, primary or secondary");
    int placement=geo_json_member(j,token,"placement"),on=geo_json_member(j,placement,"on");
    char host[24];
    if(geo_json_string(j,on,host,sizeof host))out->on_host=!strcmp(host,"r45-host");
    if(!out->on_host&&!eng_u32(j,on,&out->on,false))return eng_fail("PF-6 placement.on is an existing id or r45-host");
    if(!geo_json_keys(j,placement,"on,anchor,selector,direction,side","")||
       !geo_json_string(j,geo_json_member(j,placement,"anchor"),out->anchor,sizeof out->anchor)||
       !geo_json_string(j,geo_json_member(j,placement,"selector"),out->selector,sizeof out->selector)||
       !geo_json_string(j,geo_json_member(j,placement,"direction"),out->direction,sizeof out->direction)||
       !geo_json_string(j,geo_json_member(j,placement,"side"),out->side,sizeof out->side))return eng_fail("PF-6 placement must specify its complete D7 intent");
    if(strcmp(out->direction,"+u")&&strcmp(out->direction,"-u")&&strcmp(out->direction,"+v")&&strcmp(out->direction,"-v"))
        return eng_fail("PF-6 D7 direction must be explicit");
    if(strcmp(out->side,"+n")&&strcmp(out->side,"-n"))return eng_fail("PF-6 D7 side must be explicit");
    return true;
}
static bool pf6_parse_outer(GeoJson *j,Pf6Proposal *proposal)
{
    for(int phase=0;phase<2;++phase){
        int array=geo_json_member(j,0,phase?"post":"pre");
        if(!geo_json_is_array(j,array))return eng_fail("PF-6 pre and post must both be explicit arrays");
        int n=geo_json_size(j,array);size_t offset=phase?proposal->pre_count:0;
        if(n<0||offset+(size_t)n>PF6_OUTER_MAX)return eng_fail("I33 CAPACITY: PF-6 outer operations exceed 256");
        if(phase)proposal->post_count=(size_t)n;else proposal->pre_count=(size_t)n;
        for(int k=0;k<n;++k){
            Pf6OuterOperation *op=&proposal->operations[offset+(size_t)k];
            if(!pf6_outer_parse(j,geo_json_at(j,array,k),op))return false;
            if(op->create)for(size_t p=0;p<offset+(size_t)k;++p)
                if(proposal->operations[p].create&&!strcmp(op->key,proposal->operations[p].key))
                    return eng_fail("PF-6 outer tempKey must be unique across pre and post");
        }
    }
    return true;
}
static bool pf6_existing_host(const World *w,uint32_t fill,uint32_t *id)
{
    for(uint64_t i=0;i<w->wood.finish_surfaces.host_count;++i)
        if(w->wood.finish_surfaces.hosts[i].fill_id==fill){*id=w->wood.finish_surfaces.hosts[i].id;return true;}
    return false;
}
static bool pf6_outer_targets(const World *before,const Pf6Proposal *proposal)
{
    for(size_t i=0;i<proposal->pre_count+proposal->post_count;++i){
        const Pf6OuterOperation *op=&proposal->operations[i];
        if(op->create){
            if(!op->on_host&&!world_find_placement(before,op->on))
                return eng_fail("PF-6 numeric placement.on must name an existing formal host; use r45-host for the generated host");
        }else{
            int index=reference_timber_index(before,op->id);
            if(index<0||!before->wood.timbers[index].placed||!before->wood.timbers[index].auto_length||
               assembly_owned(before,op->id)||boundary_pair_index(before,op->id)>=0)
                return eng_fail("PF-6 set-timber-fields must name an existing formal ordinary D7; candidate ids cannot be guessed");
            for(int field=0;field<2;++field)if(field?op->has_b:op->has_a){
                EngTarget target={1,op->id,0,field};const EngBinding *binding=eng_binding((World*)before,&target);
                if(binding&&binding->has_override)return eng_fail("PF-6 set-timber-fields cannot replace an overridden field; resolve its explicit override first");
            }
        }
    }
    return true;
}
/* Each outer step is itself candidate-local and atomic. A rejected last step
 * leaves its input intact; the caller must still reject the WHOLE package. */
static bool pf6_outer_references(const World *before,const TimberAnchor *anchor)
{
    /* CLI numeric references identify formal definitions, never allocation
     * guesses. Native callers compose with candidate-owned typed handles. */
    if((anchor->anchor_kind==ANCHOR_AT_LINE&&!world_find_guide(before,anchor->ref_guide))||
       (anchor->anchor_kind==ANCHOR_AT_GRID&&!world_find_grid(before,anchor->ref_grid))||
       (anchor->anchor_kind==ANCHOR_AT_RULE&&!world_find_grid(before,anchor->ref_rule.grid_id))||
       (anchor->anchor_kind==ANCHOR_AT_EDGE&&anchor->ref_is_timber&&reference_timber_index(before,anchor->ref_timber)<0))
        return eng_fail("PF-6 numeric anchor references must name existing formal definitions; candidate ids cannot be guessed");
    if(anchor->has_between)for(int k=0;k<2;++k)
        if(anchor->between[k].kind==1&&reference_timber_index(before,anchor->between[k].timber)<0)
            return eng_fail("PF-6 numeric between references must name existing formal timbers; candidate ids cannot be guessed");
    return true;
}
static bool pf6_outer_operation(World *world,const World *before,const Pf6OuterOperation *operation,uint32_t host,bool host_present,uint32_t *created)
{
    World *trial=malloc(sizeof *trial);if(!trial)return eng_fail("I33 CAPACITY: PF-6 outer workspace unavailable");
    *trial=*world;bool ok=true;
    if(operation->create){
        if(trial->wood.timber_count>=WORLD_MAX_TIMBERS){ok=eng_fail("I33 CAPACITY: PF-6 timber capacity");goto done;}
        uint32_t id=pf6_member_id(trial);
        size_t index=trial->wood.timber_count;
        ok=wood_member_construct(id,0,1,1,true,operation->role,(Coord)operation->role+1,&trial->wood.timbers[index]);
        if(!ok)goto done;
        ++trial->wood.timber_count;memset(&trial->wood.anchors[index],0,sizeof trial->wood.anchors[index]);
        EngTarget a={1,id,0,0},b={1,id,0,1};
        ok=eng_bind(trial,&a,&operation->a)&&eng_bind(trial,&b,&operation->b);
        if(!ok)goto done;
        uint32_t on=operation->on_host?host:operation->on;
        if((operation->on_host&&!host_present)||!world_find_placement(trial,on)){ok=eng_fail("R45: explicit outer member has no existing host; empty R45 selection does not create one");goto done;}
        char command[4096];int n=snprintf(command,sizeof command,"place %u on %u %s%s%s %s %s",id,on,operation->anchor,
            operation->selector[0]?" ":"",operation->selector,operation->direction,operation->side);
        if(n<0||(size_t)n>=sizeof command){ok=eng_fail("I33 CAPACITY: PF-6 D7 command too long");goto done;}
        char *tokens[128];int count=split_tokens(command,tokens,128);
        TimberAnchor anchor;int anchor_index;
        ok=reference_place_parse("pf6-outer",1,tokens,count,trial,&anchor,&anchor_index)&&pf6_outer_references(before,&anchor);
        if(!ok)goto done;
        ok=apply_reference_place("pf6-outer",1,tokens,count,trial);
        if(ok)*created=id;
    }else{
        int index=reference_timber_index(trial,operation->id);
        if(index<0||!trial->wood.timbers[index].placed||!trial->wood.timbers[index].auto_length||assembly_owned(trial,operation->id)||
           boundary_pair_index(trial,operation->id)>=0){ok=eng_fail("PF-6 updates require an existing ordinary placed D7");goto done;}
        EngTarget a={1,operation->id,0,0},b={1,operation->id,0,1};
        if(operation->has_a)ok=eng_bind(trial,&a,&operation->a);
        if(operation->has_b&&ok)ok=eng_bind(trial,&b,&operation->b);
    }
done:
    if(ok)*world=*trial;
    else if(!g_engineering_error[0])eng_fail(scene_last_error()[0]?scene_last_error():"R45: outer D7 step rejected");
    free(trial);return ok;
}
static bool pf6_outer_validate(World *candidate)
{
    /* I8/I24: validate every existing dependency as well as all new members.
     * g_subgrid_before remains the original outer submission, not a prefix. */
    if(!world_revalidate(candidate))return eng_fail(g_revalidate_error[0]?g_revalidate_error:"I8: PF-6 complete candidate rejected");
    for(size_t i=0;i<candidate->wood.timber_count;++i)
        if(!candidate->wood.timbers[i].placed)return eng_fail("I9: PF-6 candidate contains an unplaced timber");
    return true;
}
static bool pf6_outer_evaluate(void *after,GeoEvalContext *sources,void *opaque)
{
    (void)sources;World *candidate=after;Pf6OuterCall *call=opaque;const Pf6Proposal *p=call->proposal;
    const World *previous=g_subgrid_before;bool capturing=g_reference_capturing;
    g_subgrid_before=call->before;g_reference_capturing=true;
    identity_explicit_reset();bool ok=true;Pf6Report setup={0};
    if(call->suggesting||call->selected_count){
        ok=pf6_prepare(candidate,&p->input,&setup);
        if(!ok)eng_fail(setup.error);
    }else setup.host_present=pf6_existing_host(candidate,p->input.fill_id,&setup.host_id);
    for(size_t i=0;i<p->pre_count&&ok;++i)
        if(!pf6_outer_operation(candidate,call->before,&p->operations[i],setup.host_id,setup.host_present,&call->created[i]))ok=false;
    if(ok){
        if(call->suggesting)ok=pf6_suggest(candidate,&p->input,&call->report);
        else ok=pf6_apply(candidate,&p->input,call->selected,call->selected_count,&call->report);
        if(!ok)eng_fail(call->report.error);
    }
    if(!call->suggesting)for(size_t i=p->pre_count;i<p->pre_count+p->post_count&&ok;++i)
        if(!pf6_outer_operation(candidate,call->before,&p->operations[i],setup.host_id,setup.host_present,&call->created[i]))ok=false;
    if(ok&&!call->suggesting)ok=pf6_outer_validate(candidate);
    if(ok&&!call->suggesting)for(size_t i=0;i<call->report.plan.count;++i){
        WoodR45Candidate *entry=&call->report.plan.items[i];
        if(entry->selected&&entry->valid&&entry->id&&!pf6_footprint(candidate,&call->report,entry,entry->id)){
            ok=eng_fail("I8a: cannot disclose a selected member's final post-operation geometry");break;
        }
    }
    if(setup.host_created)call->report.host_created=true;
    if(setup.grid_created)call->report.grid_created=true;
    if(!call->report.host_present){call->report.host_id=setup.host_id;call->report.host_present=setup.host_present;}
    if(!call->report.grid_present){call->report.grid_id=setup.grid_id;call->report.grid_present=setup.grid_present;}
    pf6_report_free(&setup);g_subgrid_before=previous;g_reference_capturing=capturing;return ok;
}
static void pf6_json_plan(const Pf6Report *report,bool omissions)
{
    const char *phases[]={"boundary","edge-primary","seam-primary","seam-secondary","free-edge","covered-edge","hole-edge"};
    putchar('[');bool first=true;
    for(size_t i=0;i<report->plan.count;++i){
        const WoodR45Candidate *entry=&report->plan.items[i];
        if((!entry->selectable)!=omissions)continue;
        printf("%s{\"key\":",first?"":",");first=false;js_string(entry->key);
        fputs(",\"phase\":",stdout);js_string(entry->kind>=0&&entry->kind<7?phases[entry->kind]:"unsupported");
        printf(",\"selectable\":%s,\"selected\":%s,\"valid\":%s,\"role\":",entry->selectable?"true":"false",entry->selected?"true":"false",entry->valid?"true":"false");
        js_string(timber_role_name((WoodMemberRole)entry->role));
        printf(",\"axis\":\"%c\",\"source\":{\"edgeKey\":",entry->axis?'v':'u');
        if(entry->edge_key[0])js_string(entry->edge_key);else fputs("null",stdout);
        printf(",\"lineAxis\":\"%c\",\"k\":\"%lld\",\"band\":",entry->line_axis?'v':'u',(long long)entry->k);
        if(entry->has_band)printf("\"%lld\"",(long long)entry->band);else fputs("null",stdout);
        printf(",\"range\":[\"%lld\",\"%lld\"],\"through\":\"%lld\"},\"geometry\":{\"rect\":[\"%lld\",\"%lld\",\"%lld\",\"%lld\"],\"length\":\"%lld\"},\"duplicateOf\":",
            (long long)entry->range[0],(long long)entry->range[1],(long long)entry->through,
            (long long)entry->rect[0],(long long)entry->rect[1],(long long)entry->rect[2],(long long)entry->rect[3],(long long)entry->length);
        if(entry->duplicate_of>=0&&(size_t)entry->duplicate_of<report->plan.count)js_string(report->plan.items[entry->duplicate_of].key);else fputs("null",stdout);
        fputs(",\"diagnostics\":[",stdout);
        if(entry->error[0]){fputs("{\"clause\":\"D45/R45/R6\",\"message\":",stdout);js_string(entry->error);putchar('}');}
        fputs("]}",stdout);
    }
    putchar(']');
}
static char *pf6_scene_text(const World *world)
{
    FILE *file=tmpfile();if(!file)return NULL;
    world_dump_dsl(world,file);
    if(ferror(file)||fflush(file)||fseek(file,0,SEEK_END)){fclose(file);return NULL;}
    long size=ftell(file);if(size<0||size>ENG_INPUT_MAX||fseek(file,0,SEEK_SET)){fclose(file);return NULL;}
    char *text=malloc((size_t)size+1);if(!text){fclose(file);return NULL;}
    size_t n=fread(text,1,(size_t)size,file);bool ok=n==(size_t)size&&!ferror(file);fclose(file);
    if(!ok){free(text);return NULL;}text[n]=0;return text;
}
static void pf6_json_handles(const Pf6Report *report,const uint32_t *created,const Pf6Proposal *proposal,bool formal)
{
    bool first=true;putchar('[');
    for(int k=0;k<2;++k)if(k?report->grid_created:report->host_created){
        printf("%s{\"tempKey\":\"r45:%s\",\"kind\":\"%s\",\"%s\":%u}",first?"":",",k?"grid":"host",k?"grid":"placement",formal?"id":"candidateId",k?report->grid_id:report->host_id);first=false;
    }
    for(size_t i=0;i<report->plan.count;++i){
        const WoodR45Candidate *entry=&report->plan.items[i];if(!entry->selected||!entry->valid||!entry->id)continue;
        printf("%s{\"tempKey\":\"r45:%s\",\"kind\":\"timber\",\"%s\":%u}",first?"":",",entry->key,formal?"id":"candidateId",entry->id);first=false;
    }
    for(size_t i=0;i<proposal->pre_count+proposal->post_count;++i)if(created[i]){
        printf("%s{\"tempKey\":\"%s:%s\",\"kind\":\"timber\",\"%s\":%u}",first?"":",",i<proposal->pre_count?"pre":"post",proposal->operations[i].key,formal?"id":"candidateId",created[i]);first=false;
    }
    putchar(']');
}
static void pf6_json_reused(const Pf6Report *report)
{
    bool first=true;putchar('[');
    for(int k=0;k<2;++k){
        uint32_t id=k?report->grid_id:report->host_id;
        if(!(k?report->grid_present:report->host_present)||(k?report->grid_created:report->host_created))continue;
        printf("%s{\"tempKey\":\"r45:%s\",\"kind\":\"%s\",\"id\":%u}",first?"":",",k?"grid":"host",k?"grid":"placement",id);first=false;
    }
    putchar(']');
}
static void cmd_pf6_suggest(const char *path)
{
    GeoJson j;char *text;if(!pf6_document(path,&j,&text))return;
    Pf6Proposal *proposal=calloc(1,sizeof *proposal);char schema[48];
    if(!proposal){eng_bridge_error("MEMORY","Cannot allocate PF-6 request");goto done;}
    g_engineering_error[0]=0;g_scene_last_error[0]=0;g_reference_issue_count=0;
    if(!geo_json_keys(&j,0,"schema,expectedRevision,input,pre,post","")||
       !geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,"panel-fill-builder-suggest/1")||
       !timber_edit_revision(&j,geo_json_member(&j,0,"expectedRevision"),&proposal->revision)||
       !pf6_parse_input(&j,geo_json_member(&j,0,"input"),&proposal->input)||!pf6_parse_outer(&j,proposal)){
        eng_bridge_error("SCHEMA",g_engineering_error[0]?g_engineering_error:"Expected panel-fill-builder-suggest/1 with exact revision, input, pre and post");goto done;
    }
    if(proposal->revision!=g_definition_revision){eng_bridge_error("EXPIRED","PF-6 source revision changed");goto done;}
    proposal->intent=malloc(ENG_INPUT_MAX+1);
    if(!proposal->intent||!geo_json_canonical(&j,0,proposal->intent,ENG_INPUT_MAX+1)){
        eng_bridge_error("CAPACITY","Cannot retain and disclose the complete PF-6 input");goto done;
    }
    if(g_pf6_generation==UINT64_MAX||!timber_edit_random_key(proposal->key)){
        eng_bridge_error("CAPACITY","Cannot allocate a fresh PF-6 suggestion generation");goto done;
    }
    proposal->basis=malloc(sizeof *proposal->basis);
    if(!proposal->basis){eng_bridge_error("MEMORY","Cannot retain PF-6 source definitions");goto done;}
    *proposal->basis=g_world;
    if(!pf6_outer_targets(proposal->basis,proposal)){eng_bridge_error("SCHEMA",g_engineering_error);goto done;}
    AppWorldCandidate *candidate=app_world_candidate_create(&g_world);
    if(!candidate){eng_bridge_error("MEMORY","Cannot allocate PF-6 analysis");goto done;}
    Pf6OuterCall call={0};call.proposal=proposal;call.before=&candidate->before;call.suggesting=true;
    bool valid=app_world_candidate_evaluate(candidate,pf6_outer_evaluate,&call)==GEO_CANDIDATE_OK;
    proposal->analysis_valid=valid;
    char error[512];snprintf(error,sizeof error,"%s",valid?"":g_engineering_error[0]?g_engineering_error:call.report.error);
    app_world_candidate_destroy(candidate);
    proposal->report=call.report;proposal->generation=++g_pf6_generation;
    pf6_pending_clear();pf6_proposal_free(g_pf6_proposal);g_pf6_proposal=proposal;proposal=NULL;
    printf("{\"ok\":true,\"schema\":\"panel-fill-builder-suggestions/1\",\"revision\":\"%llu\",\"setKey\":\"%s\",\"generation\":\"%llu\",\"confirmable\":false,\"token\":null,\"valid\":%s,\"complete\":false,\"entries\":",
        (unsigned long long)g_definition_revision,g_pf6_proposal->key,(unsigned long long)g_pf6_proposal->generation,valid?"true":"false");
    pf6_json_plan(&g_pf6_proposal->report,false);fputs(",\"omissions\":",stdout);pf6_json_plan(&g_pf6_proposal->report,true);
    fputs(",\"intent\":",stdout);fputs(g_pf6_proposal->intent,stdout);
    printf(",\"outerOperations\":{\"pre\":%zu,\"post\":%zu,\"postEvaluation\":\"after-selection\"},\"error\":",g_pf6_proposal->pre_count,g_pf6_proposal->post_count);
    if(error[0])js_string(error);else fputs("null",stdout);fputs("}\n",stdout);
done:pf6_proposal_free(proposal);geo_json_free(&j);free(text);
}
static void cmd_pf6_select(const char *path)
{
    if(g_history.grouping){eng_bridge_error("HISTORY_GROUP","Finish the current history group first");return;}
    if((g_preview.ready&&!g_preview.pf6_batch)||g_pair_interactive.active){eng_bridge_error("PENDING","Finish or cancel the other candidate first");return;}
    GeoJson j;char *text;if(!pf6_document(path,&j,&text))return;
    char schema[48],key[65];uint64_t revision,generation;const char **selected=NULL;
    int array=geo_json_member(&j,0,"selected");
    if(!geo_json_keys(&j,0,"schema,expectedRevision,setKey,generation,selected","")||
       !geo_json_string(&j,geo_json_member(&j,0,"schema"),schema,sizeof schema)||strcmp(schema,"panel-fill-builder-select/1")||
       !timber_edit_revision(&j,geo_json_member(&j,0,"expectedRevision"),&revision)||
       !timber_edit_revision(&j,geo_json_member(&j,0,"generation"),&generation)||
       !geo_json_string(&j,geo_json_member(&j,0,"setKey"),key,sizeof key)||!geo_json_is_array(&j,array)){
        eng_bridge_error("SCHEMA","PF-6 select requires exact revision, setKey, generation and an explicit selected array");goto done;
    }
    if(!g_pf6_proposal||revision!=g_definition_revision||revision!=g_pf6_proposal->revision||
       generation!=g_pf6_proposal->generation||strcmp(key,g_pf6_proposal->key)||
       !world_definitions_equal(&g_world,g_pf6_proposal->basis)){
        pf6_pending_clear();eng_bridge_error("EXPIRED","PF-6 source, owner or generation changed; request new suggestions");goto done;
    }
    /* A well-formed selection for this generation supersedes its previous
     * candidate even when the replacement keys are refused. */
    pf6_pending_clear();
    int count=geo_json_size(&j,array);
    if(count>0&&!g_pf6_proposal->analysis_valid){eng_bridge_error("SELECTION","The complete PF-6 analysis failed; no partial suggestion can be selected");goto done;}
    if(count<0||(size_t)count>g_pf6_proposal->report.plan.count){eng_bridge_error("SELECTION","PF-6 selection exceeds the suggestion set");goto done;}
    selected=calloc(count?(size_t)count:1,sizeof *selected);if(!selected){eng_bridge_error("MEMORY","Cannot retain PF-6 selection");goto done;}
    for(int i=0;i<count;++i){
        int token=geo_json_at(&j,array,i);char candidate_key[65];
        if(!geo_json_string(&j,token,candidate_key,sizeof candidate_key)){eng_bridge_error("SELECTION","PF-6 keys must be exact suggestion strings");goto done;}
        const WoodR45Candidate *found=NULL;
        for(size_t k=0;k<g_pf6_proposal->report.plan.count;++k)
            if(!strcmp(g_pf6_proposal->report.plan.items[k].key,candidate_key)){found=&g_pf6_proposal->report.plan.items[k];break;}
        if(!found||!found->selectable||!found->valid){eng_bridge_error("SELECTION","Unknown, rejected or omitted PF-6 key cannot be selected");goto done;}
        for(int k=0;k<i;++k)if(!strcmp(selected[k],candidate_key)){eng_bridge_error("SELECTION","Duplicate PF-6 selected key");goto done;}
        selected[i]=j.tokens[token].string;
    }
    identity_drop_serials();g_engineering_error[0]=0;g_scene_last_error[0]=0;g_reference_issue_count=0;
    AppWorldCandidate *transaction=app_world_candidate_create(&g_world);
    if(!transaction){eng_bridge_error("MEMORY","Cannot allocate PF-6 selected candidate");goto done;}
    Pf6OuterCall call={0};call.proposal=g_pf6_proposal;call.before=&transaction->before;call.selected=selected;call.selected_count=(size_t)count;
    bool valid=app_world_candidate_evaluate(transaction,pf6_outer_evaluate,&call)==GEO_CANDIDATE_OK;
    if(valid&&!app_world_candidate_seal(transaction)){valid=false;eng_fail("I8: PF-6 candidate seal failed");}
    char error[512];snprintf(error,sizeof error,"%s",g_engineering_error[0]?g_engineering_error:call.report.error);
    char *before=pf6_scene_text(&transaction->before),*after=pf6_scene_text(&transaction->after);
    if(!before||!after){
        free(before);free(after);pf6_report_free(&call.report);app_world_candidate_destroy(transaction);
        eng_bridge_error("IO","Cannot disclose complete PF-6 candidate definitions");goto done;
    }
    bool no_op=valid&&world_definitions_equal(&transaction->before,&transaction->after);
    if(!no_op){
        char *label="panel-fill-builder";
        if(!reference_stage(transaction,&label,1,valid)){
            free(before);free(after);pf6_report_free(&call.report);app_world_candidate_destroy(transaction);
            eng_bridge_error("CAPACITY","Preview token capacity exhausted; restart the service");goto done;
        }
        g_preview.engineering_batch=true;g_preview.pf6_batch=true;
        g_pf6_pending.token=g_preview.token;g_pf6_pending.generation=g_pf6_proposal->generation;
        g_pf6_pending.report=call.report;memset(&call.report,0,sizeof call.report);
        memcpy(g_pf6_pending.created,call.created,sizeof call.created);
    }
    const Pf6Report *report=no_op?&call.report:&g_pf6_pending.report;
    printf("{\"ok\":true,\"preview\":{\"schema\":\"panel-fill-builder-preview/1\",\"valid\":%s,\"token\":",valid?"true":"false");
    if(no_op)fputs("null",stdout);else printf("%u",g_preview.token);
    printf(",\"revision\":\"%llu\",\"phase\":\"%s\",\"candidateIdsAreTemporary\":true,\"beforeScene\":",(unsigned long long)g_definition_revision,no_op?"NO_OP":"SELECTED");
    js_string(before);fputs(",\"afterScene\":",stdout);js_string(after);
    fputs(",\"intent\":",stdout);fputs(g_pf6_proposal->intent,stdout);
    fputs(",\"entries\":",stdout);pf6_json_plan(report,false);fputs(",\"omissions\":",stdout);pf6_json_plan(report,true);
    fputs(",\"createdDefinitions\":",stdout);pf6_json_handles(report,call.created,g_pf6_proposal,false);
    fputs(",\"reusedDefinitions\":",stdout);pf6_json_reused(report);
    fputs(",\"idMap\":null,\"dependencies\":{\"timbers\":",stdout);json_candidate_timbers(&transaction->before,&transaction->after,true);
    fputs(",\"guides\":",stdout);json_candidate_guides(&transaction->before,&transaction->after);
    fputs("},\"violations\":[",stdout);
    if(!valid){fputs("{\"code\":\"PF6_INVALID\",\"clause\":\"D45/R45/I8/I24\",\"message\":",stdout);js_string(error);putchar('}');}
    if(!no_op)for(size_t i=0;i<g_preview.issue_count;++i){
        const ReferenceIssue *issue=&g_preview.issues[i];
        printf("%s{\"timber\":%u,\"clause\":",!valid||i?",":"",issue->timber);js_string(issue->clause);
        fputs(",\"expected\":",stdout);js_string(issue->expected);fputs(",\"message\":",stdout);js_string(issue->actual);putchar('}');
    }
    fputs("]}}\n",stdout);
    free(before);free(after);pf6_report_free(&call.report);if(no_op)app_world_candidate_destroy(transaction);
done:free(selected);geo_json_free(&j);free(text);
}
static void cmd_pf6_confirm(const char *arg)
{
    uint32_t token;identity_drop_serials();
    if(!arg||!parse_u32(arg,&token)||!g_preview.ready||!g_preview.pf6_batch||!g_preview.valid||
       token!=g_preview.token||token!=g_pf6_pending.token||!g_pf6_proposal||
       g_pf6_pending.generation!=g_pf6_proposal->generation){eng_bridge_error("TOKEN","PF-6 requires its current selected candidate token");return;}
    AppWorldCandidate *candidate=g_preview.transaction;
    if(g_history.grouping||g_preview.revision!=g_definition_revision||!app_world_candidate_current(candidate,&g_world)){
        pf6_pending_clear();eng_bridge_error("EXPIRED","PF-6 candidate changed; select against fresh suggestions");return;
    }
    if(!assembly_versions_immutable(&candidate->before,&candidate->after)||!app_world_candidate_revalidate(candidate,&g_world)){
        pf6_pending_clear();eng_bridge_error("INVALID",g_revalidate_error[0]?g_revalidate_error:g_engineering_error);return;
    }
    bool changed=!world_definitions_equal(&g_world,&candidate->after)||g_identity_pending_count!=0;
    uint64_t before=g_definition_revision;
    if(changed&&g_definition_revision==UINT64_MAX){
        identity_drop_serials();pf6_pending_clear();eng_bridge_error("CAPACITY","Definition revision capacity exhausted; World unchanged");return;
    }
    if(changed)history_record(&g_world);
    if(!app_world_candidate_publish(candidate,&g_world,true)){
        if(changed)history_unrecord();identity_drop_serials();pf6_pending_clear();
        eng_bridge_error("EXPIRED","PF-6 publication seal changed; World unchanged");return;
    }
    if(changed){identity_commit_serials();++g_definition_revision;}else identity_drop_serials();
    g_preview.ready=false;app_world_candidate_clear_stagger(candidate);
    printf("{\"ok\":true,\"schema\":\"panel-fill-builder-receipt/1\",\"history_changed\":%s,\"before_revision\":\"%llu\",\"revision\":\"%llu\",\"transaction_id\":%u,\"actionReceipt\":{\"schema\":\"panel-fill-builder-actions/1\",\"generation\":\"%llu\",\"idMap\":",
        changed?"true":"false",(unsigned long long)before,(unsigned long long)g_definition_revision,token,(unsigned long long)g_pf6_pending.generation);
    pf6_json_handles(&g_pf6_pending.report,g_pf6_pending.created,g_pf6_proposal,true);
    fputs(",\"reusedDefinitions\":",stdout);pf6_json_reused(&g_pf6_pending.report);
    fputs("},\"definition_sha256\":",stdout);char hash[65];if(eng_definition_hash(&g_world,hash))js_string(hash);else fputs("null",stdout);
    fputs("}\n",stdout);pf6_pending_clear();
}
static void cmd_pf6_cancel(const char *arg)
{
    uint32_t token;if(!arg||!parse_u32(arg,&token)){eng_bridge_error("TOKEN","PF-6 cancel requires its selected token");return;}
    bool cancelled=g_preview.ready&&g_preview.pf6_batch&&token==g_preview.token&&token==g_pf6_pending.token;
    if(cancelled){identity_drop_serials();pf6_pending_clear();}
    printf("{\"ok\":true,\"cancelled\":%s,\"revision\":\"%llu\"}\n",cancelled?"true":"false",(unsigned long long)g_definition_revision);
}
