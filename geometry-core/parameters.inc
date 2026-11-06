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
/* H candidate-order types; the K store and the legacy type-name shim stay free of them. */
#define PARAM_DECLARATION_MAX 512
#define PARAM_FIELD_RETIREMENT_MAX (PARAM_FIELD_MAX * PARAM_FIELDS_PER_CARD)
#define PARAM_DELETED_VALUE_MAX (PARAM_FIELD_RETIREMENT_MAX + PARAM_FIELD_MAX)
typedef struct {
    uint32_t parameter_id, field_id;
    unsigned generation;
    int type;
    GeoQuantity value;
} DeletedParameterValue;

/* Candidate ordering, never incarnation marks or serialized identities. */
typedef struct { uint32_t parameter_id, field_id; unsigned at; } ParameterFieldRetirement;
typedef struct { int kind; uint32_t id; int slot; unsigned at; } ParameterDeclaration;
/* R60: one direct unbind of a whole-card grid source, read at its ordered step.
 * At most one per engineering operation (ENG_OPERATION_MAX); preview-only. */
#define PARAM_CARD_CAPTURE_MAX 256
typedef struct { uint32_t id, parameter_id, fields[2]; Coord values[2]; unsigned at; } GridCardCapture;
enum { PARAM_OWNER_CARD, PARAM_OWNER_ENG_GRID, PARAM_OWNER_ENG_TIMBER,
       PARAM_OWNER_ASSEMBLY, PARAM_OWNER_MEMBER, PARAM_OWNER_RUN,
       PARAM_OWNER_GUIDE, PARAM_OWNER_DATUM, PARAM_OWNER_GRID_SYSTEM, PARAM_OWNER_GRID,
       PARAM_OWNER_PANEL_FILL, PARAM_OWNER_GRID_CARD };
/* P-062/P-065/P-121: H-owned scratch for exactly one tracked candidate
 * evaluation (the bridge batch transaction or one interactive archive record).
 * It is allocated beside the candidate, never inside World, a K store, a seal,
 * history or an exchange format. Last-valid values before a card or its
 * upstream disappears may be captured, but only explicitly unbound deleted
 * sources can consume them. `world` is the candidate snapshot it belongs to. */
typedef struct ParameterCandidateLedger {
    const void *world;
    struct ParameterCandidateLedger *outer; /* enclosing tracked candidate, if any */
    DeletedParameterValue deleted_values[PARAM_DELETED_VALUE_MAX]; size_t deleted_value_count;
    ParameterFieldRetirement field_retirements[PARAM_FIELD_RETIREMENT_MAX]; size_t field_retirement_count;
    ParameterDeclaration declarations[PARAM_DECLARATION_MAX]; size_t declaration_count;
    GridCardCapture card_captures[PARAM_CARD_CAPTURE_MAX]; size_t card_capture_count;
    unsigned candidate_order;
} ParameterCandidateLedger;
/* P-062/P-065/P-121 candidate scratch. The ledger is H state beside exactly
 * one tracked candidate (see ParameterCandidateLedger); nothing here is ever
 * written into World, the K parameter store, a candidate seal or history.
 * Outside a tracked candidate every recorder is a no-op and every reader sees
 * an empty ledger, exactly like the untracked train-18 ParameterState. */
static ParameterCandidateLedger *g_parameter_ledger;
static ParameterCandidateLedger *parameter_ledger(const World *w)
{return g_parameter_ledger&&g_parameter_ledger->world==(const void *)w?g_parameter_ledger:NULL;}
typedef struct {ParameterCandidateLedger *ledger;} ParameterCandidateScope;
static bool parameters_begin_candidate(World *w,ParameterCandidateScope *scope)
{
    scope->ledger=calloc(1,sizeof *scope->ledger);
    if(!scope->ledger)return parameter_fail("UNSUPPORTED/CAPACITY: candidate parameter ledger memory");
    scope->ledger->world=w;scope->ledger->outer=g_parameter_ledger;g_parameter_ledger=scope->ledger;return true;
}
/* I39/P-062: the scratch ends with its candidate operations; no deleted value,
 * retirement or declaration reaches comparison, staging, or history. */
static void parameters_end_candidate(ParameterCandidateScope *scope)
{
    /* Unlink from wherever it sits, so an out-of-order end can never leave an
     * inner scope (or the global) pointing at freed memory. */
    if(!scope->ledger)return;
    for(ParameterCandidateLedger **at=&g_parameter_ledger;*at;at=&(*at)->outer)
        if(*at==scope->ledger){*at=scope->ledger->outer;break;}
    free(scope->ledger);scope->ledger=NULL;
}
/* I38/R33: an intermediate unbind needs its current source closure, not unrelated fields.
 * Use fresh marks so values changed earlier in this candidate are never read from an old cache.
 * The complete candidate still goes through parameters_rebuild at transaction validation. */
