/* Reuse the original independent host/geometry fixture, but substitute the
 * actual typed values returned to W. The real graph/provider still executes. */
#define main assembly_legacy_fixture_main
#include "geo261_assembly_sources_harness.c"
#undef main

/* `later` replaces `text` once the entry has been returned `later_after` times:
 * K may answer the same reference differently inside one candidate. */
typedef struct {WoodAssemblySourceKind kind;uint32_t id,version,sub;char text[ASM_RECORD_MAX+96];int malformed;unsigned hits;
    bool bay;AsmIdentity identity;char later[ASM_RECORD_MAX+96];unsigned later_after;} Authority;
static Authority changes[8];static size_t change_count;static GeoEvalContext *changed_graph;
static bool wood_assembly_bay_source_decode(const GeoSourceRef *,WoodAssemblySourceKind *,uint32_t *,AsmIdentity *);
static GeoSourceStatus authority_source(GeoEvalContext *graph,GeoSourceRef ref,GeoDependencyKind relation,GeoSourceValue *out)
{
    GeoSourceStatus result=geo_eval_source(graph,ref,relation,out);WoodAssemblySourceKind kind;uint32_t id,version=0,sub=0;AsmIdentity identity={0};bool bay=false;
    if(result!=GEO_SOURCE_OK||graph!=changed_graph||ref.provider!=AS_ASSEMBLY)return result;
    if(!wood_assembly_source_decode(&ref,&kind,&id,&version,&sub)){if(!wood_assembly_bay_source_decode(&ref,&kind,&id,&identity))return result;bay=true;}
    for(size_t i=0;i<change_count;++i){Authority *a=&changes[i];if(kind!=a->kind||id!=a->id||version!=a->version||sub!=a->sub||bay!=a->bay||(bay&&!wood_assembly_identity_equal(identity,a->identity)))continue;++a->hits;
        const char *text=a->later_after&&a->hits>a->later_after?a->later:a->text;
        out->as.definition.content=text;out->as.definition.content_size=strlen(text);
        if(a->malformed==1)out->as.definition.schema="wrong.schema/1";
        if(a->malformed==2)out->as.definition.content_size+=1;
    }return result;
}
#define geo_eval_source authority_source
#include "assembly_sources.c"
#undef geo_eval_source

