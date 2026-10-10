/* engineering-content/1: strict JSON, canonical UTF-8 and fingerprint helpers.
 * Self-contained C; no locale-dependent numbers or external crypto runtime.
 */
#ifndef ENGINEERING_JSON_INCLUDED
#define ENGINEERING_JSON_INCLUDED
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>

#define ENG_JSON_MAX_INPUT (1024u * 1024u)
#define ENG_JSON_MAX_DEPTH 128

enum { ENG_J_OBJECT=1, ENG_J_ARRAY, ENG_J_STRING, ENG_J_INTEGER, ENG_J_BOOL, ENG_J_NULL };
typedef struct {
    int type, size, next;
    char *string;
    int64_t number;
} EngJsonToken;
typedef struct {
    const char *text;
    EngJsonToken *tokens;
    int count;
    char error[192];
} EngJson;
typedef struct { EngJson *j; size_t pos, length; int capacity; } EngJsonParser;
typedef struct { char *out; size_t used, capacity; int ok; } EngJsonWriter;
typedef struct { const char *key; int token; } EngJsonKey;
static int eng_json_compare_key(const void *a,const void *b) {
    return strcmp(((const EngJsonKey*)a)->key,((const EngJsonKey*)b)->key);
}
static EngJsonKey *eng_json_sorted_keys(const EngJson *j,int token) {
    int p,i=0,count=j->tokens[token].size;
    EngJsonKey *order=count?(EngJsonKey*)malloc((size_t)count*sizeof(*order)):NULL;
    if(count&&!order)return NULL;
    for(p=token+1;p<j->tokens[token].next;p=j->tokens[p+1].next) {
        order[i].key=j->tokens[p].string;order[i].token=p;i++;
    }
    if(count>1)qsort(order,(size_t)count,sizeof(*order),eng_json_compare_key);
    return order;
}

static int eng_json_error(EngJson *j, const char *message) {
    if (!j->error[0]) snprintf(j->error, sizeof(j->error), "%s", message);
    return 0;
}
static void eng_json_free(EngJson *j) {
    int i;
    if (!j) return;
    for (i=0;i<j->count;i++) free(j->tokens[i].string);
    free(j->tokens);
    memset(j,0,sizeof(*j));
}
/* Return the byte length of one valid scalar; reject overlong sequences,
 * surrogate code points, U+0000 and code points outside Unicode. */
