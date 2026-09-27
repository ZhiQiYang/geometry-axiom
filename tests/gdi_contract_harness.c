/* Function-level integration with real Win32 GDI handles and injected failures.
 * The layout client rectangle/control moves are mocked: this is NOT GUI E2E.
 * Build/run instructions are in test_gdi_contract.py. Outputs belong in TEMP.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <assert.h>
#undef assert
#define assert(condition) do { if (!(condition)) { fprintf(stderr,"AUDIT ASSERT line %d: %s\n",__LINE__,#condition); exit(3); } } while (0)

enum {FAIL_NONE,FAIL_SCREEN,FAIL_DC,FAIL_BITMAP,FAIL_SELECT,FAIL_FREQUENCY};
static int fail_api,fail_n,api_calls[6],failure_hits,verified_failures,screen_count,dc_count,bitmap_count,delete_failed;
static HGDIOBJ bitmaps[100];
static int bitmap_slots;
static int move_count,negative_move,fake_client,test_width,test_height;
static int force_ferror,force_fclose,removed,ferror_hits,fclose_hits;
static int failing(int api){
  api_calls[api]++;
#ifdef AUDIT_DISABLE_FAILURES
  /* Sensitivity witness: compiling with this flag MUST make the suite fail. */
  return 0;
#else
  if(api==fail_api && api_calls[api]==fail_n){failure_hits++;return 1;}
  return 0;
#endif
}
static HDC audit_GetDC(HWND window){HDC dc=failing(FAIL_SCREEN)?NULL:GetDC(window);if(dc)screen_count++;return dc;}
static int audit_ReleaseDC(HWND window,HDC dc){int ok=ReleaseDC(window,dc);if(ok)screen_count--;return ok;}
static HDC audit_CreateCompatibleDC(HDC parent){HDC dc=failing(FAIL_DC)?NULL:CreateCompatibleDC(parent);if(dc)dc_count++;return dc;}
static BOOL audit_DeleteDC(HDC dc){BOOL ok=DeleteDC(dc);if(ok)dc_count--;else delete_failed++;return ok;}
static HBITMAP audit_CreateCompatibleBitmap(HDC dc,int w,int h){HBITMAP bitmap=failing(FAIL_BITMAP)?NULL:CreateCompatibleBitmap(dc,w,h);if(bitmap){bitmap_count++;bitmaps[bitmap_slots++]=bitmap;}return bitmap;}
static HGDIOBJ audit_SelectObject(HDC dc,HGDIOBJ obj){
  int own=0;for(int i=0;i<bitmap_slots;i++)if(bitmaps[i]==obj)own=1;
  if(own && failing(FAIL_SELECT))return HGDI_ERROR;
  return SelectObject(dc,obj);
}
static BOOL audit_DeleteObject(HGDIOBJ obj){
  BOOL ok=DeleteObject(obj);
  for(int i=0;i<bitmap_slots;i++)if(bitmaps[i]==obj){if(ok){bitmap_count--;bitmaps[i]=NULL;}else delete_failed++;break;}
  return ok;
}
static BOOL audit_QueryPerformanceFrequency(LARGE_INTEGER *frequency){return failing(FAIL_FREQUENCY)?FALSE:QueryPerformanceFrequency(frequency);}
static BOOL audit_MoveWindow(HWND window,int x,int y,int w,int h,BOOL repaint){
  if(fake_client){move_count++;if(x<0||y<0||w<0||h<0)negative_move++;return TRUE;}
  return MoveWindow(window,x,y,w,h,repaint);
}
static BOOL audit_GetClientRect(HWND window,LPRECT rect){if(fake_client){*rect=(RECT){0,0,test_width,test_height};return TRUE;}return GetClientRect(window,rect);}
static HWND audit_GetDlgItem(HWND window,int id){return fake_client?(HWND)(intptr_t)id:GetDlgItem(window,id);}
static int audit_ferror(FILE *stream){if(force_ferror){ferror_hits++;return 1;}return ferror(stream);}
static int audit_fclose(FILE *stream){int actual=fclose(stream);if(force_fclose){fclose_hits++;return EOF;}return actual;}
static int audit_remove(const char *path){removed++;return remove(path);}

#define GetDC audit_GetDC
#define ReleaseDC audit_ReleaseDC
#define CreateCompatibleDC audit_CreateCompatibleDC
#define DeleteDC audit_DeleteDC
#define CreateCompatibleBitmap audit_CreateCompatibleBitmap
#define SelectObject audit_SelectObject
#define DeleteObject audit_DeleteObject
#define QueryPerformanceFrequency audit_QueryPerformanceFrequency
#define MoveWindow audit_MoveWindow
#define GetClientRect audit_GetClientRect
#define GetDlgItem audit_GetDlgItem
#define ferror audit_ferror
#define fclose audit_fclose
#define remove audit_remove
#define main geometry_core_main
#include "current_geometry.c"
#undef main

