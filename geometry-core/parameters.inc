/* parameters/1: the native evaluator is shared by bridge, scene and model CLI. */
#include "kernel/codec.h"
#include "kernel/exact.h"
#include <stdarg.h>
#include <ctype.h>
static bool g_parameter_scene_loading;
static ParameterRef g_parameter_dimension_error;
static bool parameter_kernel_error(const World *,const GeoParameterError *);
static bool parameter_fail(const char *format,...)
{
    va_list a;va_start(a,format);vsnprintf(g_parameter_error,sizeof g_parameter_error,format,a);va_end(a);utf8_trim_tail(g_parameter_error);return false;
}
/* Host diagnostics preserve the established command contract. */
static bool parameter_exact_status(GeoExactStatus status)
{
    switch(status){
    case GEO_EXACT_OK:return true;
    case GEO_EXACT_INTEGER_MAGNITUDE:return parameter_fail("UNSUPPORTED/PRECISION: integer magnitude");
    case GEO_EXACT_MULTIPLICATION_OVERFLOW:return parameter_fail("UNSUPPORTED/PRECISION: exact multiplication exceeds int64");
    case GEO_EXACT_SUM_OVERFLOW:return parameter_fail("UNSUPPORTED/PRECISION: exact sum exceeds int64");
    case GEO_EXACT_UNIT_MISMATCH:return parameter_fail("I38 UNIT: addition/subtraction needs matching units");
    case GEO_EXACT_PRODUCT_UNIT:return parameter_fail("I38 UNIT: area/volume arithmetic is not supported");
    case GEO_EXACT_DIVISION_ZERO:return parameter_fail("I38 DIV_ZERO: division by zero");
    case GEO_EXACT_INVERSE_UNIT:return parameter_fail("I38 UNIT: inverse length is not supported");
    case GEO_EXACT_UNKNOWN_OPERATION:return parameter_fail("I38 OP: unknown arithmetic operation");
    case GEO_EXACT_DENOMINATOR:return parameter_fail("I38 NUMBER: denominator must be positive");
    default:return parameter_fail("I38 UNIT: invalid quantity unit");
    }
}
static bool parameter_mul(int64_t a,int64_t b,int64_t *r)
{return parameter_exact_status(geo_integer_multiply(a,b,r));}
static bool parameter_add(int64_t a,int64_t b,int64_t *r)
{return parameter_exact_status(geo_integer_add(a,b,r));}
static GeoQuantity parameter_normal(GeoQuantity value)
{
    GeoQuantity result=value;
    parameter_exact_status(geo_quantity_normalize(value,&result));
    return result;
}
static bool parameter_binary(const char *op,GeoQuantity a,GeoQuantity b,GeoQuantity *r)
{
    GeoExactOperation operation;
    if(!strcmp(op,"add"))operation=GEO_EXACT_ADD;
    else if(!strcmp(op,"sub"))operation=GEO_EXACT_SUBTRACT;
    else if(!strcmp(op,"mul"))operation=GEO_EXACT_MULTIPLY;
    else if(!strcmp(op,"div"))operation=GEO_EXACT_DIVIDE;
    else return parameter_exact_status(GEO_EXACT_UNKNOWN_OPERATION);
    return parameter_exact_status(geo_quantity_binary(operation,a,b,r));
}
static const ParameterSet *parameter_find(const World *w,uint32_t id)
{return geo_parameters_find(&w->geo.parameters,id);}
static int parameter_field_index(const World *w,uint32_t id,uint32_t field)
{return geo_parameters_field_index(&w->geo.parameters,id,field);}
static bool parameter_u32(GeoJson *j,int t,uint32_t *out)
{int64_t v;if(!geo_json_integer(j,t,&v)||v<0||v>UINT32_MAX)return parameter_fail("I38 ID: expected uint32 identity");*out=(uint32_t)v;return true;}
static bool parameter_integer(const char *s,int64_t *v)
{if(!s||!parse_i64(s,v)||*v==INT64_MIN)return parameter_fail("UNSUPPORTED/PRECISION: exact integer must fit signed int64 magnitude");return true;}
static bool parameter_ref_parse(const char *s,ParameterRef *r)
{
    if(strncmp(s,"param:",6))return false;
    char b[64];if(strlen(s)>=sizeof b)return false;snprintf(b,sizeof b,"%s",s+6);char *c=strchr(b,':');if(!c)return false;*c++=0;
    if(!parse_u32(b,&r->parameter_id)||!parse_u32(c,&r->field_id))return false;r->set=true;return true;
}
static bool parameter_value(const World *w,ParameterRef ref,GeoQuantity *v)
{
    g_parameter_dimension_error=(ParameterRef){0};GeoParameterError error;
    if(geo_parameters_dimension_value(&w->geo.parameters,ref,v,&error))return true;
    if(error.status==GEO_PARAMETER_NOT_DIMENSION)g_parameter_dimension_error=ref;
    return parameter_kernel_error(w,&error);
}
static bool parameter_coord(const World *w,ParameterRef ref,Coord *out)
{
    g_parameter_dimension_error=(ParameterRef){0};GeoParameterError error;
    if(geo_parameters_coordinate(&w->geo.parameters,ref,out,&error))return true;
    if(error.status==GEO_PARAMETER_NOT_DIMENSION)g_parameter_dimension_error=ref;
    return parameter_kernel_error(w,&error);
}
/* Canonical AST is persisted; this bounded parser only translates input text. */
typedef struct {int op,left,right;GeoQuantity value;ParameterRef ref;} ParameterNode;
typedef struct {const char *p;ParameterNode nodes[PARAM_NODE_MAX];int count,depth;} ParameterParser;
static int parameter_text_sum(ParameterParser *p);
static void parameter_space(ParameterParser *p){while(*p->p==' '||*p->p=='\t')++p->p;}
static int parameter_node(ParameterParser *p,ParameterNode n)
{if(p->count==PARAM_NODE_MAX){parameter_fail("UNSUPPORTED/CAPACITY: expression exceeds 128 nodes");return -1;}p->nodes[p->count]=n;return p->count++;}
static bool parameter_decimal(const char **text,GeoQuantity *out)
{
    const char *p=*text;int64_t n=0,d=1;bool dot=false,any=false;
    while((*p>='0'&&*p<='9')||*p=='.'){
        if(*p=='.'){if(dot)return parameter_fail("I38 NUMBER: repeated decimal point");dot=true;++p;continue;}
        int digit=*p++-'0';any=true;
        if(n>(INT64_MAX-digit)/10||(dot&&d>INT64_MAX/10))return parameter_fail("UNSUPPORTED/PRECISION: decimal exceeds exact capacity");
        n=n*10+digit;if(dot)d*=10;
    }
    if(!any)return parameter_fail("I38 NUMBER: expected decimal number");
    *text=p;*out=parameter_normal((GeoQuantity){n,d,0});return true;
}
static int parameter_text_atom(ParameterParser *p)
{
    parameter_space(p);if(++p->depth>32){parameter_fail("UNSUPPORTED/CAPACITY: expression nesting exceeds 32");return -1;}
    int node=-1;ParameterNode n={0};
    if(*p->p=='+'||*p->p=='-'){bool neg=*p->p++=='-';int child=parameter_text_atom(p);if(child<0)return -1;if(neg){n.op=6;n.left=child;node=parameter_node(p,n);}else node=child;}
    else if(*p->p=='('){++p->p;node=parameter_text_sum(p);if(node<0)return -1;parameter_space(p);if(*p->p!=')'){parameter_fail("I38 SYNTAX: missing closing parenthesis");return -1;}++p->p;}
    else if(*p->p=='@'){
        ++p->p;char id[32],field[32];size_t i=0;
        while(isdigit((unsigned char)*p->p)&&i<sizeof id-1)id[i++]=*p->p++;id[i]=0;
        if(*p->p++!=':'){parameter_fail("I38 REFERENCE: expected @parameterId:fieldId");return -1;}i=0;
        while(isdigit((unsigned char)*p->p)&&i<sizeof field-1)field[i++]=*p->p++;field[i]=0;
        if(!parse_u32(id,&n.ref.parameter_id)||!parse_u32(field,&n.ref.field_id)){parameter_fail("I38 REFERENCE: invalid field identity");return -1;}
        n.op=1;n.ref.set=true;node=parameter_node(p,n);
    }else{
        if(!parameter_decimal(&p->p,&n.value))return -1;parameter_space(p);
        if(!strncmp(p->p,"mm",2)){n.value.unit=1;p->p+=2;}node=parameter_node(p,n);
    }
    --p->depth;return node;
}
static int parameter_text_product(ParameterParser *p)
{
    int left=parameter_text_atom(p);if(left<0)return -1;
    for(;;){parameter_space(p);char op=*p->p;if(op!='*'&&op!='/')return left;++p->p;int right=parameter_text_atom(p);if(right<0)return -1;ParameterNode n={0};n.op=op=='*'?4:5;n.left=left;n.right=right;left=parameter_node(p,n);if(left<0)return -1;}
}
static int parameter_text_sum(ParameterParser *p)
{
    int left=parameter_text_product(p);if(left<0)return -1;
    for(;;){parameter_space(p);char op=*p->p;if(op!='+'&&op!='-')return left;++p->p;int right=parameter_text_product(p);if(right<0)return -1;ParameterNode n={0};n.op=op=='+'?2:3;n.left=left;n.right=right;left=parameter_node(p,n);if(left<0)return -1;}
}
typedef struct {char *text;size_t size,used;bool ok;} ParameterWriter;
static void parameter_write(ParameterWriter *b,const char *format,...)
{
    if(!b->ok)return;va_list a;va_start(a,format);int n=vsnprintf(b->text+b->used,b->size-b->used,format,a);va_end(a);
    if(n<0||(size_t)n>=b->size-b->used){b->ok=false;return;}b->used+=(size_t)n;
}
static void parameter_ast_write(ParameterParser *p,int index,ParameterWriter *b)
{
    ParameterNode *n=&p->nodes[index];const char *ops[]={"literal","ref","add","sub","mul","div","neg"};
    if(!n->op)parameter_write(b,"{\"den\":\"%lld\",\"num\":\"%lld\",\"op\":\"literal\",\"unit\":\"%s\"}",(long long)n->value.den,(long long)n->value.num,n->value.unit?"mm":"1");
    else if(n->op==1)parameter_write(b,"{\"fieldId\":%u,\"op\":\"ref\",\"parameterId\":%u}",n->ref.field_id,n->ref.parameter_id);
    else{parameter_write(b,"{\"left\":");parameter_ast_write(p,n->left,b);parameter_write(b,",\"op\":\"%s\"",ops[n->op]);if(n->op!=6){parameter_write(b,",\"right\":");parameter_ast_write(p,n->right,b);}parameter_write(b,"}");}
}
static bool parameter_input(const char *text,int type,char out[PARAM_EXPR_MAX])
{
    char normalized[PARAM_EXPR_MAX];size_t at=0;
    for(const unsigned char *p=(const unsigned char*)text;*p;){
        if(at+1>=sizeof normalized)return parameter_fail("UNSUPPORTED/CAPACITY: input length");
        if(!strncmp((const char*)p,"−",3)){normalized[at++]='-';p+=3;}
        else if(!strncmp((const char*)p,"×",2)){normalized[at++]='*';p+=2;}
        else if(!strncmp((const char*)p,"÷",2)){normalized[at++]='/';p+=2;}
        else if(!strncmp((const char*)p,"＝",3)){normalized[at++]='=';p+=3;}
        else normalized[at++]=(char)*p++;
    }normalized[at]=0;text=normalized;
    ParameterParser p={0};p.p=text;parameter_space(&p);bool formula=*p.p=='=';if(formula)++p.p;
    int root;
    if(formula)root=parameter_text_sum(&p);
    else{
        bool neg=false;if(*p.p=='+'||*p.p=='-')neg=*p.p++=='-';ParameterNode n={0};
        if(!parameter_decimal(&p.p,&n.value))return false;if(neg)n.value.num=-n.value.num;parameter_space(&p);
        if(*p.p=='/'){++p.p;parameter_space(&p);GeoQuantity d;if(!parameter_decimal(&p.p,&d)||!parameter_binary("div",n.value,d,&n.value))return false;}
        parameter_space(&p);if(!strncmp(p.p,"mm",2)){if(type!=0)return parameter_fail("I38 UNIT: only dimension literals accept mm");p.p+=2;}
        n.value.unit=type==0;root=parameter_node(&p,n);
    }
    parameter_space(&p);if(root<0)return false;if(*p.p)return parameter_fail("I38 SYNTAX: unexpected input near %.40s",p.p);
    ParameterWriter b={out,PARAM_EXPR_MAX,0,true};parameter_ast_write(&p,root,&b);
    return b.ok?true:parameter_fail("UNSUPPORTED/CAPACITY: expression record exceeds 2047 bytes");
}
/* Dependency depth is a property of the field, not of the evaluation stack: fdepth[i] = 1 + max fdepth of the fields it references
 * (a leaf is 1). It is recorded when a field finishes and read back by every referrer, cache hit or not, so accept/reject is
 * independent of storage order. maxref accumulates the deepest referenced field of the field currently being evaluated. */

