/* parameters/1: the native evaluator is shared by bridge, scene and model CLI. */
#include "engineering_json.inc"
#include <stdarg.h>
#include <ctype.h>
static bool g_parameter_scene_loading;
static ParameterRef g_parameter_dimension_error;
static bool parameter_fail(const char *format,...)
{
    va_list a;va_start(a,format);vsnprintf(g_parameter_error,sizeof g_parameter_error,format,a);va_end(a);utf8_trim_tail(g_parameter_error);return false;
}
static int64_t parameter_gcd(int64_t a,int64_t b)
{ if(a<0)a=-a;while(b){int64_t r=a%b;a=b;b=r;}return a; }
static bool parameter_mul(int64_t a,int64_t b,int64_t *r)
{
    if(a==INT64_MIN||b==INT64_MIN)return parameter_fail("UNSUPPORTED/PRECISION: integer magnitude");
    int64_t x=a<0?-a:a,y=b<0?-b:b;
    if(y && x>INT64_MAX/y)return parameter_fail("UNSUPPORTED/PRECISION: exact multiplication exceeds int64");
    *r=a*b;return true;
}
static bool parameter_add(int64_t a,int64_t b,int64_t *r)
{
    if((b>0&&a>INT64_MAX-b)||(b<0&&a< -INT64_MAX-b))return parameter_fail("UNSUPPORTED/PRECISION: exact sum exceeds int64");
    *r=a+b;return true;
}
static ParamValue parameter_normal(ParamValue v)
{ int64_t g=parameter_gcd(v.num,v.den);v.num/=g;v.den/=g;return v; }
static bool parameter_binary(const char *op,ParamValue a,ParamValue b,ParamValue *r)
{
    if(!strcmp(op,"add")||!strcmp(op,"sub")){
        if(a.unit!=b.unit)return parameter_fail("I38 UNIT: addition/subtraction needs matching units");
        if(!strcmp(op,"sub"))b.num=-b.num;
        int64_t g=parameter_gcd(a.den,b.den),x,y,n,d;
        if(!parameter_mul(a.num,b.den/g,&x)||!parameter_mul(b.num,a.den/g,&y)||!parameter_add(x,y,&n)||!parameter_mul(a.den,b.den/g,&d))return false;
        *r=parameter_normal((ParamValue){n,d,a.unit});return true;
    }
    int unit;
    if(!strcmp(op,"mul")){
        if(a.unit&&b.unit)return parameter_fail("I38 UNIT: area/volume arithmetic is not supported");
        unit=a.unit+b.unit;
    }else if(!strcmp(op,"div")){
        if(!b.num)return parameter_fail("I38 DIV_ZERO: division by zero");
        if(!a.unit&&b.unit)return parameter_fail("I38 UNIT: inverse length is not supported");
        unit=a.unit-b.unit;int64_t n=b.num;b.num=b.den;b.den=n;
        if(b.den<0){b.den=-b.den;b.num=-b.num;}
    }else return parameter_fail("I38 OP: unknown arithmetic operation");
    int64_t g=parameter_gcd(a.num,b.den);a.num/=g;b.den/=g;
    g=parameter_gcd(b.num,a.den);b.num/=g;a.den/=g;
    if(!parameter_mul(a.num,b.num,&r->num)||!parameter_mul(a.den,b.den,&r->den))return false;
    r->unit=unit;*r=parameter_normal(*r);return true;
}
static const ParameterSet *parameter_find(const World *w,uint32_t id)
{for(size_t i=0;i<w->parameters.card_count;++i)if(w->parameters.cards[i].id==id)return &w->parameters.cards[i];return NULL;}
static int parameter_field_index(const World *w,uint32_t id,uint32_t field)
{for(size_t i=0;i<w->parameters.field_count;++i)if(w->parameters.fields[i].parameter_id==id&&w->parameters.fields[i].id==field)return (int)i;return -1;}
static bool parameter_u32(EngJson *j,int t,uint32_t *out)
{int64_t v;if(!eng_json_integer(j,t,&v)||v<0||v>UINT32_MAX)return parameter_fail("I38 ID: expected uint32 identity");*out=(uint32_t)v;return true;}
static bool parameter_integer(const char *s,int64_t *v)
{if(!s||!parse_i64(s,v)||*v==INT64_MIN)return parameter_fail("UNSUPPORTED/PRECISION: exact integer must fit signed int64 magnitude");return true;}
static bool parameter_ref_parse(const char *s,ParameterRef *r)
{
    if(strncmp(s,"param:",6))return false;
    char b[64];if(strlen(s)>=sizeof b)return false;snprintf(b,sizeof b,"%s",s+6);char *c=strchr(b,':');if(!c)return false;*c++=0;
    if(!parse_u32(b,&r->parameter_id)||!parse_u32(c,&r->field_id))return false;r->set=true;return true;
}
static bool parameter_value(const World *w,ParameterRef ref,ParamValue *v)
{
    g_parameter_dimension_error=(ParameterRef){0};
    int i=parameter_field_index(w,ref.parameter_id,ref.field_id);
    if(i<0)return parameter_fail("I38 MISSING: parameter %u field %u",ref.parameter_id,ref.field_id);
    const ParameterField *f=&w->parameters.fields[i];
    if(f->type!=0){g_parameter_dimension_error=ref;return parameter_fail("I38 UNIT: parameter %u field %u is not a dimension",ref.parameter_id,ref.field_id);}
    *v=f->value;return true;
}
static bool parameter_coord(const World *w,ParameterRef ref,Coord *out)
{
    ParamValue v;if(!parameter_value(w,ref,&v))return false;
    const ParameterSet *c=parameter_find(w,ref.parameter_id);const ParameterField *f=&w->parameters.fields[parameter_field_index(w,ref.parameter_id,ref.field_id)];
    if(v.den!=1||!coord_in_range(v.num))return parameter_fail("I38 GEOMETRY: [%u:%u %s.%s] must resolve to integer mm in D1 range (got %lld/%lld)",ref.parameter_id,ref.field_id,c->name,f->name,(long long)v.num,(long long)v.den);
    *out=v.num;return true;
}
/* Canonical AST is persisted; this bounded parser only translates input text. */
typedef struct {int op,left,right;ParamValue value;ParameterRef ref;} ParameterNode;
typedef struct {const char *p;ParameterNode nodes[PARAM_NODE_MAX];int count,depth;} ParameterParser;
static int parameter_text_sum(ParameterParser *p);
static void parameter_space(ParameterParser *p){while(*p->p==' '||*p->p=='\t')++p->p;}
static int parameter_node(ParameterParser *p,ParameterNode n)
{if(p->count==PARAM_NODE_MAX){parameter_fail("UNSUPPORTED/CAPACITY: expression exceeds 128 nodes");return -1;}p->nodes[p->count]=n;return p->count++;}
static bool parameter_decimal(const char **text,ParamValue *out)
{
    const char *p=*text;int64_t n=0,d=1;bool dot=false,any=false;
    while((*p>='0'&&*p<='9')||*p=='.'){
        if(*p=='.'){if(dot)return parameter_fail("I38 NUMBER: repeated decimal point");dot=true;++p;continue;}
        int digit=*p++-'0';any=true;
        if(n>(INT64_MAX-digit)/10||(dot&&d>INT64_MAX/10))return parameter_fail("UNSUPPORTED/PRECISION: decimal exceeds exact capacity");
        n=n*10+digit;if(dot)d*=10;
    }
    if(!any)return parameter_fail("I38 NUMBER: expected decimal number");
    *text=p;*out=parameter_normal((ParamValue){n,d,0});return true;
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
        if(*p.p=='/'){++p.p;parameter_space(&p);ParamValue d;if(!parameter_decimal(&p.p,&d)||!parameter_binary("div",n.value,d,&n.value))return false;}
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
typedef struct {World *w;unsigned char marks[PARAM_FIELD_MAX];unsigned char fdepth[PARAM_FIELD_MAX];int depth,maxref;uint32_t path_card[PARAM_DEPTH_MAX],path_field[PARAM_DEPTH_MAX];} ParameterEval;
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
static bool parameter_eval_field(ParameterEval *e,int index);
static bool parameter_eval_ast(ParameterEval *e,EngJson *j,int t,int depth,int *nodes,ParamValue *out)
{
    if(depth>32||++*nodes>PARAM_NODE_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: expression tree exceeds declared limits");
    char op[16];if(!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op))return parameter_fail("I38 AST: missing operation");
    if(!strcmp(op,"literal")){
        char num[40],den[40],unit[8];
        if(!eng_json_keys(j,t,"op,num,den,unit","")||!eng_json_string(j,eng_json_member(j,t,"num"),num,sizeof num)||!eng_json_string(j,eng_json_member(j,t,"den"),den,sizeof den)||!eng_json_string(j,eng_json_member(j,t,"unit"),unit,sizeof unit))return parameter_fail("I38 AST: invalid exact literal");
        if(!parameter_integer(num,&out->num)||!parameter_integer(den,&out->den))return false;
        if(out->den<=0)return parameter_fail("I38 NUMBER: denominator must be positive");
        if(strcmp(unit,"mm")&&strcmp(unit,"1"))return parameter_fail("I38 UNIT: expected mm or 1");
        out->unit=!strcmp(unit,"mm");*out=parameter_normal(*out);return true;
    }
    if(!strcmp(op,"ref")){
        uint32_t id,field;if(!eng_json_keys(j,t,"op,parameterId,fieldId","")||!parameter_u32(j,eng_json_member(j,t,"parameterId"),&id)||!parameter_u32(j,eng_json_member(j,t,"fieldId"),&field))return parameter_fail("I38 AST: invalid reference");
        int i=parameter_field_index(e->w,id,field);if(i<0)return parameter_fail("I38 MISSING: parameter %u field %u",id,field);
        if(!parameter_eval_field(e,i))return false;
        if(e->fdepth[i]>e->maxref)e->maxref=e->fdepth[i];  /* also on cache hits: the depth comes from the field, not the stack */
        *out=e->w->parameters.fields[i].value;return true;
    }
    bool neg=!strcmp(op,"neg");if(!neg&&strcmp(op,"add")&&strcmp(op,"sub")&&strcmp(op,"mul")&&strcmp(op,"div"))return parameter_fail("I38 OP: unsupported operation");
    if(!eng_json_keys(j,t,neg?"op,left":"op,left,right",""))return parameter_fail("I38 AST: invalid arithmetic node");
    ParamValue a,b;if(!parameter_eval_ast(e,j,eng_json_member(j,t,"left"),depth+1,nodes,&a))return false;
    if(neg){*out=a;out->num=-out->num;return true;}
    if(!parameter_eval_ast(e,j,eng_json_member(j,t,"right"),depth+1,nodes,&b))return false;
    return parameter_binary(op,a,b,out);
}
static bool parameter_eval_field(ParameterEval *e,int index)
{
    ParameterField *f=&e->w->parameters.fields[index];
    if(e->marks[index]==2)return true;  /* cached value; its dependency depth is e->fdepth[index] */
    if(e->marks[index]==1)return parameter_fail("I38 CYCLE: parameter %u field %u",f->parameter_id,f->id);
    if(e->depth==PARAM_DEPTH_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: dependency depth exceeds 64");
    e->marks[index]=1;e->path_card[e->depth]=f->parameter_id;e->path_field[e->depth++]=f->id;
    int outer_maxref=e->maxref;e->maxref=0;
    EngJson j;bool ok=eng_json_parse_n(&j,f->expression,strlen(f->expression));ParamValue value={0,1,0};int nodes=0;
    if(ok)ok=parameter_eval_ast(e,&j,0,0,&nodes,&value);else parameter_fail("I38 JSON: %s",j.error);
    eng_json_free(&j);
    if(ok&&value.unit!=(f->type==0))ok=parameter_fail("I38 UNIT: result unit does not match field type");
    if(ok&&f->type==1&&(value.num<0||value.den!=1))ok=parameter_fail("I38 COUNT: quantity must be a nonnegative integer");
    --e->depth;
    int own_depth=e->maxref+1;e->maxref=outer_maxref;
    if(ok&&own_depth>PARAM_DEPTH_MAX)ok=parameter_fail("UNSUPPORTED/CAPACITY: dependency depth exceeds 64");
    if(!ok){const ParameterSet *c=parameter_find(e->w,f->parameter_id);parameter_wrap_error(f->parameter_id,f->id,c?c->name:"?",f->name);return false;}
    /* Keep cache padding deterministic: World definition comparison includes these bytes. */
    memset(&f->value,0,sizeof f->value);
    f->value.num=value.num;f->value.den=value.den;f->value.unit=value.unit;
    e->fdepth[index]=(unsigned char)own_depth;e->marks[index]=2;return true;
}
static bool parameters_rebuild(World *w,char *error,size_t cap)
{
    g_parameter_error[0]=0;ParameterEval *e=calloc(1,sizeof *e);if(!e){snprintf(error,cap,"UNSUPPORTED/CAPACITY: parameter evaluation memory");return false;}e->w=w;
    bool ok=!w->parameters.loading;
    if(!ok)parameter_fail("I39: unterminated parameter block");
    for(size_t i=0;i<w->parameters.field_count&&ok;++i)ok=parameter_eval_field(e,(int)i);
    free(e);if(!ok)snprintf(error,cap,"%s",g_parameter_error);return ok;
}
static bool parameter_name(EngJson *j,int t,char out[PARAM_NAME_MAX])
{
    if(!eng_json_string(j,t,out,PARAM_NAME_MAX)||!grid_system_name_valid((const unsigned char*)out,strlen(out)))return parameter_fail("I38 NAME: expected 1..96 UTF-8 bytes without control characters");return true;
}
/* I38/I39 identity: a card identity deleted earlier in the SAME candidate (operation sequence) is retired for the rest of it.
 * Declaring it again (put-parameter) or letting an import allocate it would silently rebind every reference that still
 * names the old card to the new card. The list lives in the candidate World (ParameterState.retired), so a cancelled or
 * failed preview takes it along when the candidate is dropped, and batch_preview() / the `engineering archive` entry clear
 * it when their sequence ends: the identity is usable again in any later, separate transaction (nothing can still point
 * at it, because the committed World never holds a dangling reference). */
static bool parameter_retired(const World *w,uint32_t id)
{for(size_t i=0;i<w->parameters.retired_count;++i)if(w->parameters.retired[i]==id)return true;return false;}
static bool parameter_put(World *w,EngJson *j,int t)
{
    uint32_t id;if(!eng_json_keys(j,t,"id,name,fields","nextFieldId")||!parameter_u32(j,eng_json_member(j,t,"id"),&id))return parameter_fail("I38 CARD: expected id, name and fields");
    if(parameter_retired(w,id))return parameter_fail("I38 DUPLICATE: parameter %u was deleted earlier in this transaction; a deleted identity cannot be declared again",id);
    ParameterSet card={0};card.id=id;if(!parameter_name(j,eng_json_member(j,t,"name"),card.name))return false;
    int fields=eng_json_member(j,t,"fields");if(!eng_json_is_array(j,fields)||eng_json_size(j,fields)<1||eng_json_size(j,fields)>PARAM_FIELDS_PER_CARD)return parameter_fail("UNSUPPORTED/CAPACITY: card requires 1..16 fields");
    ParameterField *fresh=calloc(PARAM_FIELDS_PER_CARD,sizeof *fresh);if(!fresh)return parameter_fail("UNSUPPORTED/CAPACITY: parameter fields memory");
    bool ok=true;card.count=(size_t)eng_json_size(j,fields);const ParameterSet *old=parameter_find(w,id);card.next_field_id=old?old->next_field_id:1;
    for(size_t k=0;k<card.count&&ok;++k){int f=eng_json_at(j,fields,(int)k);ParameterField *v=&fresh[k];char type[20];v->parameter_id=id;
        int input=eng_json_member(j,f,"input"),expr=eng_json_member(j,f,"expression");
        if((input>=0)==(expr>=0)||!eng_json_keys(j,f,input>=0?"id,name,type,input":"id,name,type,expression","")||!parameter_u32(j,eng_json_member(j,f,"id"),&v->id)||!parameter_name(j,eng_json_member(j,f,"name"),v->name)||!eng_json_string(j,eng_json_member(j,f,"type"),type,sizeof type)){ok=parameter_fail("I38 FIELD: invalid field definition");break;}
        v->type=!strcmp(type,"dimension")?0:!strcmp(type,"count")?1:!strcmp(type,"ratio")?2:-1;if(v->type<0){ok=parameter_fail("I38 TYPE: dimension/count/ratio required");break;}
        for(size_t q=0;q<k;++q)if(fresh[q].id==v->id||!strcmp(fresh[q].name,v->name)){ok=parameter_fail("I38 DUPLICATE: field identity/name in parameter %u",id);break;}
        if(!ok)break;card.fields[k]=v->id;
        if(old && parameter_field_index(w,id,v->id)<0 && (old->next_field_id==0||v->id<old->next_field_id)){ok=parameter_fail("I38 ID: deleted field identities cannot be reused");break;}
        if(v->id==UINT32_MAX)card.next_field_id=0;else if(card.next_field_id&&v->id>=card.next_field_id)card.next_field_id=v->id+1;
        if(input>=0){char text[PARAM_EXPR_MAX];if(!eng_json_string(j,input,text,sizeof text))ok=parameter_fail("UNSUPPORTED/CAPACITY: parameter input exceeds 2047 bytes");else if(!parameter_input(text,v->type,v->expression))ok=false;}
        else if(!eng_json_canonical(j,expr,v->expression,sizeof v->expression))ok=parameter_fail("UNSUPPORTED/CAPACITY: expression record exceeds capacity");
        if(!ok)parameter_wrap_error(id,v->id,card.name,v->name);
    }
    uint32_t next;int nt=eng_json_member(j,t,"nextFieldId");if(ok&&nt>=0){if(!parameter_u32(j,nt,&next))ok=false;else if(card.next_field_id==0?next!=0:(next!=0&&next<card.next_field_id))ok=parameter_fail("I38 ID: nextFieldId cannot move backwards");else card.next_field_id=next;}
    size_t slot=0;while(slot<w->parameters.card_count&&w->parameters.cards[slot].id!=id)++slot;
    size_t existing=0;for(size_t i=0;i<w->parameters.field_count;++i)existing+=w->parameters.fields[i].parameter_id==id;
    if(ok&&(slot==PARAM_CARD_MAX||w->parameters.field_count-existing+card.count>PARAM_FIELD_MAX))ok=parameter_fail("UNSUPPORTED/CAPACITY: 64 cards / 256 total fields exceeded");
    if(ok){size_t n=0;for(size_t i=0;i<w->parameters.field_count;++i)if(w->parameters.fields[i].parameter_id!=id)w->parameters.fields[n++]=w->parameters.fields[i];for(size_t k=0;k<card.count;++k)w->parameters.fields[n++]=fresh[k];memset(w->parameters.fields+n,0,(PARAM_FIELD_MAX-n)*sizeof(ParameterField));w->parameters.field_count=n;w->parameters.cards[slot]=card;if(slot==w->parameters.card_count)++w->parameters.card_count;}
    free(fresh);return ok;
}
/* I38: enumerate actual references in a complete candidate. Only the first
 * PARAMETER_USES_SHOWN referrers are named; the count is exact. References from the card's own fields vanish with it. */
#define PARAMETER_USES_SHOWN 3
typedef struct {char text[256];size_t count;} ParameterUses;
static void parameter_use(ParameterUses *u,const char *format,...)
{
    if(u->count++<PARAMETER_USES_SHOWN){
        size_t n=strlen(u->text);if(n&&n+2<sizeof u->text){u->text[n++]=';';u->text[n++]=' ';u->text[n]=0;}
        va_list a;va_start(a,format);if(n<sizeof u->text)vsnprintf(u->text+n,sizeof u->text-n,format,a);va_end(a);
    }
}
static bool parameter_ast_uses(const EngJson *j,int t,uint32_t id,int depth)
{
    if(depth>32)return false;
    char op[16];if(!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op))return false;
    if(!strcmp(op,"ref")){int64_t card=-1;return eng_json_integer(j,eng_json_member(j,t,"parameterId"),&card)&&card==(int64_t)id;}
    int left=eng_json_member(j,t,"left"),right=eng_json_member(j,t,"right");
    return (left>=0&&parameter_ast_uses(j,left,id,depth+1))||(right>=0&&parameter_ast_uses(j,right,id,depth+1));
}
/* Position expressions (guides, datums) carry `param:<card>:<field>` tokens. */
static bool parameter_text_uses(const char *text,uint32_t id)
{
    for(const char *p=text;(p=strstr(p,"param:"))!=NULL;p+=6){
        const char *q=p+6;uint64_t card=0;int digits=0;
        while(*q>='0'&&*q<='9'&&digits<11){card=card*10+(uint64_t)(*q++-'0');++digits;}
        if(digits&&digits<11&&*q==':'&&card==id)return true;
    }
    return false;
}
static size_t parameter_uses(const World *w,uint32_t id,ParameterUses *u)
{
    static const char *const axis_fields[6]={"phase","step","panel","gap","anchor","stagger"};
    memset(u,0,sizeof *u);
    for(size_t i=0;i<w->parameters.field_count;++i){const ParameterField *f=&w->parameters.fields[i];
        if(f->parameter_id==id)continue;
        EngJson j;bool hit=eng_json_parse_n(&j,f->expression,strlen(f->expression))&&parameter_ast_uses(&j,0,id,0);eng_json_free(&j);
        if(hit)parameter_use(u,"parameter %u field %u",f->parameter_id,f->id);
    }
    for(size_t i=0;i<w->engineering.binding_count;++i){const EngBinding *b=&w->engineering.bindings[i];
        for(int override=0;override<2;++override){const EngDimensionSource *s=override?&b->override_value:&b->source;
            if((override&&!b->has_override)||s->kind!=ENG_PARAMETER||s->parameter.parameter_id!=id)continue;
            if(b->target.kind)parameter_use(u,"timber %u %c%s",b->target.id,b->target.field?'B':'A',override?" override":"");
            else parameter_use(u,"grid %u %c %s%s",b->target.id,b->target.axis?'v':'u',b->target.field?"gap":"panel",override?" override":"");
        }
    }
    for(size_t i=0;i<w->assembly.binding_count;++i){const AsmBinding *b=&w->assembly.bindings[i];EngJson j;
        if(eng_json_parse(&j,b->content)){int slots=eng_json_member(&j,0,"slots");
            for(int k=0;k<eng_json_size(&j,slots);++k){int slot=eng_json_at(&j,slots,k);int64_t slot_id=0;
                (void)eng_json_integer(&j,eng_json_member(&j,slot,"slotId"),&slot_id);
                for(int axis=0;axis<2;++axis){int source=eng_json_member(&j,slot,axis?"B":"A");char kind[16];int64_t card=-1;
                    if(eng_json_string(&j,eng_json_member(&j,source,"kind"),kind,sizeof kind)&&!strcmp(kind,"parameter")&&
                       eng_json_integer(&j,eng_json_member(&j,source,"parameterId"),&card)&&card==(int64_t)id)
                        parameter_use(u,"binding %u slot %lld.%c",b->id,(long long)slot_id,axis?'B':'A');
                }
            }
        }
        eng_json_free(&j);
    }
    for(size_t i=0;i<w->guide_count;++i)if(parameter_text_uses(w->guides[i].expression,id))parameter_use(u,"guide %u",w->guides[i].id);
    for(size_t i=0;i<w->datum_count;++i)if(parameter_text_uses(w->datums[i].expression,id))parameter_use(u,"datum %u",w->datums[i].id);
    for(size_t i=0;i<w->grid_system_count;++i)for(int axis=0;axis<2;++axis)for(int k=0;k<6;++k){const ParameterRef *r=&w->grid_systems[i].axis[axis].parameters[k];
        if(r->set&&r->parameter_id==id)parameter_use(u,"grid-system %u %c %s",w->grid_systems[i].id,axis?'v':'u',axis_fields[k]);}
    for(size_t i=0;i<w->grid_count;++i){const ReferenceGrid *g=&w->grids[i];if(g->from_system)continue;  /* system-derived copies are the system's own refs */
        for(int axis=0;axis<2;++axis)for(int k=0;k<6;++k){const ParameterRef *r=&g->axis[axis].parameters[k];
            if(r->set&&r->parameter_id==id)parameter_use(u,"grid %u %c %s",g->id,axis?'v':'u',axis_fields[k]);}}
    for(size_t i=0;i<w->section_profiles.member_count;++i){const ProfileMember *m=&w->section_profiles.members[i];
        if(m->a_source.kind==ENG_PARAMETER&&m->a_source.parameter.parameter_id==id)parameter_use(u,"section-profile member %u A",m->id);
        if(m->b_source.kind==ENG_PARAMETER&&m->b_source.parameter.parameter_id==id)parameter_use(u,"section-profile member %u B",m->id);
    }
    for(size_t i=0;i<w->section_profiles.run_count;++i){const ProfileRun *r=&w->section_profiles.runs[i];
        if(r->length_source.kind==ENG_PARAMETER&&r->length_source.parameter.parameter_id==id)parameter_use(u,"section-profile run %u length",r->id);
    }
    return u->count;
}
/* I38/R33: inspect retired identities only after the complete candidate is defined. */
static bool parameter_retirements_valid(const World *w)
{
    for(size_t i=0;i<w->parameters.retired_count;++i){
        uint32_t id=w->parameters.retired[i];ParameterUses uses;
        if(parameter_uses(w,id,&uses)){
            char more[40]="";if(uses.count>PARAMETER_USES_SHOWN)snprintf(more,sizeof more," and %zu more",uses.count-PARAMETER_USES_SHOWN);
            return parameter_fail("I38 MISSING: parameter %u is still referenced by %s%s; unbind or repoint %s in the same complete candidate",id,uses.text,more,uses.count==1?"it":"them");
        }
    }
    return true;
}
static bool parameter_remove(World *w,uint32_t id)
{
    size_t k=0;while(k<w->parameters.card_count&&w->parameters.cards[k].id!=id)++k;
    if(k==w->parameters.card_count)return parameter_fail("I38 MISSING: parameter %u",id);
    if(w->parameters.retired_count>=PARAM_RETIRED_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: too many parameter identities deleted in one transaction");
    memmove(w->parameters.cards+k,w->parameters.cards+k+1,(w->parameters.card_count-k-1)*sizeof(ParameterSet));memset(&w->parameters.cards[--w->parameters.card_count],0,sizeof(ParameterSet));
    size_t n=0;for(size_t i=0;i<w->parameters.field_count;++i)if(w->parameters.fields[i].parameter_id!=id)w->parameters.fields[n++]=w->parameters.fields[i];memset(w->parameters.fields+n,0,(PARAM_FIELD_MAX-n)*sizeof(ParameterField));w->parameters.field_count=n;
    n=0;for(size_t i=0;i<w->canvas_pos_count;++i)if(w->canvas_pos[i].kind!=CANVAS_POS_PARAMETER||w->canvas_pos[i].id!=id)w->canvas_pos[n++]=w->canvas_pos[i];memset(w->canvas_pos+n,0,(w->canvas_pos_count-n)*sizeof(CanvasPos));w->canvas_pos_count=n;
    w->parameters.retired[w->parameters.retired_count++]=id;
    return true;
}
/* Package imports allocate a complete independent identity map before copying.
 * References must remain inside the package; no accidental links to this world. */
static bool parameter_remap_ast(EngJson *j,int t,ParameterWriter *out,const uint32_t *old,const uint32_t *fresh,int count,int depth)
{
    if(depth>32)return parameter_fail("UNSUPPORTED/CAPACITY: imported expression nesting");
    char op[16];if(!eng_json_string(j,eng_json_member(j,t,"op"),op,sizeof op))return parameter_fail("I38 AST: imported operation missing");
    if(!strcmp(op,"literal")){
        char literal[PARAM_EXPR_MAX];if(!eng_json_canonical(j,t,literal,sizeof literal))return parameter_fail("I38 AST: imported literal invalid");parameter_write(out,"%s",literal);return out->ok;
    }
    if(!strcmp(op,"ref")){
        uint32_t id,field;if(!eng_json_keys(j,t,"op,parameterId,fieldId","")||!parameter_u32(j,eng_json_member(j,t,"parameterId"),&id)||!parameter_u32(j,eng_json_member(j,t,"fieldId"),&field))return parameter_fail("I38 AST: imported reference invalid");
        int k=0;while(k<count&&old[k]!=id)++k;if(k==count)return parameter_fail("I39 PACKAGE: missing dependency card %u",id);
        parameter_write(out,"{\"op\":\"ref\",\"parameterId\":%u,\"fieldId\":%u}",fresh[k],field);return out->ok;
    }
    bool neg=!strcmp(op,"neg");if((!neg&&strcmp(op,"add")&&strcmp(op,"sub")&&strcmp(op,"mul")&&strcmp(op,"div"))||!eng_json_keys(j,t,neg?"op,left":"op,left,right",""))return parameter_fail("I38 AST: invalid imported operation");
    parameter_write(out,"{\"op\":\"%s\",\"left\":",op);
    if(!parameter_remap_ast(j,eng_json_member(j,t,"left"),out,old,fresh,count,depth+1))return false;
    if(!neg){parameter_write(out,",\"right\":");if(!parameter_remap_ast(j,eng_json_member(j,t,"right"),out,old,fresh,count,depth+1))return false;}
    parameter_write(out,"}");return out->ok;
}
static bool parameter_import(World *w,EngJson *j,int t)
{
    char schema[40];int cards=eng_json_member(j,t,"cards");
    if(!eng_json_keys(j,t,"schema,cards","")||!eng_json_string(j,eng_json_member(j,t,"schema"),schema,sizeof schema)||strcmp(schema,"geometry-parameters/1")||!eng_json_is_array(j,cards))return parameter_fail("I39 PACKAGE: expected geometry-parameters/1 cards");
    int n=eng_json_size(j,cards);if(n<1||n>PARAM_CARD_MAX||(size_t)n+w->parameters.card_count>PARAM_CARD_MAX)return parameter_fail("UNSUPPORTED/CAPACITY: imported card capacity");
    uint32_t old[PARAM_CARD_MAX],fresh[PARAM_CARD_MAX];uint32_t candidate=0;
    for(int k=0;k<n;++k){
        int c=eng_json_at(j,cards,k);if(!parameter_u32(j,eng_json_member(j,c,"id"),&old[k]))return false;
        for(int q=0;q<k;++q)if(old[q]==old[k])return parameter_fail("I39 PACKAGE: duplicate card identity");
        while(parameter_find(w,candidate)||parameter_retired(w,candidate))++candidate;fresh[k]=candidate++;
    }
    char *buffer=malloc(PARAM_FIELDS_PER_CARD*(PARAM_EXPR_MAX+1000));if(!buffer)return parameter_fail("UNSUPPORTED/CAPACITY: package memory");bool ok=true;
    for(int k=0;k<n&&ok;++k){
        int c=eng_json_at(j,cards,k),fields=eng_json_member(j,c,"fields");char name[PARAM_NAME_MAX],quoted[600];
        if(!eng_json_keys(j,c,"id,name,fields","nextFieldId")||!parameter_name(j,eng_json_member(j,c,"name"),name)||!eng_json_is_array(j,fields)||eng_json_size(j,fields)<1||eng_json_size(j,fields)>PARAM_FIELDS_PER_CARD){ok=parameter_fail("I39 PACKAGE: invalid card");break;}
        eng_json_quote(name,quoted,sizeof quoted);ParameterWriter b={buffer,PARAM_FIELDS_PER_CARD*(PARAM_EXPR_MAX+1000),0,true};parameter_write(&b,"{\"id\":%u,\"name\":%s",fresh[k],quoted);
        int nt=eng_json_member(j,c,"nextFieldId");uint32_t next;if(nt>=0){if(!parameter_u32(j,nt,&next)){ok=false;break;}parameter_write(&b,",\"nextFieldId\":%u",next);}parameter_write(&b,",\"fields\":[");
        for(int f=0;f<eng_json_size(j,fields)&&ok;++f){int ft=eng_json_at(j,fields,f);uint32_t id;char type[20];
            if(!eng_json_keys(j,ft,"id,name,type,expression","")||!parameter_u32(j,eng_json_member(j,ft,"id"),&id)||!parameter_name(j,eng_json_member(j,ft,"name"),name)||!eng_json_string(j,eng_json_member(j,ft,"type"),type,sizeof type)||(strcmp(type,"dimension")&&strcmp(type,"count")&&strcmp(type,"ratio"))){ok=parameter_fail("I39 PACKAGE: invalid field");break;}
            eng_json_quote(name,quoted,sizeof quoted);parameter_write(&b,"%s{\"id\":%u,\"name\":%s,\"type\":\"%s\",\"expression\":",f?",":"",id,quoted,type);
            ok=parameter_remap_ast(j,eng_json_member(j,ft,"expression"),&b,old,fresh,n,0);parameter_write(&b,"}");
        }
        parameter_write(&b,"]}");if(!b.ok){ok=parameter_fail("UNSUPPORTED/CAPACITY: package expression record");break;}
        if(ok){EngJson copy;ok=eng_json_parse_n(&copy,buffer,b.used);if(ok)ok=parameter_put(w,&copy,0);eng_json_free(&copy);}
    }
    free(buffer);return ok;
}
static void parameter_json_card(const World *w,const ParameterSet *c,FILE *out,bool values)
{
    char q[600];eng_json_quote(c->name,q,sizeof q);fprintf(out,"{\"id\":%u,\"name\":%s,\"nextFieldId\":%u,\"fields\":[",c->id,q,c->next_field_id);
    for(size_t k=0;k<c->count;++k){int index=parameter_field_index(w,c->id,c->fields[k]);const ParameterField *f=&w->parameters.fields[index];eng_json_quote(f->name,q,sizeof q);
        fprintf(out,"%s{\"id\":%u,\"name\":%s,\"type\":\"%s\",\"expression\":%s",k?",":"",f->id,q,f->type==0?"dimension":f->type==1?"count":"ratio",f->expression);
        if(values)fprintf(out,",\"value\":{\"num\":\"%lld\",\"den\":\"%lld\",\"unit\":\"%s\"}",(long long)f->value.num,(long long)f->value.den,f->value.unit?"mm":"1");fputc('}',out);
    }fputs("]}",out);
}
static void parameters_dump(const World *w,FILE *out)
{
    if(!w->parameters.card_count)return;fputs("requires parameters/1\nparameters begin\n",out);
    /* One field per bounded scene record; the block is a single declaration. */
    for(size_t i=0;i<w->parameters.card_count;++i){const ParameterSet *c=&w->parameters.cards[i];char q[600];eng_json_quote(c->name,q,sizeof q);char record[900],encoded[1300];size_t n;
        snprintf(record,sizeof record,"{\"id\":%u,\"name\":%s,\"nextFieldId\":%u}",c->id,q,c->next_field_id);eng_base64_encode(record,strlen(record),encoded,sizeof encoded,&n);fprintf(out,"parameters card %s\n",encoded);
        for(size_t k=0;k<c->count;++k){const ParameterField *f=&w->parameters.fields[parameter_field_index(w,c->id,c->fields[k])];char field[3000],b64[4100];eng_json_quote(f->name,q,sizeof q);
            snprintf(field,sizeof field,"{\"parameterId\":%u,\"id\":%u,\"name\":%s,\"type\":%d,\"expression\":%s}",c->id,f->id,q,f->type,f->expression);eng_base64_encode(field,strlen(field),b64,sizeof b64,&n);fprintf(out,"parameters field %s\n",b64);
        }
    }fputs("parameters end\n",out);
}
static bool apply_parameters_line(const char *path,int line_no,char **t,int count,World *w)
{
    bool ok=false;if(!g_parameter_scene_loading){scene_error(path,line_no,"I39: parameter blocks require atomic full-scene loading; use parameter transactions for editing");return false;}
    if(count==2&&!strcmp(t[1],"begin")){if(w->parameters.loading)goto fail;w->parameters.loading=true;return true;}
    if(!w->parameters.loading)goto fail;
    if(count==2&&!strcmp(t[1],"end")){w->parameters.loading=false;for(size_t i=0;i<w->parameters.card_count;++i)if(!w->parameters.cards[i].count)goto fail;char e[512];if(!parameters_rebuild(w,e,sizeof e)){scene_error(path,line_no,e);return false;}return true;}
    if(count!=3)goto fail;unsigned char decoded[4000];size_t n=0;if(!eng_base64_decode(t[2],strlen(t[2]),decoded,sizeof decoded-1,&n))goto fail;decoded[n]=0;
    EngJson j;if(!eng_json_parse_n(&j,(char*)decoded,n)){eng_json_free(&j);goto fail;}
    if(!strcmp(t[1],"card")){
        ParameterSet c={0};if(eng_json_keys(&j,0,"id,name,nextFieldId","")&&parameter_u32(&j,eng_json_member(&j,0,"id"),&c.id)&&parameter_u32(&j,eng_json_member(&j,0,"nextFieldId"),&c.next_field_id)&&parameter_name(&j,eng_json_member(&j,0,"name"),c.name)&&!parameter_find(w,c.id)&&w->parameters.card_count<PARAM_CARD_MAX){w->parameters.cards[w->parameters.card_count++]=c;ok=true;}
    }else if(!strcmp(t[1],"field")){
        ParameterField f={0};int64_t type;
        if(eng_json_keys(&j,0,"parameterId,id,name,type,expression","")&&parameter_u32(&j,eng_json_member(&j,0,"parameterId"),&f.parameter_id)&&parameter_u32(&j,eng_json_member(&j,0,"id"),&f.id)&&parameter_name(&j,eng_json_member(&j,0,"name"),f.name)&&eng_json_integer(&j,eng_json_member(&j,0,"type"),&type)&&type>=0&&type<=2&&eng_json_canonical(&j,eng_json_member(&j,0,"expression"),f.expression,sizeof f.expression)){
            ParameterSet *c=(ParameterSet*)parameter_find(w,f.parameter_id);bool unique=true;
            for(size_t k=0;k<w->parameters.field_count;++k)if(w->parameters.fields[k].parameter_id==f.parameter_id&&(w->parameters.fields[k].id==f.id||!strcmp(w->parameters.fields[k].name,f.name)))unique=false;
            if(c&&unique&&c->count<PARAM_FIELDS_PER_CARD&&w->parameters.field_count<PARAM_FIELD_MAX&&(!c->next_field_id||f.id<c->next_field_id)){f.type=(int)type;c->fields[c->count++]=f.id;w->parameters.fields[w->parameters.field_count++]=f;ok=true;}
        }
    }
    eng_json_free(&j);if(ok)return true;
fail:scene_error(path,line_no,g_parameter_error[0]?g_parameter_error:"I39: invalid parameter block record");return false;
}
