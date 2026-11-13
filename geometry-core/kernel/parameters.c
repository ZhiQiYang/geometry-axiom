#ifndef GEOMETRY_KERNEL_PARAMETERS_IMPLEMENTATION
#define GEOMETRY_KERNEL_PARAMETERS_IMPLEMENTATION
#include "parameters.h"
#include "internal/parameter_store.h"
#include "codec.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <limits.h>

static bool geo_parameter_error(GeoParameterError *e,GeoParameterStatus status,uint32_t card,uint32_t field)
{if(e){e->status=status;e->source=(GeoParameterRef){true,card,field};}return false;}
static bool geo_parameter_exact(GeoParameterError *e,GeoExactStatus status)
{if(status==GEO_EXACT_OK)return true;if(e)e->exact=status;return geo_parameter_error(e,GEO_PARAMETER_EXACT,0,0);}
GeoParameterStore *geo_parameters_create(void){return calloc(1,sizeof(GeoParameterStore));}
GeoParameterStore *geo_parameters_clone(const GeoParameterStore *s)
{if(!s)return NULL;GeoParameterStore *copy=malloc(sizeof *copy);if(copy)*copy=*s;return copy;}
void geo_parameters_destroy(GeoParameterStore *s){free(s);}
bool geo_parameters_equal(const GeoParameterStore *a,const GeoParameterStore *b)
{return a&&b&&!memcmp(a,b,sizeof *a);}
size_t geo_parameters_card_count(const GeoParameterStore *s){return s?s->card_count:0;}
size_t geo_parameters_field_count(const GeoParameterStore *s){return s?s->field_count:0;}
const GeoParameterCard *geo_parameters_cards(const GeoParameterStore *s){return s?s->cards:NULL;}
const GeoParameterField *geo_parameters_fields(const GeoParameterStore *s){return s?s->fields:NULL;}
const GeoParameterCard *geo_parameters_find(const GeoParameterStore *s,uint32_t id)
{for(size_t i=0;i<s->card_count;++i)if(s->cards[i].id==id)return &s->cards[i];return NULL;}
int geo_parameters_field_index(const GeoParameterStore *s,uint32_t id,uint32_t field)
{for(size_t i=0;i<s->field_count;++i)if(s->fields[i].parameter_id==id&&s->fields[i].id==field)return (int)i;return -1;}
bool geo_parameters_dimension_value(const GeoParameterStore *s,GeoParameterRef ref,GeoQuantity *out,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    int i=geo_parameters_field_index(s,ref.parameter_id,ref.field_id);
    if(i<0)return geo_parameter_error(error,GEO_PARAMETER_MISSING_FIELD,ref.parameter_id,ref.field_id);
    const GeoParameterField *f=&s->fields[i];
    if(f->type!=GEO_PARAMETER_DIMENSION)return geo_parameter_error(error,GEO_PARAMETER_NOT_DIMENSION,ref.parameter_id,ref.field_id);
    *out=f->value;return true;
}
bool geo_parameters_coordinate(const GeoParameterStore *s,GeoParameterRef ref,GeoCoord *out,GeoParameterError *error)
{
    GeoQuantity value;if(!geo_parameters_dimension_value(s,ref,&value,error))return false;
    if(value.den!=1||!geo_coord_in_range(value.num)){
        if(error)error->quantity=value;
        return geo_parameter_error(error,GEO_PARAMETER_COORDINATE,ref.parameter_id,ref.field_id);
    }
    *out=value.num;return true;
}
static bool geo_parameter_integer(const char *s,int64_t *value,GeoParameterError *e)
{
    char *end=NULL;errno=0;long long n=s?strtoll(s,&end,10):0;
    if(!s||end==s||*end||errno==ERANGE||n==INT64_MIN)return geo_parameter_error(e,GEO_PARAMETER_INTEGER,0,0);
    *value=(int64_t)n;return true;
}
static bool geo_parameter_u32(GeoJson *j,int t,uint32_t *out)
{int64_t v;if(!geo_json_integer(j,t,&v)||v<0||v>UINT32_MAX)return false;*out=(uint32_t)v;return true;}
static bool geo_parameter_normal(GeoQuantity *value,GeoParameterError *e)
{GeoQuantity out=*value;if(!geo_parameter_exact(e,geo_quantity_normalize(*value,&out)))return false;*value=out;return true;}
static bool geo_parameter_binary(const char *op,GeoQuantity a,GeoQuantity b,GeoQuantity *out,GeoParameterError *e)
{
    GeoExactOperation operation;
    if(!strcmp(op,"add"))operation=GEO_EXACT_ADD;else if(!strcmp(op,"sub"))operation=GEO_EXACT_SUBTRACT;
    else if(!strcmp(op,"mul"))operation=GEO_EXACT_MULTIPLY;else operation=GEO_EXACT_DIVIDE;
    return geo_parameter_exact(e,geo_quantity_binary(operation,a,b,out));
}