static bool parameter_current_closure_valid(const World *w,int index,bool visited[PARAM_FIELD_MAX]);
static bool parameters_evaluate_refs(World *w,const ParameterRef *refs,size_t count,char *error,size_t cap)
{
    g_parameter_error[0]=0;GeoParameterEvaluation *e=geo_parameter_evaluation_create(&w->geo.parameters,NULL,NULL);
    if(!e){snprintf(error,cap,"UNSUPPORTED/CAPACITY: parameter evaluation memory");return false;}
    bool ok=!w->app.parameter_loading;
    if(!ok)parameter_fail("I39: unterminated parameter block");
    for(size_t i=0;i<count&&ok;++i){
        int index=parameter_field_index(w,refs[i].parameter_id,refs[i].field_id);
        if(index<0)ok=parameter_fail("I38 MISSING: parameter %u field %u",refs[i].parameter_id,refs[i].field_id);
        else {bool visited[PARAM_FIELD_MAX]={0};GeoQuantity value;ok=parameter_current_closure_valid(w,index,visited);
            if(ok&&!geo_parameter_evaluation_field(e,refs[i],&value))ok=parameter_kernel_error(w,geo_parameter_evaluation_error(e));}
    }
    geo_parameter_evaluation_destroy(e);if(!ok)snprintf(error,cap,"%s",g_parameter_error);return ok;
}

static bool parameter_name(GeoJson *j,int t,char out[PARAM_NAME_MAX])
{
    if(!geo_json_string(j,t,out,PARAM_NAME_MAX)||!geo_utf8_name_valid((const unsigned char*)out,strlen(out),PARAM_NAME_MAX-1))return parameter_fail("I38 NAME: expected 1..96 UTF-8 bytes without control characters");return true;
}
/* P-121/P-122: an ended field cannot silently reconnect an old referrer.
 * Events are retained (including repeated deletion); only explicit declarations
 * after the last deletion acknowledge the new source. Allocation never reads this.
 * Native scene definitions do not create transaction-order metadata. */
