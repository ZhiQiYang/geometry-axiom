/* D34/I42/R35. Definitions own stable native members; geometry remains R6. */
static bool g_assembly_replay;
static bool asm_instance_load(World *,GeoJson *,int);
static AsmInstance *assembly_instance(World *w,uint32_t id)
{for(size_t i=0;i<w->assembly.instance_count;++i)if(w->assembly.instances[i].id==id)return &w->assembly.instances[i];return NULL;}
static bool assembly_owned(const World *w,uint32_t id)
{if(g_assembly_replay)return false;for(size_t i=0;i<w->assembly.owner_count;++i)if(w->assembly.owners[i].timber==id)return true;return false;}
static bool asm_hash_token(GeoJson *j,int t,char hash[65])
{if(!geo_json_string(j,t,hash,65)||strlen(hash)!=64)return false;for(int i=0;i<64;++i)if(!((hash[i]>='0'&&hash[i]<='9')||(hash[i]>='a'&&hash[i]<='f')))return false;return true;}
static bool asm_instance_parse(World *w,GeoJson *j,int t,AsmInstance *a)
{
    memset(a,0,sizeof *a);int r=geo_json_member(j,t,"rule"),m=geo_json_member(j,t,"members");
    if(!geo_json_keys(j,t,"id,name,bindingId,rule,surfaceId,members","")||!eng_u32(j,geo_json_member(j,t,"id"),&a->id,true)||!asm_name(j,geo_json_member(j,t,"name"),a->name)||
       !eng_u32(j,geo_json_member(j,t,"bindingId"),&a->binding_id,true)||
       !geo_json_keys(j,r,"id,version,fingerprint","")||!eng_u32(j,geo_json_member(j,r,"id"),&a->rule_id,true)||!eng_u32(j,geo_json_member(j,r,"version"),&a->rule_version,true)||!asm_hash_token(j,geo_json_member(j,r,"fingerprint"),a->rule_hash)||
       !geo_json_is_array(j,m)||geo_json_size(j,m)!=3)return asm_error("D34/UNSUPPORTED: instance needs exactly three typed members and fixed sources");
    if(!eng_u32(j,geo_json_member(j,t,"surfaceId"),&a->surface_id,true))return asm_error("I42: select a valid instance surface");
    const AsmRuleVersion *rule=assembly_rule(w,a->rule_id,a->rule_version);AsmBinding *binding=assembly_binding(w,a->binding_id);
    if(!rule||strcmp(rule->fingerprint,a->rule_hash)||!binding||binding->rule_id!=a->rule_id||binding->rule_version!=a->rule_version)return asm_error("I42: missing binding or mismatched fixed rule fingerprint/version");
    GeoJson q;if(!app_json_parse(&q,rule->content)){geo_json_free(&q);return false;}int members=geo_json_member(&q,0,"members"),joints=geo_json_member(&q,0,"joints");bool ok=geo_json_size(&q,members)==3&&geo_json_size(&q,joints)==2;int sec=-1,primary=0;
    for(int i=0;i<3&&ok;++i){int v=geo_json_at(j,m,i),e=geo_json_member(j,v,"ends");char role[16],dir[8],depth[8];
        ok=geo_json_keys(j,v,"memberId,role,guideId,dir,depthSide,ends","")&&eng_u32(j,geo_json_member(j,v,"memberId"),&a->member[i],true)&&
           geo_json_string(j,geo_json_member(j,v,"role"),role,sizeof role)&&geo_json_string(j,geo_json_member(j,v,"dir"),dir,sizeof dir)&&geo_json_string(j,geo_json_member(j,v,"depthSide"),depth,sizeof depth)&&!strcmp(depth,"+n")&&geo_json_keys(j,e,"start,finish","");
        if(!ok)break;
        if(!eng_u32(j,geo_json_member(j,v,"guideId"),&a->guide[i],true)){geo_json_free(&q);return asm_error("I42: member %u needs a valid selected guide",a->member[i]);}
        a->secondary[i]=!strcmp(role,"secondary");if(a->secondary[i]){if(sec>=0)ok=false;sec=i;}else if(!strcmp(role,"primary"))++primary;else ok=false;
        if(strcmp(dir,a->secondary[i]?"+u":"+v"))ok=false;
        for(int k=0;k<i;++k)if(a->member[k]==a->member[i]||a->guide[k]==a->guide[i])ok=false;
        bool found=false;for(int k=0;k<3;++k){uint32_t id;if(eng_u32(&q,geo_json_member(&q,geo_json_at(&q,members,k),"id"),&id,true)&&id==a->member[i])found=true;}if(!found)ok=false;
        for(int k=0;k<2&&ok;++k){int end=geo_json_member(j,e,k?"finish":"start");char kind[16];ok=geo_json_string(j,geo_json_member(j,end,"kind"),kind,sizeof kind)&&!strcmp(kind,a->secondary[i]?"member":"timber")&&geo_json_keys(j,end,a->secondary[i]?"kind,memberId":"kind,id","");
            if(ok&&!eng_u32(j,geo_json_member(j,end,a->secondary[i]?"memberId":"id"),&a->ends[i][k],true)){geo_json_free(&q);return asm_error("I42: member %u needs a valid selected %s support",a->member[i],k?"finish":"start");}}
    }
    if(sec<0||primary!=2)ok=false;
    for(int k=0;k<2&&ok;++k){int target=-1;for(int i=0;i<3;++i)if(a->member[i]==a->ends[sec][k]&&!a->secondary[i])target=i;if(target<0||a->ends[sec][0]==a->ends[sec][1]){ok=false;break;}
        bool found=false;for(int h=0;h<2;++h){int joint=geo_json_at(&q,joints,h);uint32_t term,to;char kind[24],end[16],side[8],dir[8];
            if(geo_json_string(&q,geo_json_member(&q,joint,"kind"),kind,sizeof kind)&&!strcmp(kind,"end-to-side")&&eng_u32(&q,geo_json_member(&q,joint,"terminatedMember"),&term,true)&&term==a->member[sec]&&eng_u32(&q,geo_json_member(&q,joint,"targetMember"),&to,true)&&to==a->member[target]&&geo_json_string(&q,geo_json_member(&q,joint,"end"),end,sizeof end)&&!strcmp(end,k?"finish":"start")&&geo_json_string(&q,geo_json_member(&q,joint,"side"),side,sizeof side)&&!strcmp(side,k?"-u":"+u")&&geo_json_string(&q,geo_json_member(&q,joint,"dir"),dir,sizeof dir)&&!strcmp(dir,"u"))found=true;
        }if(!found)ok=false;
    }
    geo_json_free(&q);return ok||asm_error("D34/UNSUPPORTED: only two +v primary and one +u secondary with inward end-to-side joints");
}
static bool asm_instance_content(AsmInstance *a,GeoJson *j,int source)
{
    char value[ASM_RECORD_MAX],text[ASM_RECORD_MAX];if(!geo_json_canonical(j,source,value,sizeof value))return false;
    int n=snprintf(text,sizeof text,"{\"source\":%s,\"mapping\":[{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u},{\"memberId\":%u,\"timberId\":%u}]}",value,a->member[0],a->timber[0],a->member[1],a->timber[1],a->member[2],a->timber[2]);
    if(n<0||(size_t)n>=sizeof text)return asm_error("CAPACITY: instance exceeds 8191 bytes");GeoJson q;bool ok=app_json_parse(&q,text)&&geo_json_canonical(&q,0,a->content,sizeof a->content);geo_json_free(&q);return ok;
}
static bool assembly_generation_integrity(const World *w)
{
    if(w->assembly.owner_count!=w->assembly.instance_count*3)return asm_error("I42: orphan owned records or missing instance mapping");
    if(w->assembly.instance_count&&!w->assembly.generation_required)return asm_error("I42: missing required generation capability");
    for(size_t i=0;i<w->assembly.owner_count;++i){const AsmOwner *o=&w->assembly.owners[i];bool found=false;
        for(size_t k=0;k<w->assembly.instance_count;++k)for(int m=0;m<3;++m){const AsmInstance *a=&w->assembly.instances[k];if(o->instance==a->id&&o->member==a->member[m]&&o->timber==a->timber[m])found=true;}
        if(!found||reference_timber_index(w,o->timber)<0)return asm_error("I42: invalid owned mapping");
        for(size_t k=0;k<i;++k)if(w->assembly.owners[k].timber==o->timber||(w->assembly.owners[k].instance==o->instance&&w->assembly.owners[k].member==o->member))return asm_error("I42: duplicate owner identity");
    }return true;
}
static int asm_member_index(const AsmInstance *a,uint32_t id)
{for(int i=0;i<3;++i)if(a->member[i]==id)return i;return -1;}
static bool asm_member_definition(World *w,const AsmInstance *a,int m,Coord *width,Coord *depth,TimberAnchor *anchor)
{
    AsmBinding *binding=assembly_binding(w,a->binding_id);const AsmRuleVersion *rule=assembly_rule(w,a->rule_id,a->rule_version);
    if(!binding||!binding->complete||binding->rule_id!=a->rule_id||binding->rule_version!=a->rule_version||!rule||strcmp(a->rule_hash,rule->fingerprint))return asm_error("I42: incomplete or changed instance binding/rule");
    GeoJson q,b;bool ok=app_json_parse(&q,rule->content);if(!ok){geo_json_free(&q);return false;}ok=app_json_parse(&b,binding->content);if(!ok){geo_json_free(&q);geo_json_free(&b);return false;}
    uint32_t slot=0;int members=geo_json_member(&q,0,"members"),slots=geo_json_member(&b,0,"slots");
    for(int i=0;i<geo_json_size(&q,members);++i){uint32_t id;int t=geo_json_at(&q,members,i);if(eng_u32(&q,geo_json_member(&q,t,"id"),&id,true)&&id==a->member[m])eng_u32(&q,geo_json_member(&q,t,"slotId"),&slot,true);}
    int selected=-1;for(int i=0;i<geo_json_size(&b,slots);++i){uint32_t id;int t=geo_json_at(&b,slots,i);if(eng_u32(&b,geo_json_member(&b,t,"slotId"),&id,true)&&id==slot)selected=t;}
    char face[8],orient[8];ok=selected>=0&&geo_json_string(&b,geo_json_member(&b,selected,"contactFace"),face,sizeof face)&&!strcmp(face,"A")&&geo_json_string(&b,geo_json_member(&b,selected,"orientation"),orient,sizeof orient)&&!strcmp(orient,"A");
    for(int axis=0;axis<2&&ok;++axis){EngDimensionSource src;EngTarget target={1,0,0,axis};char path[192];ok=eng_source_parse(&b,geo_json_member(&b,selected,axis?"B":"A"),&src,false)&&eng_resolve(w,&src,&target,UINT32_MAX,0,axis?depth:width,path,sizeof path);}
    geo_json_free(&q);geo_json_free(&b);if(!ok)return asm_error("D34/UNSUPPORTED: generation needs complete A contact, A transverse width and B depth sources");
    const PlacementSurface *p=world_find_placement(w,a->surface_id);const GuideLine *g=NULL;for(size_t i=0;i<geo_guides_count(&w->guide_lines);++i)if(geo_guides_values(&w->guide_lines)[i].id==a->guide[m])g=&geo_guides_values(&w->guide_lines)[i];
    if(!p||!g||g->placement_id!=p->id||g->direction!=(a->secondary[m]?GUIDE_ALONG_U:GUIDE_ALONG_V))return asm_error("I42: member needs a matching same-surface guide");
    memset(anchor,0,sizeof *anchor);anchor->placement_id=p->id;anchor->ref_hole=-1;anchor->anchor_kind=ANCHOR_AT_LINE;anchor->span_mode=SPAN_AUTO;anchor->ref_guide=g->id;anchor->has_between=true;anchor->length_direction=a->secondary[m]?SURFACE_DIRECTION_POS_U:SURFACE_DIRECTION_POS_V;anchor->depth_side=SURFACE_DEPTH_POSITIVE_NORMAL;
    for(int k=0;k<2;++k){uint32_t id=a->ends[m][k];if(a->secondary[m]){int target=asm_member_index(a,id);if(target<0||a->secondary[target])return asm_error("I42: invalid secondary member dependency");id=a->timber[target];}int ti=reference_timber_index(w,id);
        if(ti<0||id==a->timber[m]||(!a->secondary[m]&&w->timbers[ti].role!=TIMBER_ROLE_BOUNDARY)||w->anchors[ti].placement_id!=p->id)return asm_error("I42/V_CUT_PRIORITY: primary requires existing same-face boundary supports; secondary requires its two primary members");
        anchor->between[k]=(ReferenceFace){1,-1,0,id};
    }return true;
}
static bool assembly_generation_prepare(World *w)
{
    if(!g_parsing_scene_file&&!assembly_generation_integrity(w))return false;
    for(size_t i=0;i<w->assembly.instance_count;++i){AsmInstance *a=&w->assembly.instances[i];
        for(int phase=0;phase<2;++phase)for(int m=0;m<3;++m)if(a->secondary[m]==(phase!=0)){
            Coord width,depth;TimberAnchor anchor;if(!asm_member_definition(w,a,m,&width,&depth,&anchor))return false;int at=reference_timber_index(w,a->timber[m]);if(at<0)return asm_error("I42: missing owned timber");
            Timber value;if(!timber_construct(a->timber[m],0,width,depth,true,a->secondary[m]?TIMBER_ROLE_SECONDARY:TIMBER_ROLE_PRIMARY,0,&value))return asm_error("D1: invalid generated section");
            anchor.order=w->anchors[at].order;if(!anchor.order)anchor.order=++w->next_order;
            w->timbers[at]=value;w->timbers[at].placed=true;w->anchors[at]=anchor;
        }
    }return true;
}
static bool assembly_generation_check(const World *w)
{
    for(size_t i=0;i<w->assembly.instance_count;++i){const AsmInstance *a=&w->assembly.instances[i];const PlacementSurface *p=world_find_placement(w,a->surface_id);if(!p)return asm_error("I42: missing instance surface");
        for(int m=0;m<3;++m){int ti=reference_timber_index(w,a->timber[m]);if(ti<0||!w->timbers[ti].placed)return asm_error("I42: unplaced owned member");
            if(!a->secondary[m])continue;int left=reference_timber_index(w,a->timber[asm_member_index(a,a->ends[m][0])]),right=reference_timber_index(w,a->timber[asm_member_index(a,a->ends[m][1])]);SurfaceRegion2 f,l,r;
            if(left<0||right<0||!timber_a0_footprint_uv(p,&w->timbers[ti],&w->anchors[ti],&f)||!timber_a0_footprint_uv(p,&w->timbers[left],&w->anchors[left],&l)||!timber_a0_footprint_uv(p,&w->timbers[right],&w->anchors[right],&r)||f.min_u!=l.max_u||f.max_u!=r.min_u||f.min_v<l.min_v||f.max_v>l.max_v||f.min_v<r.min_v||f.max_v>r.max_v)return asm_error("I42: secondary endpoints do not contact the declared inward primary sides");
        }
    }return true;
}
static bool asm_generation_operation(World *w,GeoJson *j,int t)
{
    char op[24];if(!geo_json_string(j,geo_json_member(j,t,"op"),op,sizeof op))return false;bool create=!strcmp(op,"create-instance"),edit=!strcmp(op,"edit-instance"),del=!strcmp(op,"delete-instance");if(!create&&!edit&&!del)return assembly_operation(w,j,t);
    uint32_t id;AsmInstance value,*old=NULL;char expected[65],actual[65];int source=geo_json_member(j,t,"value");
    if(create){if(!geo_json_keys(j,t,"op,expectedBindingFingerprint,value","")||!asm_instance_parse(w,j,source,&value))return false;id=value.id;if(assembly_instance(w,id))return asm_error("I42: instance already exists");}
    else {if(!geo_json_keys(j,t,edit?"op,id,expectedFingerprint,expectedBindingFingerprint,value":"op,id,expectedFingerprint","")||!eng_u32(j,geo_json_member(j,t,"id"),&id,true)||!asm_hash_token(j,geo_json_member(j,t,"expectedFingerprint"),expected))return asm_error("I42: invalid guarded instance edit/delete");old=assembly_instance(w,id);if(!old)return asm_error("I42: instance does not exist");geo_sha256(old->content,strlen(old->content),actual);if(strcmp(expected,actual))return asm_error("STALE: instance source changed");}
    if(del){
        AsmInstance copy=*old;size_t at=(size_t)(old-w->assembly.instances);memmove(old,old+1,(w->assembly.instance_count-at-1)*sizeof *old);memset(&w->assembly.instances[--w->assembly.instance_count],0,sizeof *old);
        for(int m=0;m<3;++m){int ti=reference_timber_index(w,copy.timber[m]);if(ti<0)return false;memmove(&w->timbers[ti],&w->timbers[ti+1],(w->timber_count-ti-1)*sizeof(Timber));memmove(&w->anchors[ti],&w->anchors[ti+1],(w->timber_count-ti-1)*sizeof(TimberAnchor));memset(&w->timbers[--w->timber_count],0,sizeof(Timber));memset(&w->anchors[w->timber_count],0,sizeof(TimberAnchor));}
        for(size_t i=w->assembly.owner_count;i>0;--i)if(w->assembly.owners[i-1].instance==id){memmove(&w->assembly.owners[i-1],&w->assembly.owners[i],(w->assembly.owner_count-i)*sizeof(AsmOwner));memset(&w->assembly.owners[--w->assembly.owner_count],0,sizeof(AsmOwner));}w->assembly.generation_required=w->assembly.instance_count>0;return true;
    }
    if(edit){if(!asm_instance_parse(w,j,source,&value))return false;if(value.id!=id)return asm_error("I42: edited instance identity mismatch");}
    AsmBinding *binding=assembly_binding(w,value.binding_id);if(!binding||!asm_hash_token(j,geo_json_member(j,t,"expectedBindingFingerprint"),expected))return asm_error("I42: expected binding fingerprint required");geo_sha256(binding->content,strlen(binding->content),actual);if(strcmp(expected,actual))return asm_error("STALE: instance binding source changed");
    if(edit){for(int m=0;m<3;++m){int at=asm_member_index(old,value.member[m]);if(at<0||old->secondary[at]!=value.secondary[m])return asm_error("D34/UNSUPPORTED: member membership/roles cannot change");value.timber[m]=old->timber[at];}}
    else {
        if(w->assembly.instance_count==ASM_INSTANCE_MAX||w->timber_count+3>WORLD_MAX_TIMBERS)return asm_error("CAPACITY: at most 16 instances within native timber capacity");
        for(int phase=0;phase<2;++phase)for(int m=0;m<3;++m)if(value.secondary[m]==(phase!=0)){uint32_t tid=1;while(reference_timber_index(w,tid)>=0){if(tid==UINT32_MAX)return asm_error("CAPACITY: no free timber identity");++tid;}value.timber[m]=tid;Timber *timber=&w->timbers[w->timber_count];memset(timber,0,sizeof *timber);timber->id=tid;memset(&w->anchors[w->timber_count],0,sizeof(TimberAnchor));w->anchors[w->timber_count++].order=++w->next_order;w->assembly.owners[w->assembly.owner_count++]=(AsmOwner){tid,value.id,value.member[m]};}
        old=&w->assembly.instances[w->assembly.instance_count++];
    }
    if(!asm_instance_content(&value,j,source))return false;*old=value;w->assembly.generation_required=true;return true;
}
static bool asm_instance_load(World *w,GeoJson *j,int t)
{
    if(!w->assembly.generation_required||!geo_json_keys(j,t,"source,mapping","")||w->assembly.instance_count==ASM_INSTANCE_MAX)return asm_error("I42: instance needs generation capability and source/mapping");AsmInstance a;int source=geo_json_member(j,t,"source"),map=geo_json_member(j,t,"mapping");if(!asm_instance_parse(w,j,source,&a)||assembly_instance(w,a.id)||!geo_json_is_array(j,map)||geo_json_size(j,map)!=3)return asm_error("I42: invalid or duplicate instance mapping");
    for(int i=0;i<3;++i){int v=geo_json_at(j,map,i);uint32_t member,tid;if(!geo_json_keys(j,v,"memberId,timberId","")||!eng_u32(j,geo_json_member(j,v,"memberId"),&member,true)||!eng_u32(j,geo_json_member(j,v,"timberId"),&tid,true))return false;int m=asm_member_index(&a,member);if(m<0||a.timber[m])return asm_error("I42: duplicate/missing mapped member");a.timber[m]=tid;}
    if(!asm_instance_content(&a,j,source))return false;
    /* Persisted owned definitions must equal sources before reconstruction, not be silently repaired. */
    for(int m=0;m<3;++m){Coord width,depth;TimberAnchor expected;if(!asm_member_definition(w,&a,m,&width,&depth,&expected))return false;int ti=reference_timber_index(w,a.timber[m]);if(ti<0)return asm_error("I42: saved owned timber missing");TimberAnchor actual=w->anchors[ti];actual.uv=(SurfacePoint2){0};actual.order=0;
        if(w->timbers[ti].size_a!=width||w->timbers[ti].size_b!=depth||w->timbers[ti].role!=(a.secondary[m]?TIMBER_ROLE_SECONDARY:TIMBER_ROLE_PRIMARY)||!w->timbers[ti].placed||memcmp(&actual,&expected,sizeof actual))return asm_error("I42: saved owned definitions differ from instance sources");
    }
    w->assembly.instances[w->assembly.instance_count++]=a;return true;
}
static void assembly_owned_prefix(const World *w,uint32_t id,const char *kind,FILE *out)
{
    (void)kind;for(size_t i=0;i<w->assembly.owner_count;++i)if(w->assembly.owners[i].timber==id){const AsmOwner *o=&w->assembly.owners[i];fprintf(out,"owned %u %u ",o->instance,o->member);return;}
}
static bool apply_assembly_owned_line(const char *path,int line_no,char **t,int count,World *w)
{
    uint32_t inst,member,id;if(!g_parsing_scene_file||!w->assembly.generation_required||count<6||!parse_u32(t[1],&inst)||!inst||!parse_u32(t[2],&member)||!member||!parse_u32(t[4],&id)||!id){scene_error(path,line_no,"I42: owned records require atomic generation scene and positive identities");return false;}
    bool timber=!strcmp(t[3],"timber"),place=!strcmp(t[3],"place");if(!timber&&!place)return false;
    if(timber){if(w->assembly.owner_count==ASM_INSTANCE_MAX*3||reference_timber_index(w,id)>=0)return false;w->assembly.owners[w->assembly.owner_count++]=(AsmOwner){id,inst,member};}
    else {bool found=false;for(size_t i=0;i<w->assembly.owner_count;++i){AsmOwner *o=&w->assembly.owners[i];if(o->timber==id&&o->instance==inst&&o->member==member)found=true;}if(!found)return false;}
    g_assembly_replay=true;bool ok=timber?apply_timber_line(path,line_no,t+3,count-3,w):apply_reference_place(path,line_no,t+3,count-3,w);g_assembly_replay=false;if(!ok)scene_error(path,line_no,g_revalidate_error[0]?g_revalidate_error:"I42: invalid owned record");return ok;
}