static size_t eng_utf8_scalar(const unsigned char *s, size_t n) {
    unsigned c;
    if (!n || !s[0]) return 0;
    if (s[0]<0x80) return 1;
    if (s[0]>=0xc2 && s[0]<=0xdf) {
        if (n<2 || (s[1]&0xc0)!=0x80) return 0;
        return 2;
    }
    if (s[0]>=0xe0 && s[0]<=0xef) {
        if (n<3 || (s[1]&0xc0)!=0x80 || (s[2]&0xc0)!=0x80) return 0;
        c=((s[0]&15u)<<12)|((s[1]&63u)<<6)|(s[2]&63u);
        return c>=0x800 && !(c>=0xd800 && c<=0xdfff) ? 3:0;
    }
    if (s[0]>=0xf0 && s[0]<=0xf4) {
        if (n<4 || (s[1]&0xc0)!=0x80 || (s[2]&0xc0)!=0x80 || (s[3]&0xc0)!=0x80) return 0;
        c=((s[0]&7u)<<18)|((s[1]&63u)<<12)|((s[2]&63u)<<6)|(s[3]&63u);
        return c>=0x10000 && c<=0x10ffff ? 4:0;
    }
    return 0;
}
static void eng_json_space(EngJsonParser *p) {
    while (p->pos<p->length) {
        char c=p->j->text[p->pos];
        if (c!=' ' && c!='\t' && c!='\r' && c!='\n') break;
        p->pos++;
    }
}
static int eng_json_token(EngJsonParser *p, int type) {
    EngJsonToken *tokens;
    int n=p->j->count;
    if (n==p->capacity) {
        int cap=p->capacity ? p->capacity*2:32;
        tokens=(EngJsonToken*)realloc(p->j->tokens,(size_t)cap*sizeof(*tokens));
        if (!tokens) { eng_json_error(p->j,"JSON memory capacity exceeded"); return -1; }
        p->j->tokens=tokens;
        p->capacity=cap;
    }
    memset(&p->j->tokens[n],0,sizeof(p->j->tokens[n]));
    p->j->tokens[n].type=type;
    p->j->tokens[n].next=n+1;
    p->j->count++;
    return n;
}
static int eng_json_hex4(EngJsonParser *p, unsigned *value) {
    int i; unsigned v=0;
    if (p->length-p->pos<4) return eng_json_error(p->j,"Incomplete Unicode escape");
    for(i=0;i<4;i++) {
        unsigned char c=(unsigned char)p->j->text[p->pos++];
        unsigned digit;
        if (c>='0' && c<='9') digit=c-'0';
        else if(c>='a' && c<='f') digit=c-'a'+10;
        else if(c>='A' && c<='F') digit=c-'A'+10;
        else return eng_json_error(p->j,"Invalid Unicode escape");
        v=(v<<4)|digit;
    }
    *value=v; return 1;
}
static int eng_json_parse_string(EngJsonParser *p) {
    size_t used=0, max, end;
    char *out; int token;
    if (p->pos>=p->length || p->j->text[p->pos]!='"') return -1;
    p->pos++;
    /* A decoded string cannot be longer than its encoded source. */
    end=p->pos;
    while(end<p->length && p->j->text[end]!='"') {
        if(p->j->text[end]=='\\' && end+1<p->length)end++;
        end++;
    }
    max=end-p->pos+1;
    out=(char*)malloc(max);
    if (!out) { eng_json_error(p->j,"JSON memory capacity exceeded"); return -1; }
    while(p->pos<p->length) {
        unsigned char c=(unsigned char)p->j->text[p->pos++];
        if(c=='"') {
            out[used]=0;
            token=eng_json_token(p,ENG_J_STRING);
            if(token<0) {free(out); return -1;}
            p->j->tokens[token].string=out;
            return token;
        }
        if(c<0x20) {eng_json_error(p->j,"Unescaped control character in JSON string"); break;}
        if(c=='\\') {
            unsigned u;
            if(p->pos>=p->length) {eng_json_error(p->j,"Incomplete JSON escape");break;}
            c=(unsigned char)p->j->text[p->pos++];
            if(c=='"'||c=='\\'||c=='/') out[used++]=(char)c;
            else if(c=='b') out[used++]='\b';
            else if(c=='f') out[used++]='\f';
            else if(c=='n') out[used++]='\n';
            else if(c=='r') out[used++]='\r';
            else if(c=='t') out[used++]='\t';
            else if(c=='u') {
                if(!eng_json_hex4(p,&u)) break;
                if(u>=0xd800 && u<=0xdbff) {
                    unsigned lo;
                    if(p->length-p->pos<6 || p->j->text[p->pos]!='\\' || p->j->text[p->pos+1]!='u') {
                        eng_json_error(p->j,"High surrogate requires low surrogate");break;
                    }
                    p->pos+=2;
                    if(!eng_json_hex4(p,&lo)) break;
                    if(lo<0xdc00 || lo>0xdfff) {eng_json_error(p->j,"Invalid low surrogate");break;}
                    u=0x10000+((u-0xd800)<<10)+(lo-0xdc00);
                } else if(u>=0xdc00 && u<=0xdfff) {eng_json_error(p->j,"Unpaired low surrogate");break;}
                if(!u) {eng_json_error(p->j,"NUL is not allowed in engineering JSON");break;}
                if(u<0x80) out[used++]=(char)u;
                else if(u<0x800) {out[used++]=(char)(0xc0|(u>>6));out[used++]=(char)(0x80|(u&63));}
                else if(u<0x10000) {out[used++]=(char)(0xe0|(u>>12));out[used++]=(char)(0x80|((u>>6)&63));out[used++]=(char)(0x80|(u&63));}
                else {out[used++]=(char)(0xf0|(u>>18));out[used++]=(char)(0x80|((u>>12)&63));out[used++]=(char)(0x80|((u>>6)&63));out[used++]=(char)(0x80|(u&63));}
            } else {eng_json_error(p->j,"Invalid JSON escape");break;}
        } else if(c>=0x80) {
            size_t n=eng_utf8_scalar((const unsigned char*)p->j->text+p->pos-1,p->length-p->pos+1);
            if(!n) {eng_json_error(p->j,"Invalid UTF-8 in JSON string");break;}
            memcpy(out+used,p->j->text+p->pos-1,n);used+=n;p->pos+=n-1;
        } else out[used++]=(char)c;
    }
    free(out);
    if(!p->j->error[0]) eng_json_error(p->j,"Unterminated JSON string");
    return -1;
}
static int eng_json_parse_value(EngJsonParser *p, int depth) {
    int token;
    unsigned char c;
    eng_json_space(p);
    if(depth>ENG_JSON_MAX_DEPTH) {eng_json_error(p->j,"JSON nesting capacity exceeded");return -1;}
    if(p->pos>=p->length) {eng_json_error(p->j,"Missing JSON value");return -1;}
    c=(unsigned char)p->j->text[p->pos];
    if(c=='"') return eng_json_parse_string(p);
    if(c=='{'||c=='[') {
        int object=c=='{', count=0;
        char close=object?'}':']';
        token=eng_json_token(p,object?ENG_J_OBJECT:ENG_J_ARRAY);
        if(token<0)return -1;
        p->pos++;eng_json_space(p);
        if(p->pos<p->length && p->j->text[p->pos]==close) {p->pos++;return token;}
        for(;;) {
            if(object) {
                int key;
                if(p->pos>=p->length || p->j->text[p->pos]!='"') {eng_json_error(p->j,"Object key must be a string");return -1;}
                key=eng_json_parse_string(p);
                if(key<0)return -1;
                eng_json_space(p);
                if(p->pos>=p->length || p->j->text[p->pos++]!=':') {eng_json_error(p->j,"Missing colon after JSON key");return -1;}
            }
            if(eng_json_parse_value(p,depth+1)<0)return -1;
            count++;eng_json_space(p);
            if(p->pos>=p->length) {eng_json_error(p->j,"Unterminated JSON container");return -1;}
            c=(unsigned char)p->j->text[p->pos++];
            if(c==(unsigned char)close)break;
            if(c!=',') {eng_json_error(p->j,"Missing comma in JSON container");return -1;}
            eng_json_space(p);
        }
        p->j->tokens[token].size=count;
        p->j->tokens[token].next=p->j->count;
        if(object && count>1) {
            int i;
            EngJsonKey *order=eng_json_sorted_keys(p->j,token);
            if(!order){eng_json_error(p->j,"JSON memory capacity exceeded");return -1;}
            for(i=1;i<count;i++)if(strcmp(order[i-1].key,order[i].key)==0) {
                free(order);eng_json_error(p->j,"Duplicate JSON object key");return -1;
            }
            free(order);
        }
        return token;
    }
    if(c=='-'||(c>='0'&&c<='9')) {
        int negative=c=='-';
        uint64_t n=0, limit=negative ? UINT64_C(9223372036854775808):UINT64_C(9223372036854775807);
        if(negative)p->pos++;
        if(p->pos>=p->length || p->j->text[p->pos]<'0'||p->j->text[p->pos]>'9') {eng_json_error(p->j,"Invalid JSON integer");return -1;}
        if(p->j->text[p->pos]=='0' && p->pos+1<p->length && p->j->text[p->pos+1]>='0'&&p->j->text[p->pos+1]<='9') {
            eng_json_error(p->j,"Leading zero in JSON integer");return -1;
        }
        while(p->pos<p->length && p->j->text[p->pos]>='0'&&p->j->text[p->pos]<='9') {
            unsigned digit=(unsigned)(p->j->text[p->pos++]-'0');
            if(n>(limit-digit)/10) {eng_json_error(p->j,"JSON integer exceeds int64 range");return -1;}
            n=n*10+digit;
        }
        if(p->pos<p->length && (p->j->text[p->pos]=='.'||p->j->text[p->pos]=='e'||p->j->text[p->pos]=='E')) {
            eng_json_error(p->j,"Floating-point JSON numbers are not supported");return -1;
        }
        token=eng_json_token(p,ENG_J_INTEGER);
        if(token>=0)p->j->tokens[token].number=negative ? (n==UINT64_C(9223372036854775808)?INT64_MIN:-(int64_t)n):(int64_t)n;
        return token;
    }
    if(p->length-p->pos>=4 && memcmp(p->j->text+p->pos,"null",4)==0) {p->pos+=4;return eng_json_token(p,ENG_J_NULL);}
    if(p->length-p->pos>=4 && memcmp(p->j->text+p->pos,"true",4)==0) {
        p->pos+=4;token=eng_json_token(p,ENG_J_BOOL);if(token>=0)p->j->tokens[token].number=1;return token;
    }
    if(p->length-p->pos>=5 && memcmp(p->j->text+p->pos,"false",5)==0) {p->pos+=5;return eng_json_token(p,ENG_J_BOOL);}
    eng_json_error(p->j,"Invalid JSON value");return -1;
}
static int eng_json_parse_n(EngJson *j, const char *text, size_t length) {
    EngJsonParser p;
    memset(j,0,sizeof(*j));
    j->text=text;
    if(!text || length>ENG_JSON_MAX_INPUT)return eng_json_error(j,"JSON input capacity exceeded");
    if(memchr(text,0,length))return eng_json_error(j,"NUL is not allowed in engineering JSON");
    memset(&p,0,sizeof(p));p.j=j;p.length=length;
    if(eng_json_parse_value(&p,0)<0)return 0;
    eng_json_space(&p);
    if(p.pos!=length)return eng_json_error(j,"Trailing data after JSON value");
    return 1;
}
static int eng_json_parse(EngJson *j, const char *text) {
    return eng_json_parse_n(j,text,text?strlen(text):0);
}
static int eng_json_valid_token(const EngJson *j,int token) {return j && token>=0 && token<j->count;}
static int eng_json_is_object(const EngJson *j,int token) {return eng_json_valid_token(j,token)&&j->tokens[token].type==ENG_J_OBJECT;}
static int eng_json_is_array(const EngJson *j,int token) {return eng_json_valid_token(j,token)&&j->tokens[token].type==ENG_J_ARRAY;}
static int eng_json_is_null(const EngJson *j,int token) {return eng_json_valid_token(j,token)&&j->tokens[token].type==ENG_J_NULL;}
static int eng_json_size(const EngJson *j,int token) {
    return (eng_json_is_object(j,token)||eng_json_is_array(j,token))?j->tokens[token].size:-1;
}
static int eng_json_member(const EngJson *j,int token,const char *key) {
    int p;
    if(!eng_json_is_object(j,token)||!key)return -1;
    for(p=token+1;p<j->tokens[token].next;p=j->tokens[p+1].next)
        if(strcmp(j->tokens[p].string,key)==0)return p+1;
    return -1;
}
static int eng_json_at(const EngJson *j,int token,int index) {
    int p;
    if(!eng_json_is_array(j,token)||index<0||index>=j->tokens[token].size)return -1;
    p=token+1;
    while(index--)p=j->tokens[p].next;
    return p;
}
static int eng_json_string(const EngJson *j,int token,char *out,size_t capacity) {
    size_t n;
    if(!eng_json_valid_token(j,token)||j->tokens[token].type!=ENG_J_STRING||!out)return 0;
    n=strlen(j->tokens[token].string);
    if(n>=capacity)return 0;
    memcpy(out,j->tokens[token].string,n+1);return 1;
}
static int eng_json_integer(const EngJson *j,int token,int64_t *out) {
    if(!out||!eng_json_valid_token(j,token)||j->tokens[token].type!=ENG_J_INTEGER)return 0;
    *out=j->tokens[token].number;return 1;
}
static int eng_json_boolean(const EngJson *j,int token,int *out) {
    if(!out||!eng_json_valid_token(j,token)||j->tokens[token].type!=ENG_J_BOOL)return 0;
    *out=(int)j->tokens[token].number;return 1;
}
static int eng_json_csv_has(const char *csv,const char *key) {
    size_t length=strlen(key);
    if(!csv)return 0;
    while(*csv) {
        const char *end=strchr(csv,',');
        size_t n=end?(size_t)(end-csv):strlen(csv);
        if(n==length && memcmp(csv,key,n)==0)return 1;
        if(!end)break;
        csv=end+1;
    }
    return 0;
}
static int eng_json_keys(EngJson *j,int token,const char *required,const char *optional) {
    int p;
    const char *r=required;
    if(!eng_json_is_object(j,token))return eng_json_error(j,"Expected JSON object");
    for(p=token+1;p<j->tokens[token].next;p=j->tokens[p+1].next)
        if(!eng_json_csv_has(required,j->tokens[p].string)&&!eng_json_csv_has(optional,j->tokens[p].string))
            return eng_json_error(j,"Unknown JSON object key");
    while(r&&*r) {
        const char *end=strchr(r,',');
        size_t n=end?(size_t)(end-r):strlen(r);
        int found=0;
        for(p=token+1;p<j->tokens[token].next;p=j->tokens[p+1].next)
            if(strlen(j->tokens[p].string)==n && memcmp(j->tokens[p].string,r,n)==0){found=1;break;}
        if(!found)return eng_json_error(j,"Missing required JSON object key");
        if(!end)break;
        r=end+1;
    }
    return 1;
}
static void eng_json_write(EngJsonWriter *w,const char *text,size_t n) {
    if(!w->ok)return;
    if(n>=w->capacity-w->used) {w->ok=0;return;}
    memcpy(w->out+w->used,text,n);w->used+=n;w->out[w->used]=0;
}
static void eng_json_write_string(EngJsonWriter *w,const char *s) {
    size_t p=0,n=strlen(s);
    static const char hex[]="0123456789abcdef";
    eng_json_write(w,"\"",1);
    while(p<n && w->ok) {
        unsigned char c=(unsigned char)s[p];
        const char *escape=NULL;
        if(c=='"')escape="\\\"";
        else if(c=='\\')escape="\\\\";
        else if(c=='\b')escape="\\b";
        else if(c=='\f')escape="\\f";
        else if(c=='\n')escape="\\n";
        else if(c=='\r')escape="\\r";
        else if(c=='\t')escape="\\t";
        if(escape){eng_json_write(w,escape,2);p++;}
        else if(c<0x20) {
            char buf[6]={'\\','u','0','0',hex[c>>4],hex[c&15]};eng_json_write(w,buf,6);p++;
        } else {
            size_t k=eng_utf8_scalar((const unsigned char*)s+p,n-p);
            if(!k){w->ok=0;break;}
            eng_json_write(w,s+p,k);p+=k;
        }
    }
    eng_json_write(w,"\"",1);
}
static int eng_json_quote(const char *text,char *out,size_t capacity) {
    EngJsonWriter w;
    if(!text||!out||!capacity)return 0;
    w.out=out;w.capacity=capacity;w.used=0;w.ok=1;out[0]=0;
    eng_json_write_string(&w,text);
    if(!w.ok)out[0]=0;
    return w.ok;
}
static void eng_json_write_value(const EngJson *j,int token,EngJsonWriter *w) {
    const EngJsonToken *t=&j->tokens[token];
    int p,i;
    if(!w->ok)return;
    switch(t->type) {
    case ENG_J_STRING:eng_json_write_string(w,t->string);break;
    case ENG_J_INTEGER:{char buf[32];int n=snprintf(buf,sizeof(buf),"%lld",(long long)t->number);eng_json_write(w,buf,(size_t)n);break;}
    case ENG_J_BOOL:eng_json_write(w,t->number?"true":"false",t->number?4:5);break;
    case ENG_J_NULL:eng_json_write(w,"null",4);break;
    case ENG_J_ARRAY:
        eng_json_write(w,"[",1);
        for(p=token+1,i=0;p<t->next;p=j->tokens[p].next,i++) {
            if(i)eng_json_write(w,",",1);
            eng_json_write_value(j,p,w);
        }
        eng_json_write(w,"]",1);break;
    case ENG_J_OBJECT:{
        EngJsonKey *order=eng_json_sorted_keys(j,token);
        if(t->size&&!order){w->ok=0;return;}
        eng_json_write(w,"{",1);
        for(i=0;i<t->size;i++) {
            if(i)eng_json_write(w,",",1);
            eng_json_write_string(w,order[i].key);eng_json_write(w,":",1);
            eng_json_write_value(j,order[i].token+1,w);
        }
        eng_json_write(w,"}",1);free(order);break;
    }
    default:w->ok=0;
    }
}
static int eng_json_canonical(const EngJson *j,int token,char *out,size_t capacity) {
    EngJsonWriter w;
    if(!eng_json_valid_token(j,token)||j->error[0]||!out||!capacity)return 0;
    w.out=out;w.capacity=capacity;w.used=0;w.ok=1;out[0]=0;
    eng_json_write_value(j,token,&w);
    if(!w.ok)out[0]=0;
    return w.ok;
}