struct GeoParameterEvaluation {
    GeoParameterStore *store;GeoParameterError *error,issue;
    GeoParameterResolve resolve;void *resolver_state;
    unsigned char marks[GEO_PARAMETER_FIELD_MAX],fdepth[GEO_PARAMETER_FIELD_MAX];
    int depth,maxref;uint32_t path_card[GEO_PARAMETER_DEPTH_MAX],path_field[GEO_PARAMETER_DEPTH_MAX];
};
typedef GeoParameterEvaluation GeoParameterEval;
static bool geo_parameter_eval_field(GeoParameterEval *e,int index);
static bool geo_parameter_eval_ast(GeoParameterEval *e,GeoJson *j,int t,int depth,int *nodes,GeoQuantity *out)
{
    if(depth>32||++*nodes>GEO_PARAMETER_NODE_MAX)return geo_parameter_error(e->error,GEO_PARAMETER_AST_CAPACITY,0,0);
    char op[16];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return geo_parameter_error(e->error,GEO_PARAMETER_AST_OPERATION_MISSING,0,0);
    if(!strcmp(op,"literal")){
        char num[40],den[40],unit[8];
        if(!geo_json_keys(j,t,"op,num,den,unit","")||!geo_json_string(j,geo_json_member(j,t,"num"),num,sizeof num)||!geo_json_string(j,geo_json_member(j,t,"den"),den,sizeof den)||!geo_json_string(j,geo_json_member(j,t,"unit"),unit,sizeof unit))return geo_parameter_error(e->error,GEO_PARAMETER_AST_LITERAL,0,0);
        if(!geo_parameter_integer(num,&out->num,e->error)||!geo_parameter_integer(den,&out->den,e->error))return false;
        if(out->den<=0)return geo_parameter_error(e->error,GEO_PARAMETER_DENOMINATOR,0,0);
        if(strcmp(unit,"mm")&&strcmp(unit,"1"))return geo_parameter_error(e->error,GEO_PARAMETER_LITERAL_UNIT,0,0);
        out->unit=!strcmp(unit,"mm");return geo_parameter_normal(out,e->error);
    }
    if(!strcmp(op,"ref")){
        uint32_t id,field;if(!geo_json_keys(j,t,"op,parameterId,fieldId","")||!geo_parameter_u32(j,geo_json_member(j,t,"parameterId"),&id)||!geo_parameter_u32(j,geo_json_member(j,t,"fieldId"),&field))return geo_parameter_error(e->error,GEO_PARAMETER_AST_REFERENCE,0,0);
        int i=geo_parameters_field_index(e->store,id,field);if(i<0)return geo_parameter_error(e->error,GEO_PARAMETER_MISSING_FIELD,id,field);
        if(e->resolve){
            GeoParameterStatus status=e->resolve(e->resolver_state,(GeoParameterRef){true,id,field},out);
            if(status!=GEO_PARAMETER_OK){
                if(e->error->status==GEO_PARAMETER_OK)geo_parameter_error(e->error,status,id,field);
                return false;
            }
        }else{
            if(!geo_parameter_eval_field(e,i))return false;
            *out=e->store->fields[i].value;
        }
        if(e->fdepth[i]>e->maxref)e->maxref=e->fdepth[i];  /* also on cache hits: the depth comes from the field, not the stack */
        return true;
    }
    bool neg=!strcmp(op,"neg");if(!neg&&strcmp(op,"add")&&strcmp(op,"sub")&&strcmp(op,"mul")&&strcmp(op,"div"))return geo_parameter_error(e->error,GEO_PARAMETER_UNSUPPORTED_OPERATION,0,0);
    if(!geo_json_keys(j,t,neg?"op,left":"op,left,right",""))return geo_parameter_error(e->error,GEO_PARAMETER_AST_ARITHMETIC,0,0);
    GeoQuantity a,b;if(!geo_parameter_eval_ast(e,j,geo_json_member(j,t,"left"),depth+1,nodes,&a))return false;
    if(neg){*out=a;out->num=-out->num;return true;}
    if(!geo_parameter_eval_ast(e,j,geo_json_member(j,t,"right"),depth+1,nodes,&b))return false;
    return geo_parameter_binary(op,a,b,out,e->error);
}
static bool geo_parameter_eval_field(GeoParameterEval *e,int index)
{
    GeoParameterField *f=&e->store->fields[index];
    if(e->marks[index]==2)return true;  /* cached value; its dependency depth is e->fdepth[index] */
    if(e->marks[index]==1)return geo_parameter_error(e->error,GEO_PARAMETER_CYCLE,f->parameter_id,f->id);
    if(e->depth==GEO_PARAMETER_DEPTH_MAX)return geo_parameter_error(e->error,GEO_PARAMETER_DEPTH,0,0);
    e->marks[index]=1;e->path_card[e->depth]=f->parameter_id;e->path_field[e->depth++]=f->id;
    int outer_maxref=e->maxref;e->maxref=0;
    GeoJson j;bool ok=geo_json_parse_n(&j,f->expression,strlen(f->expression));GeoQuantity value={0,1,0};int nodes=0;
    if(ok)ok=geo_parameter_eval_ast(e,&j,0,0,&nodes,&value);else (snprintf(e->error->detail,sizeof e->error->detail,"%s",j.error),geo_parameter_error(e->error,GEO_PARAMETER_JSON,0,0));
    geo_json_free(&j);
    if(ok&&value.unit!=(f->type==0))ok=geo_parameter_error(e->error,GEO_PARAMETER_FIELD_UNIT,0,0);
    if(ok&&f->type==1&&(value.num<0||value.den!=1))ok=geo_parameter_error(e->error,GEO_PARAMETER_COUNT_VALUE,0,0);
    --e->depth;
    int own_depth=e->maxref+1;e->maxref=outer_maxref;
    if(ok&&own_depth>GEO_PARAMETER_DEPTH_MAX)ok=geo_parameter_error(e->error,GEO_PARAMETER_DEPTH,0,0);
    if(!ok){if(e->error->trace_count<GEO_PARAMETER_DEPTH_MAX)e->error->trace[e->error->trace_count++]=(GeoParameterRef){true,f->parameter_id,f->id};return false;}
    /* A cache write owns the quantity members, not the surrounding bytes.
     * Copying a temporary struct can import indeterminate padding into the
     * candidate and break byte-exact clone/rollback comparisons. */
    memcpy(&f->value.num,&value.num,sizeof value.num);
    memcpy(&f->value.den,&value.den,sizeof value.den);
    memcpy(&f->value.unit,&value.unit,sizeof value.unit);
    e->fdepth[index]=(unsigned char)own_depth;e->marks[index]=2;return true;
}
GeoParameterEvaluation *geo_parameter_evaluation_create(GeoParameterStore *store,GeoParameterResolve resolve,void *state)
{
    if(!store)return NULL;
    GeoParameterEvaluation *e=calloc(1,sizeof *e);
    if(e){e->store=store;e->error=&e->issue;e->resolve=resolve;e->resolver_state=state;}
    return e;
}
void geo_parameter_evaluation_destroy(GeoParameterEvaluation *e){free(e);}
const GeoParameterError *geo_parameter_evaluation_error(const GeoParameterEvaluation *e)
{return e?e->error:NULL;}
bool geo_parameter_evaluation_field(GeoParameterEvaluation *e,GeoParameterRef ref,GeoQuantity *out)
{
    if(!e||!out)return false;
    int index=geo_parameters_field_index(e->store,ref.parameter_id,ref.field_id);
    if(index<0)return geo_parameter_error(e->error,GEO_PARAMETER_MISSING_FIELD,ref.parameter_id,ref.field_id);
    if(!geo_parameter_eval_field(e,index))return false;
    *out=e->store->fields[index].value;return true;
}
bool geo_parameters_rebuild(GeoParameterStore *store,GeoParameterError *error)
{
    GeoParameterError local;if(!error)error=&local;memset(error,0,sizeof *error);
    GeoParameterEvaluation *e=geo_parameter_evaluation_create(store,NULL,NULL);
    if(!e)return geo_parameter_error(error,GEO_PARAMETER_MEMORY,0,0);
    bool ok=true;
    for(size_t i=0;i<store->field_count&&ok;++i)ok=geo_parameter_eval_field(e,(int)i);
    *error=*e->error;geo_parameter_evaluation_destroy(e);return ok;
}
bool geo_parameters_evaluate_field(GeoParameterStore *store,GeoParameterRef ref,GeoParameterError *error)
{
    GeoParameterError local;if(!error)error=&local;memset(error,0,sizeof *error);
    if(!store)return geo_parameter_error(error,GEO_PARAMETER_INVALID_DEFINITION,ref.parameter_id,ref.field_id);
    int index=geo_parameters_field_index(store,ref.parameter_id,ref.field_id);
    if(index<0)return geo_parameter_error(error,GEO_PARAMETER_MISSING_FIELD,ref.parameter_id,ref.field_id);
    GeoParameterEvaluation *e=geo_parameter_evaluation_create(store,NULL,NULL);
    if(!e)return geo_parameter_error(error,GEO_PARAMETER_MEMORY,0,0);
    bool ok=geo_parameter_eval_field(e,index);*error=*e->error;
    geo_parameter_evaluation_destroy(e);return ok;
}