static unsigned parameter_declared_at(const World *w,int kind,uint32_t id,int slot)
{
    const ParameterCandidateLedger *p=parameter_ledger(w);
    for(size_t i=0;p&&i<p->declaration_count;++i){const ParameterDeclaration *d=&p->declarations[i];
        if(d->kind==kind&&d->id==id&&d->slot==slot)return d->at;}
    return 0;
}
static bool parameter_declare(World *w,int kind,uint32_t id,int slot)
{
    ParameterCandidateLedger *p=parameter_ledger(w);if(!p)return true;
    size_t i=0;while(i<p->declaration_count&&(p->declarations[i].kind!=kind||p->declarations[i].id!=id||p->declarations[i].slot!=slot))++i;
    if(i==p->declaration_count){if(i==PARAM_DECLARATION_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: candidate reference declarations");++p->declaration_count;}
    p->declarations[i]=(ParameterDeclaration){kind,id,slot,++p->candidate_order};return true;
}
static unsigned parameter_field_generation(const World *w,uint32_t id,uint32_t field)
{
    unsigned at=0;const ParameterCandidateLedger *p=parameter_ledger(w);
    for(size_t i=0;p&&i<p->field_retirement_count;++i){const ParameterFieldRetirement *r=&p->field_retirements[i];
        if(r->parameter_id==id&&r->field_id==field&&r->at>at)at=r->at;}
    return at;
}
static bool parameter_retire_field(World *w,uint32_t id,uint32_t field)
{
    identity_note_key(APP_IDENTITY_FIELD,id,field);
    ParameterCandidateLedger *p=parameter_ledger(w);if(!p)return true;
    if(p->field_retirement_count==PARAM_FIELD_RETIREMENT_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: candidate field deletions");
    p->field_retirements[p->field_retirement_count++]=(ParameterFieldRetirement){id,field,++p->candidate_order};return true;
}
/* K asks whether this candidate removed the key it is asked to rebuild (I38). */
static bool parameter_rebuilt_key(void *state,uint32_t id,uint32_t field)
{return parameter_field_generation((const World *)state,id,field)!=0;}
static bool parameter_reference_unhandled(const World *w,uint32_t id,uint32_t field,int kind,uint32_t owner,int slot)
{ return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }
static int parameter_engineering_owner(const EngTarget *target)
{return target->kind?PARAM_OWNER_ENG_TIMBER:PARAM_OWNER_ENG_GRID;}
static int parameter_engineering_slot(const EngTarget *target,int override)
{return target->axis*2+target->field+override*4;}
/* A cached deleted-source value must never be refreshed through an unrelated
 * incarnation occupying the same key. Only the affected dependency closure is
 * inspected; unrelated intermediate invalid definitions remain permitted. */
static bool parameter_current_ast_valid(const World *w,const ParameterField *owner,const GeoJson *j,int t,bool visited[PARAM_FIELD_MAX],int depth)
{
    if(depth>32)return true;char op[16];
    if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return true;
    if(!strcmp(op,"ref")){
        int64_t id=-1,field=-1;
        if(!geo_json_integer(j,geo_json_member(j,t,"parameterId"),&id)||!geo_json_integer(j,geo_json_member(j,t,"fieldId"),&field)||id<0||id>UINT32_MAX||field<0||field>UINT32_MAX)return true;
        int next=parameter_field_index(w,(uint32_t)id,(uint32_t)field);
        /* Missing targets retain the evaluator's existing named dependency path.
         * This extra guard is needed when an unrelated definition reoccupies a key. */
        if(next>=0&&parameter_reference_unhandled(w,(uint32_t)id,(uint32_t)field,PARAM_OWNER_CARD,owner->parameter_id,0)){
            parameter_fail("I38 MISSING: parameter %u field %u was deleted; parameter %u field %u must be explicitly redeclared after the last deletion",(uint32_t)id,(uint32_t)field,owner->parameter_id,owner->id);
            const ParameterSet *card=parameter_find(w,owner->parameter_id);
            parameter_wrap_error(owner->parameter_id,owner->id,card?card->name:"",owner->name);return false;
        }
        return next<0||parameter_current_closure_valid(w,next,visited);
    }
    int left=geo_json_member(j,t,"left"),right=geo_json_member(j,t,"right");
    return (left<0||parameter_current_ast_valid(w,owner,j,left,visited,depth+1))&&
           (right<0||parameter_current_ast_valid(w,owner,j,right,visited,depth+1));
}
static bool parameter_current_closure_valid(const World *w,int index,bool visited[PARAM_FIELD_MAX])
{
    const ParameterCandidateLedger *p=parameter_ledger(w);
    if(!p||!p->field_retirement_count||visited[index])return true;visited[index]=true;
    const ParameterField *f=&geo_parameters_fields(&w->geo.parameters)[index];GeoJson j;
    bool ok=geo_json_parse_n(&j,f->expression,strlen(f->expression));
    if(ok)ok=parameter_current_ast_valid(w,f,&j,0,visited,0);geo_json_free(&j);return ok;
}
/* P-065/P-141: a currently present source is evaluated at the unbind step.
 * Only an actually absent field may use its binding's ended-generation value. */
static bool parameter_unbind_generation(const World *w,ParameterRef ref,int kind,uint32_t owner,int slot,unsigned *generation)
{
    if(parameter_field_index(w,ref.parameter_id,ref.field_id)>=0)return false;
    const ParameterCandidateLedger *p=parameter_ledger(w);if(!p)return false;
    unsigned declared=parameter_declared_at(w,kind,owner,slot),previous=0;
    for(size_t i=0;i<p->field_retirement_count;++i){const ParameterFieldRetirement *r=&p->field_retirements[i];
        if(r->parameter_id!=ref.parameter_id||r->field_id!=ref.field_id)continue;
        if(r->at>declared){*generation=previous;return true;}previous=r->at;
    }
    return false;
}
static bool parameter_capture_deleted_values(World *w,uint32_t id);
static bool parameter_put(World *w,GeoJson *j,int t)
{
    uint32_t id;if(!geo_json_keys(j,t,"id,name,fields","nextFieldId")||!parameter_u32(j,geo_json_member(j,t,"id"),&id))return parameter_fail("I38 CARD: expected id, name and fields");
    ParameterSet card;geo_parameters_begin_definition(&w->geo.parameters,id,&card);if(!parameter_name(j,geo_json_member(j,t,"name"),card.name))return false;
    const ParameterSet *old=parameter_find(w,id);
    int fields=geo_json_member(j,t,"fields");if(!geo_json_is_array(j,fields)||geo_json_size(j,fields)<1||geo_json_size(j,fields)>PARAM_FIELDS_PER_CARD)return parameter_fail("UNSUPPORTED/CAPACITY: card requires 1..16 fields");
    ParameterField *fresh=calloc(PARAM_FIELDS_PER_CARD,sizeof *fresh);if(!fresh)return parameter_fail("UNSUPPORTED/CAPACITY: parameter fields memory");
    bool ok=true;GeoParameterError issue;card.count=(size_t)geo_json_size(j,fields);
    for(size_t k=0;k<card.count&&ok;++k){int f=geo_json_at(j,fields,(int)k);ParameterField *v=&fresh[k];char type[20];v->parameter_id=id;
        int input=geo_json_member(j,f,"input"),expr=geo_json_member(j,f,"expression");
        if((input>=0)==(expr>=0)||!geo_json_keys(j,f,input>=0?"id,name,type,input":"id,name,type,expression","")||!parameter_u32(j,geo_json_member(j,f,"id"),&v->id)||!parameter_name(j,geo_json_member(j,f,"name"),v->name)||!geo_json_string(j,geo_json_member(j,f,"type"),type,sizeof type)){ok=parameter_fail("I38 FIELD: invalid field definition");break;}
        v->type=!strcmp(type,"dimension")?0:!strcmp(type,"count")?1:!strcmp(type,"ratio")?2:-1;if(v->type<0){ok=parameter_fail("I38 TYPE: dimension/count/ratio required");break;}
        /* I38: a field key retired earlier in this same candidate may be rebuilt. */
        if(!geo_parameters_accept_rebuilt_field(&w->geo.parameters,&card,fresh,k,parameter_rebuilt_key,w,&issue)){ok=parameter_kernel_error(w,&issue);break;}
        if(input>=0){char text[PARAM_EXPR_MAX];if(!geo_json_string(j,input,text,sizeof text))ok=parameter_fail("UNSUPPORTED/CAPACITY: parameter input exceeds 2047 bytes");else if(!parameter_input(text,v->type,v->expression))ok=false;}
        else if(!geo_json_canonical(j,expr,v->expression,sizeof v->expression))ok=parameter_fail("UNSUPPORTED/CAPACITY: expression record exceeds capacity");
        if(!ok)parameter_wrap_error(id,v->id,card.name,v->name);
    }
    uint32_t next;int nt=geo_json_member(j,t,"nextFieldId");if(ok&&nt>=0){if(!parameter_u32(j,nt,&next))ok=false;else if(!geo_parameters_next_field(&card,next,&issue))ok=parameter_kernel_error(w,&issue);}
    /* K validates the complete put (including capacity) before any candidate-order effect. */
    if(ok&&!geo_parameters_check_put(&w->geo.parameters,&card,fresh,parameter_rebuilt_key,w,&issue))ok=parameter_kernel_error(w,&issue);
    /* P-065/B5: preserve the current affected closure before overwriting its definitions.
     * Only explicit unbind of an actually deleted source can consume this history. */
    if(ok&&old&&!parameter_capture_deleted_values(w,id))ok=false;
    if(ok&&old)for(size_t i=0;i<old->count&&ok;++i){bool retained=false;
        for(size_t k=0;k<card.count;++k)if(old->fields[i]==fresh[k].id)retained=true;
        if(!retained)ok=parameter_retire_field(w,id,old->fields[i]);}
    if(ok)ok=parameter_declare(w,PARAM_OWNER_CARD,id,0);
    if(ok&&!geo_parameters_put_rebuilt(&w->geo.parameters,&card,fresh,parameter_rebuilt_key,w,&issue))ok=parameter_kernel_error(w,&issue);
    free(fresh);return ok;
}
/* I38: enumerate actual references in a complete candidate. Only the first
 * PARAMETER_USES_SHOWN referrers are named; the count is exact. References from the card's own fields vanish with it. */
#define PARAMETER_USES_SHOWN 3
#define PARAMETER_USE_NAME 96 /* longest owner name is 56 bytes (grid-system card-reference) */
/* count covers every owner; native_* and other_* split the same owners by whether
 * this candidate can redeclare them. Each list keeps its first complete names. */
typedef struct {char text[PARAMETER_USES_SHOWN][PARAMETER_USE_NAME],native_text[PARAMETER_USES_SHOWN][PARAMETER_USE_NAME],
                other_text[PARAMETER_USES_SHOWN][PARAMETER_USE_NAME];size_t count,native_count,other_count;} ParameterUses;
static void parameter_use_list(char names[][PARAMETER_USE_NAME],size_t *count,const char *owner)
{
    if(*count<PARAMETER_USES_SHOWN)snprintf(names[*count],PARAMETER_USE_NAME,"%s",owner);
    ++*count;
}
static void parameter_use(ParameterUses *u,const char *format,...)
{
    char owner[PARAMETER_USE_NAME];va_list a;va_start(a,format);vsnprintf(owner,sizeof owner,format,a);va_end(a);
    parameter_use_list(u->text,&u->count,owner);
    parameter_use_list(u->other_text,&u->other_count,owner);
}
/* These owners have no declaration operation in an engineering candidate:
 * guide, datum, direct grid DSL axis tokens and panel-fill. Grid-system field
 * references are not among them; put-grid-system redeclares them (P-142 S1). */
static void parameter_native_use(ParameterUses *u,const char *format,...)
{
    char owner[PARAMETER_USE_NAME];va_list a;va_start(a,format);vsnprintf(owner,sizeof owner,format,a);va_end(a);
    parameter_use_list(u->text,&u->count,owner);
    parameter_use_list(u->native_text,&u->native_count,owner);
}
static void parameter_append(char *out,size_t cap,const char *text)
{
    size_t n=strlen(out);if(n+1<cap)snprintf(out+n,cap-n,"%s",text);
}
/* P-142 B2 review: I38 diagnostics reach every caller through g_engineering_error.
 * Write only complete owner names that fit in `room` bytes after `lead` and count the
 * rest as " and N more"; when no name fits, write nothing (the caller states the count).
 * `out` holds room+1 bytes. Returns the bytes written. */
static size_t parameter_names_fit(char *out,size_t room,char names[][PARAMETER_USE_NAME],size_t count,const char *lead)
{
    out[0]=0;
    for(size_t k=count<PARAMETER_USES_SHOWN?count:PARAMETER_USES_SHOWN;k>0;--k){
        char more[40]="";if(count>k)snprintf(more,sizeof more," and %zu more",count-k);
        size_t need=strlen(lead)+strlen(more);for(size_t i=0;i<k;++i)need+=(i?2:0)+strlen(names[i]);
        if(need>room)continue;
        parameter_append(out,room+1,lead);
        for(size_t i=0;i<k;++i){if(i)parameter_append(out,room+1,"; ");parameter_append(out,room+1,names[i]);}
        parameter_append(out,room+1,more);return strlen(out);
    }
    return 0;
}
static bool parameter_ast_uses(const GeoJson *j,int t,uint32_t id,uint32_t field,int depth)
{
    if(depth>32)return false;
    char op[16];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return false;
    if(!strcmp(op,"ref")){int64_t card=-1,f=-1;return geo_json_integer(j,geo_json_member(j,t,"parameterId"),&card)&&card==(int64_t)id&&geo_json_integer(j,geo_json_member(j,t,"fieldId"),&f)&&f==(int64_t)field;}
    int left=geo_json_member(j,t,"left"),right=geo_json_member(j,t,"right");
    return (left>=0&&parameter_ast_uses(j,left,id,field,depth+1))||(right>=0&&parameter_ast_uses(j,right,id,field,depth+1));
}
/* Position expressions (guides, datums) carry `param:<card>:<field>` tokens. */
static bool parameter_text_uses(const char *text,uint32_t id,uint32_t field)
{
    for(const char *p=text;(p=strstr(p,"param:"))!=NULL;p+=6){
        const char *q=p+6;uint64_t card=0;int digits=0;
        while(*q>='0'&&*q<='9'&&digits<11){card=card*10+(uint64_t)(*q++-'0');++digits;}
        if(digits&&digits<11&&*q==':'&&card==id){uint64_t f=0;int fd=0;++q;
            while(*q>='0'&&*q<='9'&&fd<11){f=f*10+(uint64_t)(*q++-'0');++fd;}
            if(fd&&fd<11&&f==field)return true;}
    }
    return false;
}
/* Referrers live in their GEO-261 owners: K parameter/grid/guide/datum stores,
 * W engineering/assembly/grid-application/panel-fill/section-profile state and
 * the H guide/datum source texts. */
static size_t parameter_uses(const World *w,uint32_t id,uint32_t field,ParameterUses *u)
{
    static const char *const axis_fields[6]={"phase","step","panel","gap","anchor","stagger"};
    memset(u,0,sizeof *u);
    const ParameterField *fields=geo_parameters_fields(&w->geo.parameters);
    for(size_t i=0;i<geo_parameters_field_count(&w->geo.parameters);++i){const ParameterField *f=&fields[i];
        if(!parameter_reference_unhandled(w,id,field,PARAM_OWNER_CARD,f->parameter_id,0))continue;
        GeoJson j;bool hit=geo_json_parse_n(&j,f->expression,strlen(f->expression))&&parameter_ast_uses(&j,0,id,field,0);geo_json_free(&j);
        if(hit)parameter_use(u,"parameter %u field %u",f->parameter_id,f->id);
    }
    for(size_t i=0;i<w->wood.engineering.binding_count;++i){const EngBinding *b=&w->wood.engineering.bindings[i];
        for(int override=0;override<2;++override){const EngDimensionSource *s=override?&b->override_value:&b->source;
            if((override&&!b->has_override)||s->kind!=ENG_PARAMETER||s->parameter.parameter_id!=id||s->parameter.field_id!=field||
               !parameter_reference_unhandled(w,id,field,parameter_engineering_owner(&b->target),b->target.id,parameter_engineering_slot(&b->target,override)))continue;
            if(b->target.kind)parameter_use(u,"timber %u %c%s",b->target.id,b->target.field?'B':'A',override?" override":"");
            else parameter_use(u,"grid %u %c %s%s",b->target.id,b->target.axis?'v':'u',b->target.field?"gap":"panel",override?" override":"");
        }
    }
    for(size_t i=0;i<w->wood.assembly.binding_count;++i){const AsmBinding *b=&w->wood.assembly.bindings[i];GeoJson j;
        if(app_json_parse(&j,b->content)){int slots=geo_json_member(&j,0,"slots");
            for(int k=0;k<geo_json_size(&j,slots);++k){int slot=geo_json_at(&j,slots,k);int64_t slot_id=0;
                (void)geo_json_integer(&j,geo_json_member(&j,slot,"slotId"),&slot_id);
                for(int axis=0;axis<2;++axis){int source=geo_json_member(&j,slot,axis?"B":"A");char kind[16];int64_t card=-1,f=-1;
                    if(geo_json_string(&j,geo_json_member(&j,source,"kind"),kind,sizeof kind)&&!strcmp(kind,"parameter")&&
                       geo_json_integer(&j,geo_json_member(&j,source,"parameterId"),&card)&&card==(int64_t)id&&
                       geo_json_integer(&j,geo_json_member(&j,source,"fieldId"),&f)&&f==(int64_t)field&&
                       parameter_reference_unhandled(w,id,field,PARAM_OWNER_ASSEMBLY,b->id,0))
                        parameter_use(u,"binding %u slot %lld.%c",b->id,(long long)slot_id,axis?'B':'A');
                }
            }
        }
        geo_json_free(&j);
    }
    for(size_t i=0;i<geo_guides_count(&w->geo.guide_lines);++i){const GeoGuide *g=geo_guides_at(&w->geo.guide_lines,i);
        if(parameter_text_uses(app_guide_expression(w,g->id),id,field)&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GUIDE,g->id,0))parameter_native_use(u,"guide %u",g->id);}
    for(size_t i=0;i<geo_datums_count(&w->geo.datum_planes);++i){const GeoDatum *d=geo_datums_at(&w->geo.datum_planes,i);
        if(parameter_text_uses(app_datum_expression(w,d->id),id,field)&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_DATUM,d->id,0))parameter_native_use(u,"datum %u",d->id);}
    for(size_t i=0;i<geo_grid_systems_count(&w->geo.grid_store);++i){const GridSystem *s=geo_grid_systems_at(&w->geo.grid_store,i);const GridCardReference *r=&s->card_reference;
        if(r->set&&r->parameter_id==id&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID_CARD,s->id,0))for(int a=0;a<2;++a)if(r->fields[a]==field)parameter_use(u,"grid-system %u card-reference %c field %u",s->id,a?'v':'u',field);}
    /* P-142 S1: put-grid-system (slot 0) and unbind-grid-card-reference parameter
     * mode (axis*6+k+1) declare these in the candidate, so they are redeclarable. */
    for(size_t i=0;i<geo_grid_systems_count(&w->geo.grid_store);++i){const GridSystem *s=geo_grid_systems_at(&w->geo.grid_store,i);
        for(int axis=0;axis<2;++axis)for(int k=0;k<6;++k){const ParameterRef *r=&s->axis[axis].parameters[k];
            if(r->set&&r->parameter_id==id&&r->field_id==field&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID_SYSTEM,s->id,0)&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID_SYSTEM,s->id,axis*6+k+1))parameter_use(u,"grid-system %u %c %s",s->id,axis?'v':'u',axis_fields[k]);}}
    for(size_t i=0;i<w->wood.grid_applications.count;++i){const ReferenceGrid *g=&w->wood.grid_applications.items[i];if(g->from_system)continue;  /* system-derived copies are the system's own refs */
        for(int axis=0;axis<2;++axis)for(int k=0;k<6;++k){const ParameterRef *r=&g->axis[axis].parameters[k];
            if(r->set&&r->parameter_id==id&&r->field_id==field&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID,g->id,0))parameter_native_use(u,"grid %u %c %s",g->id,axis?'v':'u',axis_fields[k]);}}
    /* P-141/D44: panel-fill has no declaration op in this candidate. */
    for(size_t i=0;i<w->wood.finish_surfaces.fill_count;++i){const PanelFill *fill=&w->wood.finish_surfaces.fills[i];
        const ParameterRef *refs[3]={&fill->gap_ref,&fill->stagger_ref,&fill->threshold};
        static const char *const names[3]={"gap","stagger","threshold"};
        for(int k=0;k<3;++k){const ParameterRef *r=refs[k];
            if(r->set&&r->parameter_id==id&&r->field_id==field&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_PANEL_FILL,fill->id,k))
                parameter_native_use(u,"panel-fill %u %s",fill->id,names[k]);}
    }
    for(size_t i=0;i<w->wood.section_profiles.member_count;++i){const ProfileMember *m=&w->wood.section_profiles.members[i];
        if(m->a_source.kind==ENG_PARAMETER&&m->a_source.parameter.parameter_id==id&&m->a_source.parameter.field_id==field&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_MEMBER,m->id,0))parameter_use(u,"section-profile member %u A",m->id);
        if(m->b_source.kind==ENG_PARAMETER&&m->b_source.parameter.parameter_id==id&&m->b_source.parameter.field_id==field&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_MEMBER,m->id,0))parameter_use(u,"section-profile member %u B",m->id);
    }
    for(size_t i=0;i<w->wood.section_profiles.run_count;++i){const ProfileRun *r=&w->wood.section_profiles.runs[i];
        if(r->length_source.kind==ENG_PARAMETER&&r->length_source.parameter.parameter_id==id&&r->length_source.parameter.field_id==field&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_RUN,r->id,0))parameter_use(u,"section-profile run %u length",r->id);
    }
    return u->count;
}
/* I38/R33: inspect missing sources only after the complete candidate is defined. */
static bool parameter_retirements_valid(const World *w)
{
    const ParameterCandidateLedger *p=parameter_ledger(w);
    for(size_t i=0;p&&i<p->field_retirement_count;++i){
        const ParameterFieldRetirement *r=&p->field_retirements[i];uint32_t id=r->parameter_id;ParameterUses uses;
        if(r->at!=parameter_field_generation(w,id,r->field_id))continue; /* last actual deletion */
        if(parameter_uses(w,id,r->field_id,&uses)){
            /* The whole message stays within the g_engineering_error copy (255 bytes). */
            const size_t limit=sizeof g_engineering_error-1;
            char head[64],names[sizeof g_engineering_error],other[sizeof g_engineering_error],count[24];
            snprintf(head,sizeof head,"I38 MISSING: parameter %u is still referenced by ",id);
            if(uses.native_count){
                /* I38/I74 (P-142 B2): every unhandled referrer is named, including the
                 * redeclarable ones that share this field with a native-only owner. */
                static const char guidance[]="; 先在原生 DSL 或該物件自己的交易裡改掉引用，另成一筆後再刪 (other references: ";
                snprintf(count,sizeof count,"%zu",uses.count-uses.native_count);
                size_t used=strlen(head)+strlen(guidance)+strlen(count)+1; /* closing parenthesis */
                used+=parameter_names_fit(names,used<limit?limit-used:0,uses.native_text,uses.native_count,"");
                parameter_names_fit(other,used<limit?limit-used:0,uses.other_text,uses.other_count,": ");
                return parameter_fail("%s%s%s%s%s)",head,names,guidance,count,other);
            }
            const char *tail=uses.count==1?"; unbind or repoint it in the same complete candidate":"; unbind or repoint them in the same complete candidate";
            size_t used=strlen(head)+strlen(tail);
            parameter_names_fit(names,used<limit?limit-used:0,uses.text,uses.count,"");
            return parameter_fail("%s%s%s",head,names,tail);
        }
    }
    return true;
}
/* P-129: preview disclosure reads explicit owner declarations, including a
 * reference that the declaration replaced with a literal/different source.
 * It does not grant new declaration paths to native-DSL-only consumers.
 * Grid-system owners are not native-only: GEO-262 put-grid-system and
 * unbind-grid-card-reference are their declaration paths (P-142 S1). */
