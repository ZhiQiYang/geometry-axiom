"""Exact F8 memo-only counterfactual; pure bytes, no compiler/test imports."""
import hashlib
F8 = '75a1e93811a52b69385cbdaf6a09d773ed9052ad'
PINS = {'geometry-core/references.inc': ('2f915779b14272a3cd9d2014d02d9476b05841145885e3d4b0717657e0a0378c', '093d5d7f06963a0f555c6614595791c99e250c019865006edadeacf956838a80'), 'geometry-app/native/reference_sources.inc': ('77c03a865a39f6ab0e0eff7005d04ccf91d36db92c9f218ed69630f28be9bd56', 'a6dece841da1a19d5df5c032a17d713363136c49aee09f7f641d374c26b85512')}
EDITS = {'geometry-core/references.inc': [{'id': 'remove-contact-memo-fields', 'fixed': '        /* Contact keeps only its successful three-field decode; its key is independent of the full anchor. */\n        bool contact_valid;uint32_t contact_id;\n        WoodMemberPlacementContact contact;\n        WoodMemberPlacement anchor;\n        WoodMemberDefinition definition;\n', 'withdrawn': '        WoodMemberPlacement anchor;\n        WoodMemberDefinition definition;\n'}], 'geometry-app/native/reference_sources.inc': [{'id': 'remove-contact-memo-and-shared-depend-helpers', 'fixed': 'static bool reference_member_placement_depend(ReferenceEval *ctx,uint32_t id)\n{\n    WoodDefinitionKey key;\n    if(geo_eval_depend(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&key),\n            GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;\n    return true;\n}\nstatic bool reference_member_contact_read(ReferenceEval *ctx,size_t i,uint32_t id,WoodMemberPlacementContact *out)\n{\n    if(i>=WORLD_MAX_TIMBERS||geo_eval_is_sealed(ctx->sources))\n        return wood_definition_sources_placement_contact(ctx->definition_sources,id,out);\n    if(ctx->member_reads[i].contact_valid&&ctx->member_reads[i].contact_id==id){\n        /* Use the original shared edge site for every current consumer. */\n        if(!reference_member_placement_depend(ctx,id))return false;\n        *out=ctx->member_reads[i].contact;return true;\n    }\n    if(!wood_definition_sources_placement_contact(ctx->definition_sources,id,out))return false;\n    ctx->member_reads[i].contact=*out;ctx->member_reads[i].contact_id=id;\n    ctx->member_reads[i].contact_valid=true;return true;\n}\nstatic void reference_member_footprint_invalidate(ReferenceEval *ctx,size_t i)\n', 'withdrawn': 'static void reference_member_footprint_invalidate(ReferenceEval *ctx,size_t i)\n'}, {'id': 'restore-original-anchor-hit-dependency-site', 'fixed': '        if(!reference_member_placement_depend(ctx,id))return false;\n', 'withdrawn': '        WoodDefinitionKey key;\n        /* 解碼命中仍須記錄當前 consumer 的依賴邊。 */\n        if(geo_eval_depend(ctx->sources,wood_definition_source_ref(APP_SOURCE_WOOD_DEFINITION,WOOD_DEFINITION_PLACEMENT,id,&key),\n            GEO_DEPENDENCY_DEFINITION_REQUIRED)!=GEO_SOURCE_OK)return false;\n'}, {'id': 'restore-original-contact-decode', 'fixed': '            if(!reference_member_contact_read(ctx,i,id,&anchor)){\n', 'withdrawn': '            if(!wood_definition_sources_placement_contact(ctx->definition_sources,id,&anchor)){\n'}]}
LOCAL_INIT = b'    ReferenceEval local,*ctx;bool persistent=false;\n    if(g_active_app_candidate&&w==&g_active_app_candidate->after){\n        ctx=app_candidate_evaluation_state(g_active_app_candidate->control);\n        if(!ctx||ctx->world!=w)ctx=reference_sources_begin_candidate(w);\n        if(!ctx)return false;persistent=true;\n    }else{\n        local=(ReferenceEval){0};ctx=&local;\n    }\n'
def digest(raw): return hashlib.sha256(raw).hexdigest()
def require(ok, message):
    if not ok: raise RuntimeError(message)
def withdraw_memo(path, raw):
    require(path in PINS and digest(raw)==PINS[path][0], 'exact fixed F8 memo source required: '+path)
    for edit in EDITS[path]:
        old,new=edit['fixed'].encode(),edit['withdrawn'].encode()
        require(raw.count(old)==1, 'unique memo withdrawal anchor: '+edit['id'])
        raw=raw.replace(old,new,1)
    require(digest(raw)==PINS[path][1], 'exact memo-only withdrawn source required: '+path)
    if path=='geometry-core/references.inc':require(raw.count(LOCAL_INIT)==1, 'H local-init must survive memo withdrawal')
    return raw
def restore_memo(path, raw):
    require(path in PINS and digest(raw)==PINS[path][1], 'exact withdrawn source required: '+path)
    for edit in reversed(EDITS[path]):
        old,new=edit['withdrawn'].encode(),edit['fixed'].encode()
        require(raw.count(old)==1, 'unique memo restoration anchor: '+edit['id'])
        raw=raw.replace(old,new,1)
    require(digest(raw)==PINS[path][0], 'restoration must equal original F8 bytes: '+path)
    return raw