static bool geo_parameter_name_valid(const char name[GEO_PARAMETER_NAME_MAX])
{
    const char *end=memchr(name,0,GEO_PARAMETER_NAME_MAX);
    return end&&geo_utf8_name_valid((const unsigned char*)name,(size_t)(end-name),GEO_PARAMETER_NAME_MAX-1);
}
void geo_parameters_begin_definition(const GeoParameterStore *s,uint32_t id,GeoParameterCard *card)
{memset(card,0,sizeof *card);card->id=id;const GeoParameterCard *old=geo_parameters_find(s,id);card->next_field_id=old?old->next_field_id:1;}
bool geo_parameters_accept_rebuilt_field(const GeoParameterStore *s,GeoParameterCard *card,
    const GeoParameterField *fields,size_t k,GeoParameterRebuiltKey rebuilt,void *state,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(k>=GEO_PARAMETER_FIELDS_PER_CARD)return geo_parameter_error(error,GEO_PARAMETER_CAPACITY,card->id,0);
    const GeoParameterField *v=&fields[k];const GeoParameterCard *old=geo_parameters_find(s,card->id);
    if(v->parameter_id!=card->id||v->type<0||v->type>2)return geo_parameter_error(error,GEO_PARAMETER_INVALID_DEFINITION,card->id,v->id);
    for(size_t q=0;q<k;++q)if(fields[q].id==v->id||!strcmp(fields[q].name,v->name))return geo_parameter_error(error,GEO_PARAMETER_DUPLICATE_FIELD,card->id,v->id);
    card->fields[k]=v->id;
    if(old&&geo_parameters_field_index(s,card->id,v->id)<0&&(old->next_field_id==0||v->id<old->next_field_id)&&
       !(rebuilt&&rebuilt(state,card->id,v->id)))return geo_parameter_error(error,GEO_PARAMETER_REUSED_FIELD,card->id,v->id);
    if(v->id==UINT32_MAX)card->next_field_id=0;else if(card->next_field_id&&v->id>=card->next_field_id)card->next_field_id=v->id+1;
    return true;
}
bool geo_parameters_accept_field(const GeoParameterStore *s,GeoParameterCard *card,
    const GeoParameterField *fields,size_t k,GeoParameterError *error)
{return geo_parameters_accept_rebuilt_field(s,card,fields,k,NULL,NULL,error);}
bool geo_parameters_next_field(GeoParameterCard *card,uint32_t next,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(card->next_field_id==0?next!=0:(next!=0&&next<card->next_field_id))return geo_parameter_error(error,GEO_PARAMETER_NEXT_ID,card->id,0);
    card->next_field_id=next;return true;
}
/* Complete put validation without mutation; on success returns the slot. */
static bool geo_parameters_validate_put(const GeoParameterStore *s,const GeoParameterCard *card,const GeoParameterField *fields,
    GeoParameterRebuiltKey rebuilt,void *state,GeoParameterCard *validated,size_t *out_slot,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    if(!s||!card||!fields||!card->count||card->count>GEO_PARAMETER_FIELDS_PER_CARD)return geo_parameter_error(error,GEO_PARAMETER_INVALID_DEFINITION,0,0);
    if(!geo_parameter_name_valid(card->name))return geo_parameter_error(error,GEO_PARAMETER_NAME,card->id,0);
    for(size_t k=0;k<card->count;++k){
        if(!geo_parameter_name_valid(fields[k].name))return geo_parameter_error(error,GEO_PARAMETER_NAME,card->id,fields[k].id);
        if(!memchr(fields[k].expression,0,GEO_PARAMETER_EXPR_MAX))return geo_parameter_error(error,GEO_PARAMETER_INVALID_DEFINITION,card->id,fields[k].id);
    }
    geo_parameters_begin_definition(s,card->id,validated);validated->count=card->count;
    for(size_t k=0;k<card->count;++k)if(!geo_parameters_accept_rebuilt_field(s,validated,fields,k,rebuilt,state,error))return false;
    if(!geo_parameters_next_field(validated,card->next_field_id,error))return false;
    size_t slot=0;while(slot<s->card_count&&s->cards[slot].id!=card->id)++slot;
    size_t existing=0;for(size_t i=0;i<s->field_count;++i)existing+=s->fields[i].parameter_id==card->id;
    if(slot==GEO_PARAMETER_CARD_MAX||s->field_count-existing+card->count>GEO_PARAMETER_FIELD_MAX)return geo_parameter_error(error,GEO_PARAMETER_CAPACITY,card->id,0);
    *out_slot=slot;return true;
}
bool geo_parameters_check_put(const GeoParameterStore *s,const GeoParameterCard *card,const GeoParameterField *fields,
    GeoParameterRebuiltKey rebuilt,void *state,GeoParameterError *error)
{GeoParameterCard validated;size_t slot;return geo_parameters_validate_put(s,card,fields,rebuilt,state,&validated,&slot,error);}
bool geo_parameters_put(GeoParameterStore *s,const GeoParameterCard *card,const GeoParameterField *fields,GeoParameterError *error)
{return geo_parameters_put_rebuilt(s,card,fields,NULL,NULL,error);}
bool geo_parameters_put_rebuilt(GeoParameterStore *s,const GeoParameterCard *card,const GeoParameterField *fields,
    GeoParameterRebuiltKey rebuilt,void *state,GeoParameterError *error)
{
    GeoParameterCard validated;size_t slot;
    if(!geo_parameters_validate_put(s,card,fields,rebuilt,state,&validated,&slot,error))return false;
    /* Public const views may be passed back as a definition. Snapshot before
     * compaction, which can otherwise overwrite the caller's borrowed slice. */
    GeoParameterField replacement[GEO_PARAMETER_FIELDS_PER_CARD];
    memcpy(replacement,fields,card->count*sizeof *fields);
    size_t n=0;for(size_t i=0;i<s->field_count;++i)if(s->fields[i].parameter_id!=card->id)s->fields[n++]=s->fields[i];
    for(size_t k=0;k<card->count;++k){s->fields[n]=replacement[k];memset(&s->fields[n].value,0,sizeof s->fields[n].value);++n;}
    memset(s->fields+n,0,(GEO_PARAMETER_FIELD_MAX-n)*sizeof(GeoParameterField));s->field_count=n;
    s->cards[slot]=*card;memcpy(s->cards[slot].fields,validated.fields,sizeof validated.fields);
    if(slot==s->card_count)++s->card_count;return true;
}
bool geo_parameters_remove(GeoParameterStore *s,uint32_t id,GeoParameterError *error)
{
    if(error)memset(error,0,sizeof *error);
    size_t k=0;while(k<s->card_count&&s->cards[k].id!=id)++k;
    if(k==s->card_count)return geo_parameter_error(error,GEO_PARAMETER_MISSING_CARD,id,0);
    memmove(s->cards+k,s->cards+k+1,(s->card_count-k-1)*sizeof(GeoParameterCard));memset(&s->cards[--s->card_count],0,sizeof(GeoParameterCard));
    size_t n=0;for(size_t i=0;i<s->field_count;++i)if(s->fields[i].parameter_id!=id)s->fields[n++]=s->fields[i];
    memset(s->fields+n,0,(GEO_PARAMETER_FIELD_MAX-n)*sizeof(GeoParameterField));s->field_count=n;return true;
}
bool geo_parameters_stage_card(GeoParameterStore *s,const GeoParameterCard *card)
{
    if(!s||!card||!geo_parameter_name_valid(card->name)||card->count||geo_parameters_find(s,card->id)||s->card_count>=GEO_PARAMETER_CARD_MAX)return false;
    s->cards[s->card_count++]=*card;return true;
}
bool geo_parameters_stage_field(GeoParameterStore *s,const GeoParameterField *field)
{
    if(!s||!field||!geo_parameter_name_valid(field->name)||!memchr(field->expression,0,GEO_PARAMETER_EXPR_MAX)||field->type<0||field->type>2)return false;
    GeoParameterCard *card=(GeoParameterCard*)geo_parameters_find(s,field->parameter_id);
    if(!card||card->count>=GEO_PARAMETER_FIELDS_PER_CARD||s->field_count>=GEO_PARAMETER_FIELD_MAX||(card->next_field_id&&field->id>=card->next_field_id))return false;
    for(size_t k=0;k<s->field_count;++k)if(s->fields[k].parameter_id==field->parameter_id&&(s->fields[k].id==field->id||!strcmp(s->fields[k].name,field->name)))return false;
    card->fields[card->count++]=field->id;s->fields[s->field_count++]=*field;return true;
}

#endif