static bool parameter_declared_owner_present(const World *w,const ParameterDeclaration *d)
{
    if(d->kind==PARAM_OWNER_CARD)return parameter_find(w,d->id)!=NULL;
    if(d->kind==PARAM_OWNER_GRID_CARD||d->kind==PARAM_OWNER_GRID_SYSTEM)return world_find_grid_system(w,d->id)!=NULL;
    if(d->kind==PARAM_OWNER_ENG_GRID||d->kind==PARAM_OWNER_ENG_TIMBER){
        for(size_t i=0;i<w->wood.engineering.binding_count;++i){const EngBinding *b=&w->wood.engineering.bindings[i];
            if(b->target.id==d->id&&parameter_engineering_owner(&b->target)==d->kind&&
               parameter_engineering_slot(&b->target,0)==d->slot%4)return true;}
    }else if(d->kind==PARAM_OWNER_ASSEMBLY){for(size_t i=0;i<w->wood.assembly.binding_count;++i)if(w->wood.assembly.bindings[i].id==d->id)return true;}
    else if(d->kind==PARAM_OWNER_MEMBER){for(size_t i=0;i<w->wood.section_profiles.member_count;++i)if(w->wood.section_profiles.members[i].id==d->id)return true;}
    else if(d->kind==PARAM_OWNER_RUN){for(size_t i=0;i<w->wood.section_profiles.run_count;++i)if(w->wood.section_profiles.runs[i].id==d->id)return true;}
    return false;
}
static bool parameter_declared_owner_uses(const World *w,const ParameterDeclaration *d,uint32_t id,uint32_t field)
{
    const GridSystem *gs=(d->kind==PARAM_OWNER_GRID_CARD||d->kind==PARAM_OWNER_GRID_SYSTEM)?world_find_grid_system(w,d->id):NULL;
    if(gs&&d->kind==PARAM_OWNER_GRID_CARD)return gs->card_reference.set&&gs->card_reference.parameter_id==id&&(gs->card_reference.fields[0]==field||gs->card_reference.fields[1]==field);
    if(gs&&d->kind==PARAM_OWNER_GRID_SYSTEM){for(int a=0;a<2;++a)for(int k=0;k<6;++k){if(d->slot&&d->slot!=a*6+k+1)continue;ParameterRef r=gs->axis[a].parameters[k];if(r.set&&r.parameter_id==id&&r.field_id==field)return true;}return false;}
    if(d->kind==PARAM_OWNER_CARD){
        const ParameterField *fields=geo_parameters_fields(&w->geo.parameters);
        for(size_t i=0;i<geo_parameters_field_count(&w->geo.parameters);++i){const ParameterField *f=&fields[i];if(f->parameter_id!=d->id)continue;
            GeoJson j;bool hit=geo_json_parse_n(&j,f->expression,strlen(f->expression))&&parameter_ast_uses(&j,0,id,field,0);geo_json_free(&j);if(hit)return true;}
    }else if(d->kind==PARAM_OWNER_ENG_GRID||d->kind==PARAM_OWNER_ENG_TIMBER){
        for(size_t i=0;i<w->wood.engineering.binding_count;++i){const EngBinding *b=&w->wood.engineering.bindings[i];
            if(b->target.id!=d->id||parameter_engineering_owner(&b->target)!=d->kind)continue;
            for(int override=0;override<2;++override){const EngDimensionSource *s=override?&b->override_value:&b->source;
                if((!override||b->has_override)&&parameter_engineering_slot(&b->target,override)==d->slot&&s->kind==ENG_PARAMETER&&s->parameter.parameter_id==id&&s->parameter.field_id==field)return true;}
        }
    }else if(d->kind==PARAM_OWNER_ASSEMBLY){
        for(size_t i=0;i<w->wood.assembly.binding_count;++i){const AsmBinding *b=&w->wood.assembly.bindings[i];if(b->id!=d->id)continue;GeoJson j;bool hit=false;
            if(app_json_parse(&j,b->content)){int slots=geo_json_member(&j,0,"slots");
                for(int k=0;k<geo_json_size(&j,slots)&&!hit;++k)for(int axis=0;axis<2&&!hit;++axis){
                    int source=geo_json_member(&j,geo_json_at(&j,slots,k),axis?"B":"A");char kind[16];int64_t card=-1,f=-1;
                    hit=geo_json_string(&j,geo_json_member(&j,source,"kind"),kind,sizeof kind)&&!strcmp(kind,"parameter")&&geo_json_integer(&j,geo_json_member(&j,source,"parameterId"),&card)&&card==(int64_t)id&&geo_json_integer(&j,geo_json_member(&j,source,"fieldId"),&f)&&f==(int64_t)field;}}
            geo_json_free(&j);if(hit)return true;
        }
    }else if(d->kind==PARAM_OWNER_MEMBER){
        for(size_t i=0;i<w->wood.section_profiles.member_count;++i){const ProfileMember *m=&w->wood.section_profiles.members[i];if(m->id!=d->id)continue;
            const EngDimensionSource *s[2]={&m->a_source,&m->b_source};for(int k=0;k<2;++k)if(s[k]->kind==ENG_PARAMETER&&s[k]->parameter.parameter_id==id&&s[k]->parameter.field_id==field)return true;}
    }else if(d->kind==PARAM_OWNER_RUN){
        for(size_t i=0;i<w->wood.section_profiles.run_count;++i){const ProfileRun *r=&w->wood.section_profiles.runs[i];if(r->id==d->id&&r->length_source.kind==ENG_PARAMETER&&r->length_source.parameter.parameter_id==id&&r->length_source.parameter.field_id==field)return true;}
    }
    return false;
}
/* P-065: query only the dependency paths affected by an overwritten or removed card.
 * This is reachability, not evaluation: unrelated invalid definitions cannot block deletion. */