/* Prepend one "[card:field name.field] -> " link to g_parameter_error. Consumers truncate from the end (eng_fail keeps 255 bytes,
 * grid messages "%.190s"), so a 64-link path used to swallow the error code. Keep the outermost link, the innermost link and the
 * root cause, and elide the middle, so the total stays within PARAM_ERROR_BUDGET and the code (e.g. UNSUPPORTED/CAPACITY) survives. */
#define PARAM_ERROR_BUDGET 190
static void parameter_wrap_error(uint32_t pid,uint32_t fid,const char *card,const char *field)
{
    char head[256],tail[512],out[512];
    snprintf(head,sizeof head,"[%u:%u %s.%s] -> ",pid,fid,card,field);utf8_trim_tail(head);
    snprintf(tail,sizeof tail,"%s",g_parameter_error);
    if(strlen(head)+strlen(tail)<=PARAM_ERROR_BUDGET){snprintf(g_parameter_error,sizeof g_parameter_error,"%s%s",head,tail);return;}
    const char *last=NULL,*prev=NULL;for(const char *q=tail;(q=strstr(q," -> "))!=NULL;q+=4){prev=last;last=q;}
    const char *root=last?last+4:tail,*inner=last?(prev?prev+4:tail):"";int inner_len=last?(int)(last-inner):0;
    if(inner_len==3&&!memcmp(inner,"...",3))inner_len=0;
    snprintf(out,sizeof out,"%s... -> %.*s%s%s",head,inner_len,inner,inner_len?" -> ":"",root);
    if(strlen(out)>PARAM_ERROR_BUDGET)snprintf(out,sizeof out,"%s... -> %s",head,root);
    if(strlen(out)>PARAM_ERROR_BUDGET){
        int room=PARAM_ERROR_BUDGET-7-(int)strlen(root);if(room<16)room=16;
        snprintf(out,sizeof out,"%.*s",room,head);utf8_trim_tail(out);
        size_t n=strlen(out);snprintf(out+n,sizeof out-n,"... -> %s",root);
    }
    snprintf(g_parameter_error,sizeof g_parameter_error,"%s",out);utf8_trim_tail(g_parameter_error);
}
static bool parameter_kernel_error(const World *w,const GeoParameterError *error)
{
    uint32_t id=error->source.parameter_id,field=error->source.field_id;
    switch(error->status){
    case GEO_PARAMETER_MISSING_CARD:parameter_fail("I38 MISSING: parameter %u",id);break;
    case GEO_PARAMETER_MISSING_FIELD:parameter_fail("I38 MISSING: parameter %u field %u",id,field);break;
    case GEO_PARAMETER_NOT_DIMENSION:parameter_fail("I38 UNIT: parameter %u field %u is not a dimension",id,field);break;
    case GEO_PARAMETER_COORDINATE:{const ParameterSet *c=parameter_find(w,id);int i=parameter_field_index(w,id,field);const ParameterField *f=&geo_parameters_fields(&w->geo.parameters)[i];
        parameter_fail("I38 GEOMETRY: [%u:%u %s.%s] must resolve to integer mm in D1 range (got %lld/%lld)",id,field,c->name,f->name,(long long)error->quantity.num,(long long)error->quantity.den);break;}
    case GEO_PARAMETER_AST_CAPACITY:parameter_fail("UNSUPPORTED/CAPACITY: expression tree exceeds declared limits");break;
    case GEO_PARAMETER_AST_OPERATION_MISSING:parameter_fail("I38 AST: missing operation");break;
    case GEO_PARAMETER_AST_LITERAL:parameter_fail("I38 AST: invalid exact literal");break;
    case GEO_PARAMETER_INTEGER:parameter_fail("UNSUPPORTED/PRECISION: exact integer must fit signed int64 magnitude");break;
    case GEO_PARAMETER_DENOMINATOR:parameter_fail("I38 NUMBER: denominator must be positive");break;
    case GEO_PARAMETER_LITERAL_UNIT:parameter_fail("I38 UNIT: expected mm or 1");break;
    case GEO_PARAMETER_AST_REFERENCE:parameter_fail("I38 AST: invalid reference");break;
    case GEO_PARAMETER_UNSUPPORTED_OPERATION:parameter_fail("I38 OP: unsupported operation");break;
    case GEO_PARAMETER_AST_ARITHMETIC:parameter_fail("I38 AST: invalid arithmetic node");break;
    case GEO_PARAMETER_CYCLE:parameter_fail("I38 CYCLE: parameter %u field %u",id,field);break;
    case GEO_PARAMETER_DEPTH:parameter_fail("UNSUPPORTED/CAPACITY: dependency depth exceeds 64");break;
    case GEO_PARAMETER_JSON:parameter_fail("I38 JSON: %s",!strcmp(error->detail,"NUL is not allowed in JSON")?"NUL is not allowed in engineering JSON":error->detail);break;
    case GEO_PARAMETER_FIELD_UNIT:parameter_fail("I38 UNIT: result unit does not match field type");break;
    case GEO_PARAMETER_COUNT_VALUE:parameter_fail("I38 COUNT: quantity must be a nonnegative integer");break;
    case GEO_PARAMETER_MEMORY:parameter_fail("UNSUPPORTED/CAPACITY: parameter evaluation memory");break;
    case GEO_PARAMETER_EXACT:parameter_exact_status(error->exact);break;
    case GEO_PARAMETER_DUPLICATE_FIELD:parameter_fail("I38 DUPLICATE: field identity/name in parameter %u",id);break;
    case GEO_PARAMETER_REUSED_FIELD:parameter_fail("I38 ID: deleted field identities cannot be reused");break;
    case GEO_PARAMETER_NEXT_ID:parameter_fail("I38 ID: nextFieldId cannot move backwards");break;
    case GEO_PARAMETER_CAPACITY:parameter_fail("UNSUPPORTED/CAPACITY: 64 cards / 256 total fields exceeded");break;
    case GEO_PARAMETER_NAME:parameter_fail("I38 NAME: expected 1..96 UTF-8 bytes without control characters");break;
    default:parameter_fail("I38 FIELD: invalid field definition");break;
    }
    for(size_t k=0;k<error->trace_count;++k){GeoParameterRef ref=error->trace[k];const ParameterSet *c=parameter_find(w,ref.parameter_id);int i=parameter_field_index(w,ref.parameter_id,ref.field_id);const ParameterField *f=i>=0?&geo_parameters_fields(&w->geo.parameters)[i]:NULL;
        parameter_wrap_error(ref.parameter_id,ref.field_id,c?c->name:"?",f?f->name:"?");}
    return false;
}
static bool parameters_rebuild(World *w,char *error,size_t cap)
{
    g_parameter_error[0]=0;GeoParameterError issue;bool ok;
    if(w->app.parameter_loading)ok=parameter_fail("I39: unterminated parameter block");
    else{ok=geo_parameters_rebuild(&w->geo.parameters,&issue);if(!ok)parameter_kernel_error(w,&issue);}
    if(!ok)snprintf(error,cap,"%s",g_parameter_error);return ok;
}

