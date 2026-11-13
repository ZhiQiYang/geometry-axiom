/* P-103: explicit algorithm-only footprints. This is a test executable,
 * never an input path exposed by the product bridge. Uses the same evaluator. */
#define main geometry_program_main
#include "../current_geometry.c"
#undef main
static World world;
static int capacity_check(void)
{
    SurfacePoint2 a[]={{0,0},{100,0},{100,300},{0,300}},b[]={{100,0},{200,0},{200,300},{100,300}};
    PfLoop loops[]={{a,4,false},{b,4,false}};PfFragment fragments[]={{&loops[0],1,30000},{&loops[1],1,30000}};
    PfTile tiles[2]={0};tiles[0].body[2]=100;tiles[0].body[3]=300;tiles[1].body[0]=100;tiles[1].body[2]=200;tiles[1].body[3]=300;
    for(int i=0;i<2;++i){tiles[i].count=1;tiles[i].fragments=&fragments[i];}
    PfSeamLine *lines=calloc(PF_SUPPORT_MAX+1,sizeof *lines);if(!lines)return 2;
    for(size_t i=0;i<=PF_SUPPORT_MAX;++i)lines[i].coordinate=100;
    PfLayout d={0};d.layout.tiles=tiles;d.layout.count=2;d.layout.vertices=8;d.layout.seams=lines;d.layout.seam_count=PF_SUPPORT_MAX;PfSupport s;
    bool ok=pf_support_evaluate(&d,NULL,0,(GeoQuantity){8,1,1},&s);
    if(!ok||s.count!=PF_SUPPORT_MAX||s.part_count!=PF_SUPPORT_MAX){fprintf(stderr,"PF3_CAPACITY_N: complete N results required\n");pf_support_free(&s);free(lines);return 1;}
    pf_support_free(&s);d.layout.seam_count=PF_SUPPORT_MAX+1;
    ok=pf_support_evaluate(&d,NULL,0,(GeoQuantity){8,1,1},&s);
    bool rejected=!ok&&g_fs_diagnostic==FS_DIAGNOSTIC_CAPACITY&&strstr(g_engineering_error,"limit")&&!s.count&&!s.part_count&&!s.seams&&!s.parts;
    pf_support_free(&s);free(lines);
    if(!rejected){fprintf(stderr,"PF3_CAPACITY_N1: reject and discard whole output, never truncate\n");return 1;}
    puts("[32768,32768,0]");return 0;
}
int main(int argc,char **argv)
{
    if(argc==2&&!strcmp(argv[1],"--capacity"))return capacity_check();
    if(argc<2||(argc-2)%4||(argc-2)/4>WORLD_MAX_TIMBERS)return 2;
    if(!parse_scene_file(argv[1],&world)){fprintf(stderr,"PF3_ALGORITHM_SCENE: %s\n",scene_last_error());return 2;}
    const PanelFill *p=pf_find(&world,1);if(!p)return 2;
    PfFootprint *rects=calloc(WORLD_MAX_TIMBERS,sizeof *rects);if(!rects)return 2;
    size_t nr=(size_t)(argc-2)/4;
    for(size_t i=0;i<nr;++i){Coord values[4];for(int k=0;k<4;++k)if(!parse_coord(argv[2+4*i+k],&values[k])){free(rects);return 2;}
        if(values[0]>=values[2]||values[1]>=values[3]){free(rects);return 2;}
        rects[i]=(PfFootprint){{values[0],values[1]},{values[2],values[3]}};
    }
    PfLayout d;PfSupport s={0};GeoQuantity x;
    bool ok=parameter_value(&world,p->threshold,&x)&&pf_build(&world,p,&d);
    if(!ok){free(rects);return 2;}
    ok=pf_support_evaluate(&d,rects,nr,x,&s);
    if(!ok)fprintf(stderr,"PF3_ALGORITHM: %s\n",g_engineering_error);
    else {putchar('[');bool first=true;
        for(size_t i=0;i<s.part_count;++i){const PfSupportPart *v=&s.parts[i];const PfSeamLine *line=&d.layout.seams[s.seams[v->seam].line];
            if(line->axis||line->coordinate!=100)continue;
            printf("%s[%lld,%lld,%lld,%lld,%s]",first?"":",",(long long)v->range[0],(long long)v->range[1],(long long)v->left,(long long)v->right,v->supported?"true":"false");first=false;}
        puts("]");}
    free(rects);pf_support_free(&s);pf_free(&d);return ok?0:1;
}