static uint32_t eng_sha_rotr(uint32_t v,unsigned n) {return (v>>n)|(v<<(32-n));}
static void eng_sha_block(uint32_t state[8],const unsigned char block[64]) {
    static const uint32_t k[64]={
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
    uint32_t words[64],a,b,c,d,e,f,g,h;
    int i;
    for(i=0;i<16;i++)words[i]=((uint32_t)block[i*4]<<24)|((uint32_t)block[i*4+1]<<16)|((uint32_t)block[i*4+2]<<8)|block[i*4+3];
    for(i=16;i<64;i++) {
        uint32_t x=words[i-15],y=words[i-2];
        words[i]=words[i-16]+(eng_sha_rotr(x,7)^eng_sha_rotr(x,18)^(x>>3))+words[i-7]+(eng_sha_rotr(y,17)^eng_sha_rotr(y,19)^(y>>10));
    }
    a=state[0];b=state[1];c=state[2];d=state[3];e=state[4];f=state[5];g=state[6];h=state[7];
    for(i=0;i<64;i++) {
        uint32_t t1=h+(eng_sha_rotr(e,6)^eng_sha_rotr(e,11)^eng_sha_rotr(e,25))+((e&f)^((~e)&g))+k[i]+words[i];
        uint32_t t2=(eng_sha_rotr(a,2)^eng_sha_rotr(a,13)^eng_sha_rotr(a,22))+((a&b)^(a&c)^(b&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    state[0]+=a;state[1]+=b;state[2]+=c;state[3]+=d;state[4]+=e;state[5]+=f;state[6]+=g;state[7]+=h;
}
static void eng_sha256(const void *data,size_t length,char out[65]) {
    uint32_t state[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    unsigned char final[128];
    const unsigned char *bytes=(const unsigned char*)data;
    size_t full=length/64,remain=length%64,i,padded=remain<56?64:128;
    uint64_t bits=(uint64_t)length*8;
    static const char hex[]="0123456789abcdef";
    for(i=0;i<full;i++)eng_sha_block(state,bytes+i*64);
    memset(final,0,sizeof(final));
    if(remain)memcpy(final,bytes+full*64,remain);
    final[remain]=0x80;
    for(i=0;i<8;i++)final[padded-1-i]=(unsigned char)(bits>>(i*8));
    eng_sha_block(state,final);if(padded==128)eng_sha_block(state,final+64);
    for(i=0;i<32;i++) {
        unsigned b=(state[i/4]>>(24-(i%4)*8))&255u;
        out[i*2]=hex[b>>4];out[i*2+1]=hex[b&15];
    }
    out[64]=0;
}
static int eng_base64_encode(const void *data,size_t length,char *out,size_t capacity,size_t *out_length) {
    static const char table[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const unsigned char *s=(const unsigned char*)data;
    size_t i,n,p=0;
    if(out_length)*out_length=0;
    if(!out||(!data&&length)||length>(SIZE_MAX-2)/3)return 0;
    n=((length+2)/3)*4;
    if(n>=capacity)return 0;
    for(i=0;i<length;i+=3) {
        unsigned v=((unsigned)s[i]<<16)|(i+1<length?(unsigned)s[i+1]<<8:0)|(i+2<length?s[i+2]:0);
        out[p++]=table[(v>>18)&63];out[p++]=table[(v>>12)&63];
        out[p++]=i+1<length?table[(v>>6)&63]:'=';out[p++]=i+2<length?table[v&63]:'=';
    }
    out[p]=0;if(out_length)*out_length=p;return 1;
}
static int eng_base64_digit(unsigned char c) {
    if(c>='A'&&c<='Z')return c-'A';
    if(c>='a'&&c<='z')return c-'a'+26;
    if(c>='0'&&c<='9')return c-'0'+52;
    if(c=='+')return 62;if(c=='/')return 63;return -1;
}
static int eng_base64_decode(const char *data,size_t length,void *out,size_t capacity,size_t *out_length) {
    unsigned char *dest=(unsigned char*)out;
    size_t i,needed,p=0;
    if(out_length)*out_length=0;
    if(!data||(!out&&length)||length%4)return 0;
    needed=(length/4)*3;
    if(length&&data[length-1]=='=')needed--;
    if(length>1&&data[length-2]=='=')needed--;
    if(needed>capacity)return 0;
    /* Validate the full source before writing any output. */
    for(i=0;i<length;i+=4) {
        int a=eng_base64_digit((unsigned char)data[i]),b=eng_base64_digit((unsigned char)data[i+1]);
        int c=eng_base64_digit((unsigned char)data[i+2]),d=eng_base64_digit((unsigned char)data[i+3]);
        if(a<0||b<0)return 0;
        if(data[i+2]=='=') {if(i+4!=length||data[i+3]!='='||(b&15))return 0;}
        else if(c<0)return 0;
        else if(data[i+3]=='=') {if(i+4!=length||(c&3))return 0;}
        else if(d<0)return 0;
    }
    for(i=0;i<length;i+=4) {
        unsigned a=(unsigned)eng_base64_digit((unsigned char)data[i]),b=(unsigned)eng_base64_digit((unsigned char)data[i+1]);
        unsigned c=data[i+2]=='='?0:(unsigned)eng_base64_digit((unsigned char)data[i+2]);
        unsigned d=data[i+3]=='='?0:(unsigned)eng_base64_digit((unsigned char)data[i+3]);
        unsigned v=(a<<18)|(b<<12)|(c<<6)|d;
        dest[p++]=(unsigned char)(v>>16);
        if(data[i+2]!='=')dest[p++]=(unsigned char)(v>>8);
        if(data[i+3]!='=')dest[p++]=(unsigned char)v;
    }
    if(out_length)*out_length=p;
    return 1;
}
#endif /* ENGINEERING_JSON_INCLUDED */
