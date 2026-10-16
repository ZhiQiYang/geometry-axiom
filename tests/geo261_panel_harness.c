#include "panel_support.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(name,condition) do{if(!(condition)){fprintf(stderr,"ASSERT:%s\n",name);return 1;}}while(0)
bool frozen_panel_build(const WoodPanelLayoutInput *,WoodPanelLayout *);
bool frozen_panel_clip(const GeoRegionView *,const GeoRect2 *,const GeoRect2 *,size_t,bool,size_t *,GeoClipResult *);
bool frozen_panel_support(const WoodPanelLayout *,const WoodPanelFootprint *,size_t,GeoQuantity,WoodPanelSupport *);

static GeoFrame identity(void)
{return (GeoFrame){{0,0,0},{1,0,0},{0,1,0},{0,0,1}};}
static void box(GeoPoint2 *v,GeoCoord a,GeoCoord b,GeoCoord c,GeoCoord d)
{v[0]=(GeoPoint2){a,b};v[1]=(GeoPoint2){c,b};v[2]=(GeoPoint2){c,d};v[3]=(GeoPoint2){a,d};}
static bool same_points(const GeoClipLoop *a,const GeoClipLoop *b)
{if(a->count!=b->count||a->hole!=b->hole)return false;for(size_t i=0;i<a->count;++i)if(a->points[i].u!=b->points[i].u||a->points[i].v!=b->points[i].v)return false;return true;}
static bool same_clip(const GeoClipResult *a,const GeoClipResult *b)
{if(a->count!=b->count||a->area!=b->area)return false;for(size_t f=0;f<a->count;++f){if(a->fragments[f].count!=b->fragments[f].count||a->fragments[f].area!=b->fragments[f].area)return false;
 for(size_t l=0;l<a->fragments[f].count;++l)if(!same_points(&a->fragments[f].loops[l],&b->fragments[f].loops[l]))return false;}return true;}
static bool same_layout(const WoodPanelLayout *a,const WoodPanelLayout *b)
{if(a->count!=b->count||a->fragments!=b->fragments||a->vertices!=b->vertices||a->whole!=b->whole||a->seam_count!=b->seam_count||a->size[0]!=b->size[0]||a->size[1]!=b->size[1]||a->gap!=b->gap||a->stagger!=b->stagger)return false;
 for(size_t i=0;i<a->count;++i){const WoodPanelTile *x=&a->tiles[i],*y=&b->tiles[i];if(x->i!=y->i||x->j!=y->j)return false;for(int k=0;k<4;++k)if(x->body[k]!=y->body[k])return false;
  GeoClipResult u={x->fragments,x->count,x->area},v={y->fragments,y->count,y->area};if(!same_clip(&u,&v))return false;}
 for(size_t i=0;i<a->seam_count;++i){const WoodPanelSeamLine *x=&a->seams[i],*y=&b->seams[i];if(x->axis!=y->axis||x->k!=y->k||x->band!=y->band||x->coordinate!=y->coordinate||x->staggered!=y->staggered||x->range[0]!=y->range[0]||x->range[1]!=y->range[1])return false;}return true;}
static bool same_support(const WoodPanelSupport *a,const WoodPanelSupport *b)
{if(a->count!=b->count||a->non_count!=b->non_count||a->part_count!=b->part_count)return false;
 for(int group=0;group<2;++group){size_t n=group?a->non_count:a->count;const WoodPanelEffectiveSeam *x=group?a->nonseams:a->seams,*y=group?b->nonseams:b->seams;
  for(size_t i=0;i<n;++i)if(x[i].line!=y[i].line||x[i].range[0]!=y[i].range[0]||x[i].range[1]!=y[i].range[1]||x[i].edges[0]!=y[i].edges[0]||x[i].edges[1]!=y[i].edges[1])return false;}
 for(size_t i=0;i<a->part_count;++i){const WoodPanelSupportPart *x=&a->parts[i],*y=&b->parts[i];if(x->seam!=y->seam||x->range[0]!=y->range[0]||x->range[1]!=y->range[1]||x->left!=y->left||x->right!=y->right||x->supported!=y->supported)return false;}return true;}