static void bench_case(const Scene *scene,const SceneLayout *layout,int api,int occurrence,int iters){
  fail_api=api;fail_n=occurrence;memset(api_calls,0,sizeof api_calls);bitmap_slots=0;failure_hits=0;
  bench_paint(scene,layout,iters);
  if(api!=FAIL_NONE){assert(api_calls[api]>=occurrence);assert(failure_hits==1);verified_failures++;}
  else {assert(failure_hits==0);assert(api_calls[FAIL_SCREEN]==(iters>0?1:0));}
  assert(screen_count==0);assert(dc_count==0);assert(bitmap_count==0);assert(delete_failed==0);
  printf("PASS bench %s api=%d occurrence=%d iterations=%d calls=%d hits=%d\n",
    api==FAIL_NONE?(iters>0?"success":"no-op"):"injected-failure",api,occurrence,iters,api_calls[api],failure_hits);
}
int main(void){
  const char *invalid[]={NULL,"","#","123456","#12345","#1234567","#12345g","# 23456","#12+456","#-23456","##12345"};
  for(size_t i=0;i<sizeof invalid/sizeof invalid[0];i++)assert(gdi_color(invalid[i])==RGB(0,0,0));
  assert(gdi_color("#aBcD09")==RGB(171,205,9));
  for(int i=0;i<STYLE_COUNT;i++){
    const char *values[]={STYLE_SPEC[i].line,STYLE_SPEC[i].fill,STYLE_SPEC[i].gdi_fill};
    for(int j=0;j<3;j++)if(values[j]){
      unsigned r,g,b;assert(strlen(values[j])==7);assert(sscanf(values[j],"#%2x%2x%2x",&r,&g,&b)==3);
      assert(gdi_color(values[j])==RGB(r,g,b));
    }
  }
  puts("PASS colors: malformed strings + every STYLE_SPEC color");
  fake_client=1;GdiApp app={0};
  const int sizes[][2]={{0,0},{1,1},{15,5},{100,20},{175,33},{1100,800}};
  for(size_t i=0;i<sizeof sizes/sizeof sizes[0];i++){
    test_width=sizes[i][0];test_height=sizes[i][1];move_count=negative_move=0;
    gdi_layout_input_bar((HWND)1,&app);assert(move_count==5);assert(negative_move==0);
  }
  fake_client=0;puts("PASS tiny layouts: 0x0 through restored 1100x800; no negative MoveWindow arguments");
  World world={0};assert(reference_default_world(&world));Scene scene=scene_from_world(&world);SceneLayout layout;
  assert(scene_compute_layout(&scene,&layout));
  bench_case(&scene,&layout,FAIL_NONE,0,2);
  DWORD initial=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
  bench_case(&scene,&layout,FAIL_SCREEN,1,1);
  bench_case(&scene,&layout,FAIL_NONE,0,0);
  for(int api=FAIL_DC;api<=FAIL_SELECT;api++)for(int n=1;n<=3;n++)bench_case(&scene,&layout,api,n,1);
  bench_case(&scene,&layout,FAIL_FREQUENCY,1,1);
  bench_case(&scene,&layout,FAIL_NONE,0,10);
  assert(verified_failures==11);
  assert(GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS)==initial);
  puts("PASS actual Windows GDI count unchanged; 11 confirmed injected failures, 2 successes, 1 no-op");
  fail_api=FAIL_NONE;
  removed=0;force_ferror=1;assert(!emit_svg_three_views("partial-ferror.svg",&scene,&layout));assert(ferror_hits==1);assert(removed==1);assert(GetFileAttributesA("partial-ferror.svg")==INVALID_FILE_ATTRIBUTES);
  removed=0;force_ferror=0;force_fclose=1;assert(!emit_svg_three_views("partial-close.svg",&scene,&layout));assert(fclose_hits==1);assert(removed==1);assert(GetFileAttributesA("partial-close.svg")==INVALID_FILE_ATTRIBUTES);
  removed=0;force_fclose=0;assert(emit_svg_three_views("complete.svg",&scene,&layout));assert(removed==0);assert(GetFileAttributesA("complete.svg")!=INVALID_FILE_ATTRIBUTES);
  removed=0;force_ferror=1;assert(!emit_svg_three_views("NUL",&scene,&layout));assert(removed==0);force_ferror=0;
  puts("PASS SVG ferror/fclose partial cleanup; Windows NUL device never passed to remove");
  return 0;
}