static bool parameter_name(GeoJson *j,int t,char out[PARAM_NAME_MAX])
{
    if(!geo_json_string(j,t,out,PARAM_NAME_MAX)||!geo_utf8_name_valid((const unsigned char*)out,strlen(out),PARAM_NAME_MAX-1))return parameter_fail("I38 NAME: expected 1..96 UTF-8 bytes without control characters");return true;
}
static bool parameter_put(World *w,GeoJson *j,int t)
{
    uint32_t id;if(!geo_json_keys(j,t,"id,name,fields","nextFieldId")||!parameter_u32(j,geo_json_member(j,t,"id"),&id))return parameter_fail("I38 CARD: expected id, name and fields");
    ParameterSet card;geo_parameters_begin_definition(&w->geo.parameters,id,&card);if(!parameter_name(j,geo_json_member(j,t,"name"),card.name))return false;
    int fields=geo_json_member(j,t,"fields");if(!geo_json_is_array(j,fields)||geo_json_size(j,fields)<1||geo_json_size(j,fields)>PARAM_FIELDS_PER_CARD)return parameter_fail("UNSUPPORTED/CAPACITY: card requires 1..16 fields");
    ParameterField *fresh=calloc(PARAM_FIELDS_PER_CARD,sizeof *fresh);if(!fresh)return parameter_fail("UNSUPPORTED/CAPACITY: parameter fields memory");
    bool ok=true;GeoParameterError issue;card.count=(size_t)geo_json_size(j,fields);
    for(size_t k=0;k<card.count&&ok;++k){int f=geo_json_at(j,fields,(int)k);ParameterField *v=&fresh[k];char type[20];v->parameter_id=id;
        int input=geo_json_member(j,f,"input"),expr=geo_json_member(j,f,"expression");
        if((input>=0)==(expr>=0)||!geo_json_keys(j,f,input>=0?"id,name,type,input":"id,name,type,expression","")||!parameter_u32(j,geo_json_member(j,f,"id"),&v->id)||!parameter_name(j,geo_json_member(j,f,"name"),v->name)||!geo_json_string(j,geo_json_member(j,f,"type"),type,sizeof type)){ok=parameter_fail("I38 FIELD: invalid field definition");break;}
        v->type=!strcmp(type,"dimension")?0:!strcmp(type,"count")?1:!strcmp(type,"ratio")?2:-1;if(v->type<0){ok=parameter_fail("I38 TYPE: dimension/count/ratio required");break;}
        if(!geo_parameters_accept_field(&w->geo.parameters,&card,fresh,k,&issue)){ok=parameter_kernel_error(w,&issue);break;}
        if(input>=0){char text[PARAM_EXPR_MAX];if(!geo_json_string(j,input,text,sizeof text))ok=parameter_fail("UNSUPPORTED/CAPACITY: parameter input exceeds 2047 bytes");else if(!parameter_input(text,v->type,v->expression))ok=false;}
        else if(!geo_json_canonical(j,expr,v->expression,sizeof v->expression))ok=parameter_fail("UNSUPPORTED/CAPACITY: expression record exceeds capacity");
        if(!ok)parameter_wrap_error(id,v->id,card.name,v->name);
    }
    uint32_t next;int nt=geo_json_member(j,t,"nextFieldId");if(ok&&nt>=0){if(!parameter_u32(j,nt,&next))ok=false;else if(!geo_parameters_next_field(&card,next,&issue))ok=parameter_kernel_error(w,&issue);}
    if(ok&&!geo_parameters_put(&w->geo.parameters,&card,fresh,&issue))ok=parameter_kernel_error(w,&issue);
    free(fresh);return ok;
}
static bool parameter_remove(World *w,uint32_t id)
{
    GeoParameterError issue;if(!geo_parameters_remove(&w->geo.parameters,id,&issue))return parameter_kernel_error(w,&issue);
    size_t n=0;for(size_t i=0;i<w->app.canvas_pos_count;++i)if(w->app.canvas_pos[i].kind!=CANVAS_POS_PARAMETER||w->app.canvas_pos[i].id!=id)w->app.canvas_pos[n++]=w->app.canvas_pos[i];memset(w->app.canvas_pos+n,0,(w->app.canvas_pos_count-n)*sizeof(CanvasPos));w->app.canvas_pos_count=n;return true;
}
/* Package imports allocate a complete independent identity map before copying.
 * References must remain inside the package; no accidental links to this world. */
