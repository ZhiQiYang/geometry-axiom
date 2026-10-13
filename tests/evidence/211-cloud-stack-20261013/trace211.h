#include <stdint.h>
#include <stdio.h>
#define NOINST __attribute__((no_instrument_function))
static uintptr_t trace_top, trace_peak;
static void *trace_chain[256], *trace_peak_chain[256];
static int trace_depth, trace_peak_depth;
NOINST __attribute__((constructor)) static void trace_start(void) {trace_top=(uintptr_t)__builtin_frame_address(0);}
NOINST void __cyg_profile_func_enter(void *fn, void *caller) {
    uintptr_t sp=(uintptr_t)__builtin_frame_address(0);
    if(!trace_top)trace_top=sp;
    if(trace_depth<256)trace_chain[trace_depth]=fn;
    trace_depth++;
    uintptr_t used=trace_top-sp;
    if(used>trace_peak && trace_depth<=256){trace_peak=used; trace_peak_depth=trace_depth; for(int i=0;i<trace_depth;i++)trace_peak_chain[i]=trace_chain[i];}
}
NOINST void __cyg_profile_func_exit(void *fn, void *caller) {trace_depth--;}
NOINST __attribute__((destructor)) static void trace_summary(void) {
    fprintf(stderr,"TRACE211 peak_relative_bytes=%lu call_depth=%d\n",(unsigned long)trace_peak,trace_peak_depth);
    for(int i=0;i<trace_peak_depth;i++)fprintf(stderr,"TRACE211 frame %d %p\n",i,trace_peak_chain[i]);
}
