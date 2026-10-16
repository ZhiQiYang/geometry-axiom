
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
#include "codec.h"
int main(int argc,char **argv) {
    FILE *f; long rawlen; size_t n,written=0; char *data,*out;
    int ok=0; GeoJson j;
#ifdef _WIN32
    _setmode(_fileno(stdout),_O_BINARY);
#endif
    if(argc!=3)return 70;
    f=fopen(argv[2],"rb");if(!f)return 71;
    fseek(f,0,SEEK_END);rawlen=ftell(f);rewind(f);
    if(rawlen<0){fclose(f);return 72;}
    n=(size_t)rawlen;
    data=(char*)malloc(n+1);out=(char*)malloc(n*6+4096);
    if(!data||!out){fclose(f);return 73;}
    if(fread(data,1,n,f)!=n){fclose(f);return 74;}
    fclose(f);data[n]=0;
    if(!strcmp(argv[1],"hash")){geo_sha256(data,n,out);puts(out);ok=1;}
    else if(!strcmp(argv[1],"encode")){
        ok=geo_base64_encode(data,n,out,n*6+4096,&written);
        if(ok)fwrite(out,1,written,stdout);
    }else if(!strcmp(argv[1],"decode")){
        ok=geo_base64_decode(data,n,out,n*6+4096,&written);
        if(ok)fwrite(out,1,written,stdout);
    }else if(!strcmp(argv[1],"quote")){
        ok=!memchr(data,0,n)&&geo_json_quote(data,out,n*6+4096);
        if(ok)fputs(out,stdout);
    }else{
        ok=geo_json_parse_n(&j,data,n);
        if(ok && !strcmp(argv[1],"canonical")){
            ok=geo_json_canonical(&j,0,out,n*6+4096);
            if(ok)fputs(out,stdout);
        }else if(ok && !strcmp(argv[1],"keys")){
            ok=geo_json_keys(&j,0,"id,version","name");
        }else if(ok && !strcmp(argv[1],"accessors")){
            int array=geo_json_member(&j,0,"values"),boolean=-1;
            int64_t integer=0;char text[8];char tiny[2]={'x',0};size_t z;
            ok=geo_json_is_object(&j,0)&&geo_json_size(&j,0)==2
                &&geo_json_is_array(&j,array)&&geo_json_size(&j,array)==4
                &&geo_json_integer(&j,geo_json_at(&j,array,0),&integer)&&integer==INT64_MIN
                &&geo_json_boolean(&j,geo_json_at(&j,array,1),&boolean)&&boolean==1
                &&!geo_json_integer(&j,geo_json_at(&j,array,1),&integer)
                &&geo_json_is_null(&j,geo_json_at(&j,array,2))
                &&geo_json_string(&j,geo_json_at(&j,array,3),text,sizeof(text))&&!strcmp(text,"abc")
                &&geo_json_at(&j,array,-1)==-1&&geo_json_at(&j,array,4)==-1
                &&geo_json_member(&j,0,"missing")==-1
                &&!geo_json_canonical(&j,0,tiny,sizeof(tiny))&&!tiny[0]
                &&!geo_json_quote("abc",tiny,sizeof(tiny))&&!tiny[0]
                &&!geo_json_string(&j,geo_json_at(&j,array,3),tiny,sizeof(tiny))
                &&!geo_base64_encode("a",1,tiny,sizeof(tiny),&z)
                &&!geo_base64_decode("YWJj",4,tiny,sizeof(tiny),&z);
        }else if(ok)ok=0;
        if(!ok)fputs(j.error,stderr);
        geo_json_free(&j);
    }
    free(data);free(out);return ok?0:1;
}
