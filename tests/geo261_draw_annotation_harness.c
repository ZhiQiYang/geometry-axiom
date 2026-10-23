/* Exercise the production dispatch and SVG fallback, without a GDI window. */
#ifdef _WIN32
#undef _WIN32
#endif
#define main geometry_cli_main
#include "../current_geometry.c"
#undef main

static int text_calls, annotation_calls;
static const DrawTextAnnotation *seen_annotation;
static char seen_text[128];
static ViewPoint2 seen_at;
static DrawStyle seen_style;
static int seen_rotation;

static void capture_text(void *ctx, ViewPoint2 at, DrawStyle style,
                         const char *text, int rotation)
{
    (void)ctx;
    ++text_calls; seen_at=at; seen_style=style; seen_rotation=rotation;
    snprintf(seen_text,sizeof seen_text,"%s",text);
}

static void capture_annotation(void *ctx, ViewPoint2 at, DrawStyle style,
                               const char *text, int rotation,
                               const DrawTextAnnotation *annotation)
{
    capture_text(ctx,at,style,text,rotation);
    ++annotation_calls; seen_annotation=annotation;
}

int main(int argc,char **argv)
{
    const DrawTextAnnotation annotation={"member-face",UINT32_MAX,"START","short"};
    const ViewPoint2 at={123,-456};
    /* A deliberately unrelated full label proves dispatch does not parse it. */
    const char *full="opaque full label";
    if(argc!=2)return 2;
    if(strcmp(argv[1],"fallback")==0){
        DrawTarget target={0}; target.text=capture_text;
        scene_emit_annotated_text(NULL,at,STYLE_TIMBER_LABEL,full,90,&annotation);
        if(text_calls!=0)return 1;
        scene_emit_annotated_text(&target,at,STYLE_TIMBER_LABEL,full,90,&annotation);
        if(text_calls!=1||annotation_calls!=0||strcmp(seen_text,full)||
           seen_at.x!=123||seen_at.y!=-456||seen_rotation!=90||seen_style!=STYLE_TIMBER_LABEL)return 1;
        target.annotated_text=capture_annotation;
        scene_emit_annotated_text(&target,at,STYLE_TIMBER_LABEL,full,90,&annotation);
        if(text_calls!=2||annotation_calls!=1||seen_annotation!=&annotation||strcmp(seen_text,full))return 1;
        scene_emit_text(&target,at,STYLE_LABEL,"ordinary",0);
        return text_calls==3&&annotation_calls==1&&!strcmp(seen_text,"ordinary")?0:1;
    }
    if(strcmp(argv[1],"svg")==0){
        FILE *file=tmpfile(); if(!file)return 2;
        DrawTarget target=SVG_TARGET; target.ctx=file;
        scene_emit_annotated_text(&target,at,STYLE_TIMBER_LABEL,full,90,&annotation);
        rewind(file); char actual[512]={0}; size_t count=fread(actual,1,sizeof actual-1,file); fclose(file);
        const char *expected="<text x=\"123\" y=\"-456\" class=\"label timber-label\" transform=\"rotate(90 123 -456)\">opaque full label</text>\n";
        return count==strlen(expected)&&strcmp(actual,expected)==0?0:1;
    }
    return 2;
}