static int clipping(void)
{
    GeoPoint2 outer[4],hole[4];box(outer,0,0,10,10);box(hole,2,2,8,8);GeoLoop2View holes[]={{hole,4}};
    GeoRegionView r={{outer,4},holes,1};GeoRect2 body={0,0,10,10};GeoClipResult result={0};size_t vertices=0;
    CHECK("clip-hole-ok",geo_region_clip_rect_minus_rects(&r,&body,NULL,0,false,32768,&vertices,&result)==GEO_CLIP_OK);
    CHECK("clip-hole-area",result.area==64&&result.count==1&&result.fragments[0].count==2);
    GeoPoint2 expected_outer[]={{0,0},{10,0},{10,10},{0,10}},expected_hole[]={{2,2},{2,8},{8,8},{8,2}};
    GeoClipLoop a={expected_outer,4,false},b={expected_hole,4,true};
    CHECK("clip-canonical-orientation",same_points(&result.fragments[0].loops[0],&a)&&same_points(&result.fragments[0].loops[1],&b));
    CHECK("clip-vertex-count",vertices==8);geo_clip_result_free(&result);
    box(outer,0,0,20,20);r.hole_count=0;body=(GeoRect2){0,0,20,20};GeoRect2 cuts[]={{10,0,20,10},{0,10,10,20}};vertices=0;
    CHECK("clip-touch-ok",geo_region_clip_rect_minus_rects(&r,&body,cuts,2,false,32768,&vertices,&result)==GEO_CLIP_OK);
    CHECK("clip-point-touch-components",result.count==2&&result.area==200&&result.fragments[0].area==100&&result.fragments[1].area==100);
    CHECK("clip-component-order",result.fragments[0].loops[0].points[0].u==0&&result.fragments[1].loops[0].points[0].u==10);
    geo_clip_result_free(&result);cuts[0]=body;vertices=0;
    CHECK("clip-empty-is-valid",geo_region_clip_rect_minus_rects(&r,&body,cuts,1,false,32768,&vertices,&result)==GEO_CLIP_OK&&result.count==0&&result.area==0&&vertices==0);
    geo_clip_result_free(&result);box(outer,0,0,10,10);body=(GeoRect2){0,0,10,10};
    cuts[0]=(GeoRect2){2,2,5,5};cuts[1]=(GeoRect2){5,5,8,8};vertices=0;
    CHECK("clip-touching-holes-ok",geo_region_clip_rect_minus_rects(&r,&body,cuts,2,false,32768,&vertices,&result)==GEO_CLIP_OK);
    CHECK("clip-touching-holes-split",result.count==1&&result.area==82&&result.fragments[0].count==3&&result.fragments[0].loops[1].hole&&result.fragments[0].loops[2].hole);
    geo_clip_result_free(&result);return 0;
}
static int capacity(void)
{
    GeoPoint2 outer[4];box(outer,0,0,10,10);GeoRegionView r={{outer,4},NULL,0};GeoRect2 body={0,0,10,10},cut={5,20,6,30};GeoClipResult result={0};size_t vertices=0;
    CHECK("clip-collinear-ok",geo_region_clip_rect_minus_rects(&r,&body,&cut,1,false,32768,&vertices,&result)==GEO_CLIP_OK);
    CHECK("clip-removes-subdivision",vertices==4&&result.fragments[0].loops[0].count==4);geo_clip_result_free(&result);vertices=0;
    CHECK("clip-kept-ok",geo_region_clip_rect_minus_rects(&r,&body,&cut,1,true,32768,&vertices,&result)==GEO_CLIP_OK);
    CHECK("clip-keeps-subdivision",vertices==8&&result.fragments[0].loops[0].count==8);geo_clip_result_free(&result);vertices=4;
    CHECK("clip-cumulative-budget",geo_region_clip_rect_minus_rects(&r,&body,NULL,0,false,7,&vertices,&result)==GEO_CLIP_VERTEX_LIMIT&&vertices==4);
    geo_clip_result_free(&result);vertices=4;
    CHECK("clip-exact-budget",geo_region_clip_rect_minus_rects(&r,&body,NULL,0,false,8,&vertices,&result)==GEO_CLIP_OK&&vertices==8);geo_clip_result_free(&result);
    box(outer,0,0,1000,1000);body=(GeoRect2){0,0,1000,1000};GeoRect2 cuts[64];for(int i=0;i<64;++i)cuts[i]=(GeoRect2){2*i+1,1100,2*i+2,1200};vertices=0;
    CHECK("clip-axis-capacity",geo_region_clip_rect_minus_rects(&r,&body,cuts,64,false,32768,&vertices,&result)==GEO_CLIP_AXIS_LIMIT&&result.count==0&&vertices==0);geo_clip_result_free(&result);return 0;
}
static int layout(void)
{
    GeoPoint2 outer[4];box(outer,-20,-20,20,20);WoodPanelLayoutInput input={0};input.region=(GeoRegionView){{outer,4},NULL,0};input.frame=identity();input.size[0]=input.size[1]=10;input.stagger=5;input.stagger_axis=0;
    WoodPanelLayout d;GeoClipStatus detail;CHECK("layout-stagger-ok",wood_panel_layout_build(&input,&d,&detail)==WOOD_PANEL_OK);
    const WoodPanelTile *target=NULL;for(size_t i=0;i<d.count;++i)if(d.tiles[i].i==-1&&d.tiles[i].j==-1)target=&d.tiles[i];
    CHECK("layout-negative-odd-shift",target&&target->body[0]==-5&&target->body[1]==-10&&target->body[2]==5&&target->body[3]==0);
    bool found=false;for(size_t i=0;i<d.seam_count;++i){WoodPanelSeamLine *s=&d.seams[i];if(s->axis==0&&s->k==-1&&s->band==-1)found=s->coordinate==5&&s->range[0]==-10&&s->range[1]==0;}
    CHECK("layout-negative-band-identity",found);wood_panel_layout_free(&d);
    box(outer,0,0,23,10);input.gap=3;input.stagger=0;input.stagger_axis=-1;
    CHECK("layout-gap-ok",wood_panel_layout_build(&input,&d,&detail)==WOOD_PANEL_OK);
    CHECK("layout-gap-bodies",d.count==2&&d.tiles[0].body[2]==10&&d.tiles[1].body[0]==13&&d.whole==2);
    found=false;for(size_t i=0;i<d.seam_count;++i)if(d.seams[i].axis==0&&d.seams[i].k==0)found=d.seams[i].coordinate==11;
    CHECK("layout-odd-gap-center",found);wood_panel_layout_free(&d);
    input.frame.origin.x=GEO_COORD_LIMIT;CHECK("layout-world-range",wood_panel_layout_build(&input,&d,&detail)==WOOD_PANEL_VERTEX_RANGE&&d.tiles==NULL&&d.count==0);
    input.frame=identity();box(outer,0,0,11000,10);input.gap=0;
    CHECK("layout-whole-enumeration-capacity",wood_panel_layout_build(&input,&d,&detail)==WOOD_PANEL_ENUM_LIMIT&&d.tiles==NULL&&d.count==0);return 0;
}
static size_t seam_parts(const WoodPanelLayout *d,const WoodPanelSupport *s,GeoCoord coordinate,const WoodPanelSupportPart **parts)
{size_t n=0;for(size_t i=0;i<s->part_count;++i){const WoodPanelSupportPart *p=&s->parts[i];const WoodPanelSeamLine *line=&d->seams[s->seams[p->seam].line];if(line->axis==0&&line->coordinate==coordinate)parts[n++]=p;}return n;}
static int support(void)
{
    GeoPoint2 outer[4];box(outer,0,0,1000,300);GeoRect2 hole={105,50,200,100};WoodPanelLayoutInput input={0};input.region=(GeoRegionView){{outer,4},NULL,0};input.frame=identity();input.size[0]=1000;input.size[1]=300;input.origin[0]=-900;input.stagger_axis=-1;input.cuts=&hole;input.cut_count=1;
    WoodPanelLayout d;GeoClipStatus detail;CHECK("support-layout",wood_panel_layout_build(&input,&d,&detail)==WOOD_PANEL_OK);
    WoodPanelFootprint rects[]={{{90,0},{105,300}},{{105,0},{120,300}},{{-100,75},{-90,125}}};WoodPanelSupport s;const WoodPanelSupportPart *parts[32];
    CHECK("support-evaluation",wood_panel_support_evaluate(&d,rects,3,64,(GeoQuantity){8,1,1},&s)==WOOD_PANEL_SUPPORT_OK);
    size_t n=seam_parts(&d,&s,100,parts);CHECK("support-fragment-vertices",n==3&&parts[0]->range[0]==0&&parts[0]->range[1]==50&&parts[1]->range[1]==100&&parts[2]->range[1]==300);
    CHECK("support-touching-union",parts[0]->left==10&&parts[0]->right==20&&parts[1]->left==10&&parts[1]->right==5&&parts[2]->right==20);
    CHECK("support-insufficient-is-result",parts[0]->supported&&!parts[1]->supported&&parts[2]->supported);wood_panel_support_free(&s);
    CHECK("support-same-colour-eval",wood_panel_support_evaluate(&d,rects,3,64,(GeoQuantity){5,1,1},&s)==WOOD_PANEL_SUPPORT_OK);
    n=seam_parts(&d,&s,100,parts);CHECK("support-widths-not-colours",n==3&&parts[0]->supported&&parts[1]->supported&&parts[2]->supported);wood_panel_support_free(&s);
    CHECK("support-rational-eval",wood_panel_support_evaluate(&d,rects,3,64,(GeoQuantity){101,20,1},&s)==WOOD_PANEL_SUPPORT_OK);
    n=seam_parts(&d,&s,100,parts);CHECK("support-rational-not-rounded",n==3&&!parts[1]->supported);wood_panel_support_free(&s);
    CHECK("support-source-limit",wood_panel_support_evaluate(&d,rects,65,64,(GeoQuantity){8,1,1},&s)==WOOD_PANEL_SUPPORT_FOOTPRINT_LIMIT&&!s.seams&&!s.parts&&!s.count);wood_panel_support_free(&s);
    CHECK("support-empty-set-eval",wood_panel_support_evaluate(&d,NULL,0,64,(GeoQuantity){8,1,1},&s)==WOOD_PANEL_SUPPORT_OK);
    n=seam_parts(&d,&s,100,parts);CHECK("support-empty-set-zero",n==1&&parts[0]->left==0&&parts[0]->right==0&&!parts[0]->supported);wood_panel_support_free(&s);wood_panel_layout_free(&d);return 0;
}
static int equivalence(void)
{
    GeoPoint2 outer[4],hole[4];box(outer,-20,-15,30,25);box(hole,-5,-5,5,5);GeoLoop2View holes[]={{hole,4}};GeoRect2 cuts[]={{8,-30,12,30},{-25,10,35,14},{0,0,15,15}};
    GeoRegionView region={{outer,4},holes,0};GeoRect2 body={-25,-20,35,30};
    for(size_t h=0;h<2;++h)for(size_t count=0;count<4;++count)for(int keep=0;keep<2;++keep){region.hole_count=h;GeoClipResult a={0},b={0};size_t va=3,vb=3;
        GeoClipStatus status=geo_region_clip_rect_minus_rects(&region,&body,cuts,count,keep!=0,32768,&va,&a);bool old=frozen_panel_clip(&region,&body,cuts,count,keep!=0,&vb,&b);
        CHECK("frozen-clipping-verdict",(status==GEO_CLIP_OK)==old);CHECK("frozen-clipping-result",va==vb&&same_clip(&a,&b));geo_clip_result_free(&a);geo_clip_result_free(&b);}
    for(int axis=-1;axis<2;++axis)for(int gap=0;gap<4;gap+=3)for(int origin=-7;origin<=7;origin+=7)for(size_t count=0;count<3;++count){
        WoodPanelLayoutInput input={0};input.region=region;input.frame=identity();input.size[0]=17;input.size[1]=13;input.gap=gap;input.stagger=5;input.stagger_axis=axis;input.origin[0]=origin;input.origin[1]=-origin;input.cuts=cuts;input.cut_count=count;
        if(origin>0)input.frame=(GeoFrame){{10,20,30},{0,1,0},{0,0,1},{1,0,0}};
        WoodPanelLayout a,b;GeoClipStatus detail;WoodPanelStatus status=wood_panel_layout_build(&input,&a,&detail);bool old=frozen_panel_build(&input,&b);
        CHECK("frozen-layout-verdict",(status==WOOD_PANEL_OK)==old);CHECK("frozen-layout-result",same_layout(&a,&b));
        if(status==WOOD_PANEL_OK){WoodPanelFootprint rects[]={{{-100,-100},{100,100}},{{-8,-8},{3,11}},{{3,-8},{15,11}}};
            for(size_t nr=0;nr<4;++nr){WoodPanelSupport x,y;GeoQuantity threshold=nr==3?(GeoQuantity){INT64_MAX,INT64_MAX/10,1}:(GeoQuantity){15,2,1};
                WoodPanelSupportStatus st=wood_panel_support_evaluate(&a,rects,nr,64,threshold,&x);bool ok=frozen_panel_support(&b,rects,nr,threshold,&y);
                CHECK("frozen-support-verdict",(st==WOOD_PANEL_SUPPORT_OK)==ok);CHECK("frozen-support-result",same_support(&x,&y));wood_panel_support_free(&x);wood_panel_support_free(&y);}}
        wood_panel_layout_free(&a);wood_panel_layout_free(&b);}
    return 0;
}
int main(int argc,char **argv)
{if(argc!=2)return 2;if(!strcmp(argv[1],"clip"))return clipping();if(!strcmp(argv[1],"capacity"))return capacity();if(!strcmp(argv[1],"layout"))return layout();if(!strcmp(argv[1],"support"))return support();if(!strcmp(argv[1],"equivalence"))return equivalence();return 2;}