static bool parameter_field_depends_on(const World *w,int index,uint32_t id,bool visited[PARAM_FIELD_MAX]);
static bool parameter_ast_depends_on(const World *w,const GeoJson *j,int t,uint32_t id,bool visited[PARAM_FIELD_MAX],int depth)
{
    if(depth>32)return false;
    char op[16];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return false;
    if(!strcmp(op,"ref")){
        int64_t card=-1,field=-1;
        if(!geo_json_integer(j,geo_json_member(j,t,"parameterId"),&card)||
           !geo_json_integer(j,geo_json_member(j,t,"fieldId"),&field)||card<0||card>UINT32_MAX||field<0||field>UINT32_MAX)return false;
        if((uint32_t)card==id)return true;
        int index=parameter_field_index(w,(uint32_t)card,(uint32_t)field);
        return index>=0&&parameter_field_depends_on(w,index,id,visited);
    }
    int left=geo_json_member(j,t,"left"),right=geo_json_member(j,t,"right");
    return (left>=0&&parameter_ast_depends_on(w,j,left,id,visited,depth+1))||
           (right>=0&&parameter_ast_depends_on(w,j,right,id,visited,depth+1));
}
static bool parameter_field_depends_on(const World *w,int index,uint32_t id,bool visited[PARAM_FIELD_MAX])
{
    const ParameterField *f=&geo_parameters_fields(&w->geo.parameters)[index];
    if(f->parameter_id==id)return true;
    if(visited[index])return false;visited[index]=true;
    GeoJson j;bool hit=geo_json_parse_n(&j,f->expression,strlen(f->expression))&&
        parameter_ast_depends_on(w,&j,0,id,visited,0);
    geo_json_free(&j);return hit;
}
/* P-062/P-065: refresh overwritten/removed fields and their affected dependants while
 * their current closures are still available. A later upstream deletion may make
 * evaluation impossible; preserve an earlier valid candidate snapshot in that case.
 * Ordinary evaluation and surviving unbind sources never read these snapshots.
 * Each field is re-evaluated by K with fresh marks over only its own closure. */