static bool inject(Fixture *f,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,uint32_t sub,const char *name)
{
    if(change_count==8)return false;Authority *a=&changes[change_count++];memset(a,0,sizeof *a);a->kind=kind;a->id=id;a->version=version;a->sub=sub;changed_graph=f->graph;
    GeoJson j;bool ok=geo_json_parse(&j,fixture_text)&&geo_json_canonical(&j,geo_json_member(&j,geo_json_member(&j,0,"authority"),name),a->text,sizeof a->text);geo_json_free(&j);return ok;
}
static void clear_changes(void){change_count=0;changed_graph=NULL;memset(changes,0,sizeof changes);}
static bool rebuild(Fixture *f){char error[512]="";return wood_assembly_rebuild(&f->context,error,sizeof error);}
static bool authored_equal(Fixture *f,const AssemblyState *before)
{
    AssemblyState *copy=malloc(sizeof *copy);if(!copy)return false;*copy=f->state;
    for(size_t i=0;i<copy->binding_count;++i)copy->bindings[i].complete=before->bindings[i].complete;
    bool same=!memcmp(copy,before,sizeof *copy);free(copy);return same;
}
static int binding_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,9,0,0,"binding"),"binding-authority-setup");AssemblyState *before=malloc(sizeof *before);CHECK(before,"snapshot-allocation");*before=f->state;
    CHECK(rebuild(f)&&wood_assembly_generation_prepare(&f->context)&&item(f,1)->fact.width==35&&item(f,2)->fact.width==35&&item(f,3)->fact.width==40&&changes[0].hits>0,"returned-binding-controls-dimensions");
    CHECK(authored_equal(f,before),"binding-authoring-is-not-overwritten");free(before);dispose(f,false);clear_changes();return 0;
}
static int slot_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,9,0,17,"slot"),"slot-authority-setup");
    CHECK(rebuild(f)&&wood_assembly_generation_prepare(&f->context)&&item(f,1)->fact.width==37&&item(f,2)->fact.width==37,"returned-slot-controls-dimensions");dispose(f,true);clear_changes();
    f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,9,0,17,"slotPolicy"),"slot-policy-setup");
    CHECK(rebuild(f)&&!wood_assembly_generation_prepare(&f->context)&&f->write_count==0&&strstr(f->error,"generation needs complete A contact"),"returned-slot-controls-contact-policy");dispose(f,false);clear_changes();return 0;
}
static int rule_authority_case(void)
{
    Fixture *f=fixture(false),*plain=fixture(false);CHECK(f&&plain&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,8,1,0,"rule"),"rule-authority-setup");
    GeoJson j;AsmRuleVersion rule;CHECK(geo_json_parse(&j,changes[0].text)&&wood_assembly_rule_parse(&plain->context,&j,0,&rule),"plain-returned-rule");geo_json_free(&j);plain->state.rules[0]=rule;
    CHECK(!rebuild(f)&&!rebuild(plain)&&!strcmp(f->error,plain->error)&&strstr(f->error,"explicitly map every fixed rule slot")&&f->parameter_calls==0,"returned-rule-controls-original-binding-policy");
    CHECK(strcmp(f->state.rules[0].content,changes[0].text)&&f->state.rule_count==2,"rule-authoring-is-not-overwritten");dispose(f,false);dispose(plain,true);clear_changes();return 0;
}
static int instance_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,2,0,0,"instance"),"instance-authority-setup");
    CHECK(rebuild(f)&&!wood_assembly_generation_prepare(&f->context)&&f->write_count==1&&f->writes[0]==1&&strstr(f->error,"matching same-surface guide"),"returned-instance-controls-guide-and-partial-order");
    CHECK(f->state.instances[0].guide[1]==2&&!item(f,2)->fact.placed&&!item(f,3)->fact.placed,"instance-authoring-and-later-writes-untouched");dispose(f,true);clear_changes();return 0;
}
static void fourth_member(Fixture *f){f->items[f->count++]=(Item){.id=4};}
static int mapping_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,2,0,0,"mapping"),"mapping-authority-setup");fourth_member(f);bool owned=false;
    CHECK(wood_assembly_sources_owned(f->sources,4,&owned)&&owned&&wood_assembly_sources_owned(f->sources,1,&owned)&&!owned&&f->parameter_calls==0&&f->named_calls==0&&f->guide_calls==0&&f->footprint_calls==0,"returned-mapping-controls-definition-only-ownership");
    CHECK(rebuild(f)&&wood_assembly_generation_prepare(&f->context)&&f->write_count==3&&!memcmp(f->writes,(uint32_t[]){4,2,3},sizeof(uint32_t)*3)&&item(f,3)->definition.between[0]==4&&!item(f,1)->fact.placed,"returned-mapping-controls-targets-and-supports");
    GeoCoord a,b;CHECK(wood_assembly_sources_owned_dimensions(f->sources,4,&a,&b)&&a==27&&b==33&&f->state.instances[0].timber[0]==1,"returned-mapping-controls-owned-dimensions");dispose(f,false);clear_changes();return 0;
}
static int generated_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,2,0,11,"generated11")&&inject(f,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,2,0,37,"generated37")&&inject(f,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,2,0,89,"generated89"),"generated-authority-setup");fourth_member(f);
    CHECK(rebuild(f)&&wood_assembly_generation_prepare(&f->context)&&f->write_count==3&&!memcmp(f->writes,(uint32_t[]){4,2,3},sizeof(uint32_t)*3)&&item(f,3)->definition.between[0]==4,"returned-generated-definition-controls-write-target");
    bool owned=false;CHECK(wood_assembly_sources_owned(f->sources,4,&owned)&&owned&&changes[0].hits&&changes[1].hits&&changes[2].hits,"returned-generated-definition-controls-ownership");dispose(f,true);clear_changes();return 0;
}
static int result_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_GENERATED,2,0,11,"result"),"result-authority-setup");fourth_member(f);WoodAssemblyDefinition d;
    CHECK(rebuild(f)&&wood_assembly_sources_generated(f->sources,2,11,&d)&&d.width==43&&d.depth==47&&d.guide_id==2&&d.timber_id==4&&d.between[0]==91&&d.between[1]==90,"returned-generated-result-controls-every-field");dispose(f,false);clear_changes();return 0;
}
static int check_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_BINDING_CHECK,9,0,0,"bindingResult"),"binding-result-setup");
    CHECK(rebuild(f)&&!f->state.bindings[0].complete&&!wood_assembly_generation_prepare(&f->context)&&f->write_count==0,"returned-binding-result-controls-complete-cache");dispose(f,true);clear_changes();
    f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_INSTANCE_CHECK,2,0,0,"checkResult"),"check-result-setup");
    CHECK(rebuild(f)&&wood_assembly_generation_prepare(&f->context)&&!wood_assembly_generation_check(&f->context)&&changes[0].hits>0,"returned-check-result-controls-validation");dispose(f,false);clear_changes();return 0;
}
static int malformed_authority_case(void)
{
    const WoodAssemblySourceKind kinds[]={WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,WOOD_ASSEMBLY_SOURCE_INSTANCE_DEFINITION,WOOD_ASSEMBLY_SOURCE_MAPPING_DEFINITION,WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION,WOOD_ASSEMBLY_SOURCE_GENERATED};
    for(size_t k=0;k<sizeof kinds/sizeof kinds[0];++k)for(int mode=0;mode<4;++mode){Fixture *f=fixture(true);CHECK(f&&attach(f),"malformed-authority-setup");AssemblyState *before=malloc(sizeof *before);CHECK(before,"malformed-snapshot");*before=f->state;
        WoodAssemblySourceKind kind=kinds[k];uint32_t id=kind==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION?8:kind==WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION?9:2;
        uint32_t sub=kind==WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION?17:kind==WOOD_ASSEMBLY_SOURCE_GENERATED_DEFINITION||kind==WOOD_ASSEMBLY_SOURCE_GENERATED?11:0;
        CHECK(inject(f,kind,id,kind==WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION?1:0,sub,"result"),"malformed-injection");changes[0].malformed=mode;if(mode==0)strcpy(changes[0].text,"{\"broken\":");
        if(mode==3){memmove(changes[0].text+1,changes[0].text,strlen(changes[0].text)+1);changes[0].text[0]=' ';}
        WoodAssemblyDefinition out,saved;memset(&out,0x5a,sizeof out);saved=out;
        CHECK(!wood_assembly_sources_generated(f->sources,2,11,&out)&&!memcmp(&out,&saved,sizeof out)&&authored_equal(f,before)&&f->write_count==0,"malformed-returned-definition-is-atomic");free(before);dispose(f,k%2!=0);clear_changes();}
    for(int axis=0;axis<2;++axis){Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_GENERATED,2,0,11,"result"),"result-bound-setup");GeoJson j;
        CHECK(geo_json_parse(&j,changes[0].text),"result-bound-json");j.tokens[geo_json_member(&j,0,axis?"depth":"width")].number=GEO_COORD_LIMIT;
        CHECK(geo_json_canonical(&j,0,changes[0].text,sizeof changes[0].text),"result-bound-canonical");WoodAssemblyDefinition out;
        CHECK(wood_assembly_sources_generated(f->sources,2,11,&out)&&(axis?out.depth:out.width)==GEO_COORD_LIMIT,"returned-result-accepts-exact-coordinate-limit");
        j.tokens[geo_json_member(&j,0,axis?"depth":"width")].number=GEO_COORD_LIMIT+1;CHECK(geo_json_canonical(&j,0,changes[0].text,sizeof changes[0].text),"result-overflow-canonical");geo_json_free(&j);WoodAssemblyDefinition saved=out;
        CHECK(!wood_assembly_sources_generated(f->sources,2,11,&out)&&!memcmp(&out,&saved,sizeof out)&&f->write_count==0,"returned-result-rejects-overflow-atomically");dispose(f,axis!=0);clear_changes();}
    return 0;
}
static int dormant_authority_case(void)
{
    Fixture *f=fixture(true);CHECK(f&&attach(f)&&inject(f,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,10,0,0,"dormant"),"dormant-authority-setup");
    CHECK(wood_assembly_sources_definitions(f->sources)&&f->parameter_calls==0&&f->named_calls==0&&f->guide_calls==0&&f->footprint_calls==0&&f->pose_calls==0,"dormant-definitions-do-not-force-policy-or-geometry");
    CHECK(assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_DEFINITION,10,0,17)!=SIZE_MAX&&assembly_index(f,WOOD_ASSEMBLY_SOURCE_SLOT_A,10,0,17)==SIZE_MAX&&changes[0].hits>0,"dormant-returned-slots-are-enumerated");dispose(f,true);clear_changes();return 0;
}
/* Issue 381: a repeated-bay record that K returns unchanged is not parsed
 * again. One bay instance with three owned identities; every ownership query
 * asks K for each identity's bay-generated definition. */
