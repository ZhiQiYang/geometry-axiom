#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <dlfcn.h>
static FILE *target;
FILE *tmpfile(void) {
    static unsigned calls;
    FILE *(*real_tmpfile)(void)=dlsym(RTLD_NEXT,"tmpfile");
    if(++calls!=3)return real_tmpfile();
    const char *mode=getenv("WP60_IO_FAULT");
    if(mode&&!strcmp(mode,"open")){errno=ENOSPC;return NULL;}
    if(mode&&!strcmp(mode,"write"))return fopen("/dev/full","w+");
    target=real_tmpfile();return target;
}
size_t fread(void *ptr,size_t size,size_t count,FILE *stream) {
    size_t (*real_fread)(void *,size_t,size_t,FILE *)=dlsym(RTLD_NEXT,"fread");
    const char *mode=getenv("WP60_IO_FAULT");
    if(stream==target&&mode&&!strcmp(mode,"read")){errno=EIO;return 0;}
    return real_fread(ptr,size,count,stream);
}