static bool parameter_capture_deleted_values(World *w,uint32_t id)
{
    ParameterCandidateLedger *p=parameter_ledger(w);
    if(!p)return true;  /* no tracked candidate: nothing can consume a deleted value */
    for(size_t i=0;i<geo_parameters_field_count(&w->geo.parameters);++i){
        const ParameterField *f=&geo_parameters_fields(&w->geo.parameters)[i];bool visited[PARAM_FIELD_MAX]={0};
        if(!parameter_field_depends_on(w,(int)i,id,visited))continue;
        g_parameter_error[0]=0;GeoParameterError issue;
        bool current[PARAM_FIELD_MAX]={0};
        if(!parameter_current_closure_valid(w,(int)i,current)||
           !geo_parameters_evaluate_field(&w->geo.parameters,(GeoParameterRef){true,f->parameter_id,f->id},&issue))continue;
        unsigned generation=parameter_field_generation(w,f->parameter_id,f->id);
        size_t saved_index=0;
        while(saved_index<p->deleted_value_count&&(p->deleted_values[saved_index].parameter_id!=f->parameter_id||
              p->deleted_values[saved_index].field_id!=f->id||p->deleted_values[saved_index].generation!=generation))++saved_index;
        if(saved_index==p->deleted_value_count){
            if(p->deleted_value_count==PARAM_DELETED_VALUE_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: deleted parameter values");
            ++p->deleted_value_count;
        }
        DeletedParameterValue *saved=&p->deleted_values[saved_index];
        memset(saved,0,sizeof *saved);saved->parameter_id=f->parameter_id;saved->field_id=f->id;saved->generation=generation;saved->type=f->type;
        saved->value.num=f->value.num;saved->value.den=f->value.den;saved->value.unit=f->value.unit;
    }
    g_parameter_error[0]=0;return true;
}
/* This lookup is intentionally absent from the ordinary parameter evaluator.
 * Surviving sources and all final definitions still require live references. */
static bool parameter_deleted_coord(const World *w,ParameterRef ref,unsigned generation,Coord *out)
{
    const ParameterCandidateLedger *p=parameter_ledger(w);
    { /* Caller proved this binding still refers to an ended source generation. */
        for(size_t i=0;p&&i<p->deleted_value_count;++i){
            const DeletedParameterValue *saved=&p->deleted_values[i];
            if(saved->parameter_id!=ref.parameter_id||saved->field_id!=ref.field_id||saved->generation!=generation)continue;
            if(saved->type!=0)return parameter_fail("I38 UNIT: deleted parameter %u field %u is not a dimension",ref.parameter_id,ref.field_id);
            if(saved->value.den!=1||!coord_in_range(saved->value.num))return parameter_fail("I38 GEOMETRY: deleted parameter %u field %u must resolve to integer mm in D1 range",ref.parameter_id,ref.field_id);
            *out=saved->value.num;return true;
        }
    }
    return parameter_fail("I38 MISSING: deleted parameter %u field %u has no valid value in this candidate",ref.parameter_id,ref.field_id);
}
static bool parameter_remove(World *w,uint32_t id)
{
    const ParameterSet *removed=parameter_find(w,id);
    if(!removed)return parameter_fail("I38 MISSING: parameter %u",id);
    identity_note_key(APP_IDENTITY_PARAMETER,id,0);
    if(!parameter_capture_deleted_values(w,id))return false;
    for(size_t i=0;i<removed->count;++i)if(!parameter_retire_field(w,id,removed->fields[i]))return false;
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
        /* R53/P-122: first unused in the candidate plus this import's allocation.
         * I38 protects old references independently of whether a key is reused. */
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
