static void json_parameter_canvas_target(const World *w,uint32_t placement_id,bool *first)
{
    const PlacementSurface *p=world_find_placement(w,placement_id);if(!p)return;
    printf("%s{\"kind\":\"%s\",\"id\":%u}",*first?"":",",p->boundary_id?"boundary":"placement",p->boundary_id?p->boundary_id:p->id);*first=false;
}
static void json_parameter_uses(const World *w)
{
    bool first=true;fputc('[',stdout);
    for(size_t i=0;i<w->engineering.binding_count;++i){const EngBinding *b=&w->engineering.bindings[i];
        for(int override=0;override<2;++override){const EngDimensionSource *s=override?&b->override_value:&b->source;if((override&&!b->has_override)||s->kind!=ENG_PARAMETER)continue;
            printf("%s{\"parameterId\":%u,\"fieldId\":%u,\"kind\":\"%s\",\"id\":%u,\"label\":",first?"":",",s->parameter.parameter_id,s->parameter.field_id,b->target.kind?"timber":"grid",b->target.id);first=false;
            char label[120];snprintf(label,sizeof label,"%s %u · %s%s",b->target.kind?"角材":"網格",b->target.id,b->target.kind?(b->target.field?"B":"A"):(b->target.field?"gap":"panel"),override?" 覆寫":"");js_string(label);
            fputs(",\"canvasTargets\":[",stdout);bool target_first=true;
            if(b->target.kind){for(size_t k=0;k<w->timber_count;++k)if(w->timbers[k].id==b->target.id)json_parameter_canvas_target(w,w->anchors[k].placement_id,&target_first);}
            else for(size_t k=0;k<w->grid_count;++k)if(w->grids[k].id==b->target.id)json_parameter_canvas_target(w,w->grids[k].placement_id,&target_first);
            fputs("]}",stdout);
        }
    }
    for(size_t i=0;i<w->assembly.binding_count;++i){const AsmBinding *b=&w->assembly.bindings[i];GeoJson j;
        if(app_json_parse(&j,b->content)){int slots=geo_json_member(&j,0,"slots");
            for(int k=0;k<geo_json_size(&j,slots);++k){int slot=geo_json_at(&j,slots,k);uint32_t sid=0;eng_u32(&j,geo_json_member(&j,slot,"slotId"),&sid,true);
                for(int axis=0;axis<2;++axis){EngDimensionSource src;int t=geo_json_member(&j,slot,axis?"B":"A");
                    if(geo_json_is_null(&j,t)||!eng_source_parse(&j,t,&src,false)||src.kind!=ENG_PARAMETER)continue;
                    printf("%s{\"parameterId\":%u,\"fieldId\":%u,\"kind\":\"assembly-binding\",\"id\":%u,\"label\":",first?"":",",src.parameter.parameter_id,src.parameter.field_id,b->id);first=false;
                    char label[160];snprintf(label,sizeof label,"組構配置 %u · 槽位 %u.%c",b->id,sid,axis?'B':'A');js_string(label);
                    printf(",\"canvasTargets\":[{\"kind\":\"assembly-binding\",\"id\":%u}]}",b->id);
                }
            }
        }geo_json_free(&j);
    }
    for(int kind=0;kind<2;++kind){size_t n=kind?w->datum_count:w->guide_count;
        for(size_t i=0;i<n;++i){const char *expr=kind?w->datums[i].expression:w->guides[i].expression;uint32_t id=kind?w->datums[i].id:w->guides[i].id;
            for(const char *p=expr;(p=strstr(p,"param:"))!=NULL;++p){char token[70];size_t k=0;while(p[k]&&(p[k]==':'||isdigit((unsigned char)p[k])||(k<6))&&k<sizeof token-1){token[k]=p[k];++k;}token[k]=0;ParameterRef r={0};if(!parameter_ref_parse(token,&r))continue;
                printf("%s{\"parameterId\":%u,\"fieldId\":%u,\"kind\":\"%s\",\"id\":%u,\"label\":",first?"":",",r.parameter_id,r.field_id,kind?"datum":"guide",id);first=false;char label[100];snprintf(label,sizeof label,"%s %u",kind?"基準面":"參考線",id);js_string(label);
                fputs(",\"canvasTargets\":[",stdout);bool target_first=true;
                if(!kind)json_parameter_canvas_target(w,w->guides[i].placement_id,&target_first);
                else for(size_t k=0;k<w->guide_count;++k)if(w->guides[k].source==GUIDE_DATUM&&w->guides[k].datum_id==id)json_parameter_canvas_target(w,w->guides[k].placement_id,&target_first);
                fputs("]}",stdout);
            }
        }
    }
    putchar(']');
}