static unsigned parse_calls;
static bool counting_parse(void *user,GeoJson *j,const char *text){(void)user;++parse_calls;return geo_json_parse(j,text);}
static bool authority_text(const char *name,char *out,size_t capacity)
{GeoJson j;bool ok=geo_json_parse(&j,fixture_text)&&geo_json_canonical(&j,geo_json_member(&j,geo_json_member(&j,0,"authority"),name),out,capacity);geo_json_free(&j);return ok;}
static Fixture *bay_fixture(void)
{
    Fixture *f=fixture(false);if(!f)return NULL;f->context.json_parse=counting_parse;GeoJson j;AsmInstance *a=&f->state.instances[f->state.instance_count];
    bool ok=geo_json_parse(&j,fixture_text)&&wood_assembly_instance_definition_parse(&f->context,&j,geo_json_member(&j,geo_json_member(&j,0,"authority"),"bay"),a);geo_json_free(&j);
    if(!ok||!a->bay_repeat||a->mapping_count!=3)return NULL;++f->state.instance_count;f->state.generation_required=f->state.bay_required=true;return f;
}
static bool inject_bay(Fixture *f,uint32_t key,const char *name)
{
    if(change_count==8)return false;Authority *a=&changes[change_count++];memset(a,0,sizeof *a);a->kind=WOOD_ASSEMBLY_SOURCE_BAY_GENERATED_DEFINITION;a->id=5;a->bay=true;a->identity=(AsmIdentity){ASM_ID_PRIMARY,key,0,0};changed_graph=f->graph;
    return authority_text(name,a->text,sizeof a->text);
}
static bool owned_by_bay(Fixture *f,uint32_t timber,bool expected)
{bool owned=!expected;return wood_assembly_sources_owned(f->sources,timber,&owned)&&owned==expected;}
static int bay_authority_case(void)
{
    Fixture *f=bay_fixture();CHECK(f&&attach(f),"bay-authority-setup");
    CHECK(owned_by_bay(f,1,true)&&owned_by_bay(f,2,true)&&owned_by_bay(f,3,true)&&owned_by_bay(f,4,false)&&f->parameter_calls==0&&f->named_calls==0&&f->guide_calls==0&&f->footprint_calls==0&&f->pose_calls==0,"bay-record-is-definition-only-ownership");
    CHECK(inject_bay(f,1,"bayGeneratedA")&&strlen(changes[0].text)>0,"bay-injection");
    CHECK(owned_by_bay(f,4,true)&&owned_by_bay(f,1,false)&&owned_by_bay(f,2,true)&&changes[0].hits==3,"returned-bay-definition-controls-ownership");
    /* Same bytes again: K is still asked on every use, and the answer stands. */
    unsigned asked=changes[0].hits;CHECK(owned_by_bay(f,4,true)&&changes[0].hits==asked+1,"unchanged-bay-definition-is-requested-again");
    /* K now returns another record of the same length for the same reference. */
    CHECK(authority_text("bayGeneratedB",changes[0].text,sizeof changes[0].text),"bay-second-record");
    CHECK(owned_by_bay(f,5,true)&&owned_by_bay(f,4,false),"changed-returned-bay-definition-is-decoded-again");
    /* The first record again, then with a wrong schema and with one extra byte. */
    CHECK(authority_text("bayGeneratedA",changes[0].text,sizeof changes[0].text)&&owned_by_bay(f,4,true),"bay-first-record-again");
    bool owned=true;changes[0].malformed=1;CHECK(!wood_assembly_sources_owned(f->sources,4,&owned)&&strstr(f->error,"I40: invalid assembly source definition"),"wrong-schema-returned-bay-definition-is-rejected");
    changes[0].malformed=2;f->error[0]=0;CHECK(!wood_assembly_sources_owned(f->sources,4,&owned)&&strstr(f->error,"I40: invalid assembly source definition"),"oversized-returned-bay-definition-is-rejected");
    changes[0].malformed=0;CHECK(owned_by_bay(f,4,true),"bay-record-recovers-after-malformed-returns");dispose(f,false);clear_changes();return 0;
}
static bool inject_same(Fixture *f,WoodAssemblySourceKind kind,uint32_t id,uint32_t version,const char *text)
{
    if(change_count==8||strlen(text)>=sizeof changes[0].text)return false;Authority *a=&changes[change_count++];memset(a,0,sizeof *a);a->kind=kind;a->id=id;a->version=version;changed_graph=f->graph;
    strcpy(a->text,text);return true;
}
static int bay_reuse_case(void)
{
    /* The binding and rule entries return the authored bytes; they only count requests. */
    Fixture *f=bay_fixture(),*plain=bay_fixture();CHECK(f&&plain&&attach(f)&&inject_same(f,WOOD_ASSEMBLY_SOURCE_BINDING_DEFINITION,9,0,wood_assembly_binding(&plain->context,9)->content)&&
        inject_same(f,WOOD_ASSEMBLY_SOURCE_RULE_DEFINITION,8,1,wood_assembly_rule(&plain->context,8,1)->content),"bay-reuse-setup");
    unsigned parses[3],binding[3],rule[3];
    for(int k=0;k<3;++k){parse_calls=0;CHECK(owned_by_bay(f,1,true),"bay-reuse-query");parses[k]=parse_calls;binding[k]=changes[0].hits;rule[k]=changes[1].hits;}
    /* Per query: once for the instance and once for each of three identities;
     * the rule also directly after its binding. */
    CHECK(binding[2]-binding[1]==4&&rule[2]-rule[1]==8,"reused-bay-record-requests-binding-and-rule-again");
    /* A query reads the instance (7 parses) and three identities. An unchanged
     * record costs its binding and rule (3); a decode adds the record and the
     * rule topology (5). The first query decodes all three. */
    CHECK(parses[1]==16&&parses[2]==16&&parses[0]>=22,"unchanged-returned-bay-definition-is-not-parsed-again");
    /* Scribble on the candidate copy: the returned binding and rule must restore it. */
    AsmBinding *copy=wood_assembly_binding(&f->sources->context,9);AsmRuleVersion *version=(AsmRuleVersion *)wood_assembly_rule(&f->sources->context,8,1);CHECK(copy&&version,"bay-candidate-copies");
    strcpy(copy->name,"scribbled");strcpy(version->name,"scribbled");
    CHECK(owned_by_bay(f,1,true)&&!strcmp(copy->name,"unequal")&&!strcmp(version->name,"single bay"),"reused-bay-record-restores-returned-binding-and-rule");
    /* From now on K returns another rule to the bay-record requests of one query:
     * the first two rule requests of a query belong to the instance definition. */
    CHECK(authority_text("rule",changes[1].later,sizeof changes[1].later)&&strcmp(changes[1].later,changes[1].text),"bay-later-rule");
    changes[1].later_after=changes[1].hits+2;bool owned=true;f->error[0]=0;
    CHECK(!wood_assembly_sources_owned(f->sources,1,&owned)&&strstr(f->error,"changed fixed rule fingerprint/version"),"reused-bay-record-requires-the-fixed-rule");
    dispose(f,true);dispose(plain,true);clear_changes();return 0;
}
static int baseline_authority_case(void)
{int r=graph_case();if(r)return r;r=definitions_case();if(r)return r;r=diagnostic_case();if(r)return r;r=partial_case();if(r)return r;return lifetime_case();}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;FILE *file=fopen(argv[2],"rb");if(!file)return 2;fseek(file,0,SEEK_END);long size=ftell(file);rewind(file);fixture_text=malloc((size_t)size+1);if(!fixture_text){fclose(file);return 2;}if(fread(fixture_text,1,(size_t)size,file)!=(size_t)size){fclose(file);return 2;}fclose(file);fixture_text[size]=0;
    int result=!strcmp(argv[1],"binding")?binding_authority_case():!strcmp(argv[1],"slot")?slot_authority_case():!strcmp(argv[1],"rule")?rule_authority_case():!strcmp(argv[1],"instance")?instance_authority_case():!strcmp(argv[1],"mapping")?mapping_authority_case():!strcmp(argv[1],"generated")?generated_authority_case():!strcmp(argv[1],"result")?result_authority_case():!strcmp(argv[1],"check")?check_authority_case():!strcmp(argv[1],"malformed")?malformed_authority_case():!strcmp(argv[1],"dormant")?dormant_authority_case():!strcmp(argv[1],"bay")?bay_authority_case():!strcmp(argv[1],"bayreuse")?bay_reuse_case():!strcmp(argv[1],"baseline")?baseline_authority_case():2;
    free(fixture_text);return result;
}