static bool parameter_remap_ast(GeoJson *j,int t,ParameterWriter *out,const uint32_t *old,const uint32_t *fresh,int count,int depth)
{
    if(depth>32)return parameter_fail("UNSUPPORTED/CAPACITY: imported expression nesting");
    char op[16];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return parameter_fail("I38 AST: imported operation missing");
    if(!strcmp(op,"literal")){
        char literal[PARAM_EXPR_MAX];if(!geo_json_canonical(j,t,literal,sizeof literal))return parameter_fail("I38 AST: imported literal invalid");parameter_write(out,"%s",literal);return out->ok;
    }
    if(!strcmp(op,"ref")){
        uint32_t id,field;if(!geo_json_keys(j,t,"op,parameterId,fieldId","")||!parameter_u32(j,geo_json_member(j,t,"parameterId"),&id)||!parameter_u32(j,geo_json_member(j,t,"fieldId"),&field))return parameter_fail("I38 AST: imported reference invalid");
        int k=0;while(k<count&&old[k]!=id)++k;if(k==count)return parameter_fail("I39 PACKAGE: missing dependency card %u",id);
        parameter_write(out,"{\"op\":\"ref\",\"parameterId\":%u,\"fieldId\":%u}",fresh[k],field);return out->ok;
    }
    bool neg=!strcmp(op,"neg");if((!neg&&strcmp(op,"add")&&strcmp(op,"sub")&&strcmp(op,"mul")&&strcmp(op,"div"))||!geo_json_keys(j,t,neg?"op,left":"op,left,right",""))return parameter_fail("I38 AST: invalid imported operation");
    parameter_write(out,"{\"op\":\"%s\",\"left\":",op);
    if(!parameter_remap_ast(j,geo_json_member(j,t,"left"),out,old,fresh,count,depth+1))return false;
    if(!neg){parameter_write(out,",\"right\":");if(!parameter_remap_ast(j,geo_json_member(j,t,"right"),out,old,fresh,count,depth+1))return false;}
    parameter_write(out,"}");return out->ok;
}
static bool parameter_import(World *w,GeoJson *j,int t)
{
    char schema[40];int cards=geo_json_member(j,t,"cards");
    if(!geo_json_keys(j,t,"schema,cards","")||!geo_json_string(j,geo_json_member(j,t,"schema"),schema,sizeof schema)||strcmp(schema,"geometry-parameters/1")||!geo_json_is_array(j,cards))return parameter_fail("I39 PACKAGE: expected geometry-parameters/1 cards");
    int n=geo_json_size(j,cards);if(n<1||n>PARAM_CARD_MAX||(size_t)n+geo_parameters_card_count(&w->geo.parameters)>PARAM_CARD_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: imported card capacity");
    uint32_t old[PARAM_CARD_MAX],fresh[PARAM_CARD_MAX];uint32_t candidate=0;
    for(int k=0;k<n;++k){
        int c=geo_json_at(j,cards,k);if(!parameter_u32(j,geo_json_member(j,c,"id"),&old[k]))return false;
        for(int q=0;q<k;++q)if(old[q]==old[k])return parameter_fail("I39 PACKAGE: duplicate card identity");
        while(parameter_find(w,candidate))++candidate;fresh[k]=candidate++;
    }
    char *buffer=malloc(PARAM_FIELDS_PER_CARD*(PARAM_EXPR_MAX+1000));if(!buffer)return parameter_fail("UNSUPPORTED/CAPACITY: package memory");bool ok=true;
    for(int k=0;k<n&&ok;++k){
        int c=geo_json_at(j,cards,k),fields=geo_json_member(j,c,"fields");char name[PARAM_NAME_MAX],quoted[600];
        if(!geo_json_keys(j,c,"id,name,fields","nextFieldId")||!parameter_name(j,geo_json_member(j,c,"name"),name)||!geo_json_is_array(j,fields)||geo_json_size(j,fields)<1||geo_json_size(j,fields)>PARAM_FIELDS_PER_CARD){ok=parameter_fail("I39 PACKAGE: invalid card");break;}
        geo_json_quote(name,quoted,sizeof quoted);ParameterWriter b={buffer,PARAM_FIELDS_PER_CARD*(PARAM_EXPR_MAX+1000),0,true};parameter_write(&b,"{\"id\":%u,\"name\":%s",fresh[k],quoted);
        int nt=geo_json_member(j,c,"nextFieldId");uint32_t next;if(nt>=0){if(!parameter_u32(j,nt,&next)){ok=false;break;}parameter_write(&b,",\"nextFieldId\":%u",next);}parameter_write(&b,",\"fields\":[");
        for(int f=0;f<geo_json_size(j,fields)&&ok;++f){int ft=geo_json_at(j,fields,f);uint32_t id;char type[20];
            if(!geo_json_keys(j,ft,"id,name,type,expression","")||!parameter_u32(j,geo_json_member(j,ft,"id"),&id)||!parameter_name(j,geo_json_member(j,ft,"name"),name)||!geo_json_string(j,geo_json_member(j,ft,"type"),type,sizeof type)||(strcmp(type,"dimension")&&strcmp(type,"count")&&strcmp(type,"ratio"))){ok=parameter_fail("I39 PACKAGE: invalid field");break;}
            geo_json_quote(name,quoted,sizeof quoted);parameter_write(&b,"%s{\"id\":%u,\"name\":%s,\"type\":\"%s\",\"expression\":",f?",":"",id,quoted,type);
            ok=parameter_remap_ast(j,geo_json_member(j,ft,"expression"),&b,old,fresh,n,0);parameter_write(&b,"}");
        }
        parameter_write(&b,"]}");if(!b.ok){ok=parameter_fail("UNSUPPORTED/CAPACITY: package expression record");break;}
        if(ok){GeoJson copy;ok=app_json_parse_n(&copy,buffer,b.used);if(ok)ok=parameter_put(w,&copy,0);geo_json_free(&copy);}
    }
    free(buffer);return ok;
}
static void parameter_json_card(const World *w,const ParameterSet *c,FILE *out,bool values)
{
    char q[600];geo_json_quote(c->name,q,sizeof q);fprintf(out,"{\"id\":%u,\"name\":%s,\"nextFieldId\":%u,\"fields\":[",c->id,q,c->next_field_id);
    for(size_t k=0;k<c->count;++k){int index=parameter_field_index(w,c->id,c->fields[k]);const ParameterField *f=&geo_parameters_fields(&w->geo.parameters)[index];geo_json_quote(f->name,q,sizeof q);
        fprintf(out,"%s{\"id\":%u,\"name\":%s,\"type\":\"%s\",\"expression\":%s",k?",":"",f->id,q,f->type==0?"dimension":f->type==1?"count":"ratio",f->expression);
        if(values)fprintf(out,",\"value\":{\"num\":\"%lld\",\"den\":\"%lld\",\"unit\":\"%s\"}",(long long)f->value.num,(long long)f->value.den,f->value.unit?"mm":"1");fputc('}',out);
    }fputs("]}",out);
}
static void parameters_dump(const World *w,FILE *out)
{
    if(!geo_parameters_card_count(&w->geo.parameters))return;fputs("requires parameters/1\nparameters begin\n",out);
    /* One field per bounded scene record; the block is a single declaration. */
    for(size_t i=0;i<geo_parameters_card_count(&w->geo.parameters);++i){const ParameterSet *c=&geo_parameters_cards(&w->geo.parameters)[i];char q[600];geo_json_quote(c->name,q,sizeof q);char record[900],encoded[1300];size_t n;
        snprintf(record,sizeof record,"{\"id\":%u,\"name\":%s,\"nextFieldId\":%u}",c->id,q,c->next_field_id);geo_base64_encode(record,strlen(record),encoded,sizeof encoded,&n);fprintf(out,"parameters card %s\n",encoded);
        for(size_t k=0;k<c->count;++k){const ParameterField *f=&geo_parameters_fields(&w->geo.parameters)[parameter_field_index(w,c->id,c->fields[k])];char field[3000],b64[4100];geo_json_quote(f->name,q,sizeof q);
            snprintf(field,sizeof field,"{\"parameterId\":%u,\"id\":%u,\"name\":%s,\"type\":%d,\"expression\":%s}",c->id,f->id,q,f->type,f->expression);geo_base64_encode(field,strlen(field),b64,sizeof b64,&n);fprintf(out,"parameters field %s\n",b64);
        }
    }fputs("parameters end\n",out);
}
static bool apply_parameters_line(const char *path,int line_no,char **t,int count,World *w)
{
    bool ok=false;if(!g_parameter_scene_loading){scene_error(path,line_no,"I39: parameter blocks require atomic full-scene loading; use parameter transactions for editing");return false;}
    if(count==2&&!strcmp(t[1],"begin")){if(w->app.parameter_loading)goto fail;w->app.parameter_loading=true;return true;}
    if(!w->app.parameter_loading)goto fail;
    if(count==2&&!strcmp(t[1],"end")){w->app.parameter_loading=false;for(size_t i=0;i<geo_parameters_card_count(&w->geo.parameters);++i)if(!geo_parameters_cards(&w->geo.parameters)[i].count)goto fail;char e[512];if(!parameters_rebuild(w,e,sizeof e)){scene_error(path,line_no,e);return false;}return true;}
    if(count!=3)goto fail;unsigned char decoded[4000];size_t n=0;if(!geo_base64_decode(t[2],strlen(t[2]),decoded,sizeof decoded-1,&n))goto fail;decoded[n]=0;
    GeoJson j;if(!app_json_parse_n(&j,(char*)decoded,n)){geo_json_free(&j);goto fail;}
    if(!strcmp(t[1],"card")){
        ParameterSet c={0};if(geo_json_keys(&j,0,"id,name,nextFieldId","")&&parameter_u32(&j,geo_json_member(&j,0,"id"),&c.id)&&parameter_u32(&j,geo_json_member(&j,0,"nextFieldId"),&c.next_field_id)&&parameter_name(&j,geo_json_member(&j,0,"name"),c.name)&&geo_parameters_stage_card(&w->geo.parameters,&c)){ok=true;}
    }else if(!strcmp(t[1],"field")){
        ParameterField f={0};int64_t type;
        if(geo_json_keys(&j,0,"parameterId,id,name,type,expression","")&&parameter_u32(&j,geo_json_member(&j,0,"parameterId"),&f.parameter_id)&&parameter_u32(&j,geo_json_member(&j,0,"id"),&f.id)&&parameter_name(&j,geo_json_member(&j,0,"name"),f.name)&&geo_json_integer(&j,geo_json_member(&j,0,"type"),&type)&&type>=0&&type<=2&&geo_json_canonical(&j,geo_json_member(&j,0,"expression"),f.expression,sizeof f.expression)){
            f.type=(int)type;ok=geo_parameters_stage_field(&w->geo.parameters,&f);
        }
    }
    geo_json_free(&j);if(ok)return true;
fail:scene_error(path,line_no,g_parameter_error[0]?g_parameter_error:"I39: invalid parameter block record");return false;
}
