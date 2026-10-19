"""Executable §7 mutations. Patches are exact; the runner restores bytes in finally.

M12 and M23 belong to the ledger/UI slices, not a fabricated native kill.
Each entry names the real CR assertion and changes actual compiled source.

GEO-261: 26 entries were re-anchored from the main #253 sources onto the K/W/H
locations that now enforce the same rule (same CR case, same kind of defect).
NATIVE-CONTRACT.md section "§7 整卡突變在 GEO-261 之後的錨點" maps every one of
them (main 4b975a3d line, integration line, why it is the same rule), and the
4 live-anchor entries whose injected code moved to the GEO-261 APIs.
"""

CR='geometry-core/card_reference.inc'
GS='geometry-core/grid_systems.inc'
PAR='geometry-core/parameters.inc'
EB='geometry-web/engineering_bridge.inc'
MAIN='current_geometry.c'
# GEO-261 owners of rules that main kept in the files above.
K_GRID='geometry-core/kernel/grid_store.c'
K_PAR='geometry-core/kernel/parameters.c'
K_EXACT='geometry-core/kernel/exact.c'
K_CANDIDATE='geometry-core/kernel/candidate.c'
H_CANDIDATE='geometry-app/native/app_candidate.c'
W_GRID='geometry-templates/woodworking/native/grid_application.c'
MODEL='geometry-core/model_base.c'


def change(path, old, new):
    return {'path': path, 'old': old, 'new': new}


def mutant(identifier, case, *patches, model=False):
    return {'id': identifier, 'case': case, 'patches': list(patches), 'model': model}


MUTATIONS=[
    mutant('M01-index', 'CR04', change('geometry-web/source-inspector-bridge.inc', 'si_grid_card(s,from,g);', '((void)0);')),
    mutant('M01-cache', 'CR04', change('geometry-web/source-inspector-bridge.inc', 'if(d->card_length&&k==(d->source==GRID_SRC_REPEAT?1:2))', 'if(false)')),
    mutant('M01', 'CR01', change(CR, 'GeoGridStoreError detail;', '''if(s.card_reference.set){for(int a=0;a<2;++a){int slot=s.axis[a].source==GRID_SRC_REPEAT?1:2;
            s.axis[a].parameters[slot]=(ParameterRef){true,s.card_reference.parameter_id,s.card_reference.fields[a]};s.axis[a].card_length=false;}memset(&s.card_reference,0,sizeof s.card_reference);}
    GeoGridStoreError detail;''')),
    mutant('M02-id', 'CR25', change(CR, 'r->set=true;return true;', 'if(r->fields[0]>r->fields[1]){uint32_t x=r->fields[0];r->fields[0]=r->fields[1];r->fields[1]=x;}r->set=true;return true;')),
    mutant('M02-order', 'CR25', change(CR, 'const GridSystem *old=world_find_grid_system(w,s.id);', '''if(s.card_reference.set){const ParameterSet *p=parameter_find(w,s.card_reference.parameter_id);size_t u=0,v=0;
        if(p){for(size_t k=0;k<p->count;++k){if(p->fields[k]==s.card_reference.fields[0])u=k;if(p->fields[k]==s.card_reference.fields[1])v=k;}if(u>v){uint32_t x=s.card_reference.fields[0];s.card_reference.fields[0]=s.card_reference.fields[1];s.card_reference.fields[1]=x;}}}
    const GridSystem *old=world_find_grid_system(w,s.id);''')),
    mutant('M02-name', 'CR25', change(CR, 'const GridSystem *old=world_find_grid_system(w,s.id);', '''if(s.card_reference.set){int u=parameter_field_index(w,s.card_reference.parameter_id,s.card_reference.fields[0]),v=parameter_field_index(w,s.card_reference.parameter_id,s.card_reference.fields[1]);
        if(u>=0&&v>=0&&strcmp(geo_parameters_fields(&w->geo.parameters)[u].name,geo_parameters_fields(&w->geo.parameters)[v].name)>0){uint32_t x=s.card_reference.fields[0];s.card_reference.fields[0]=s.card_reference.fields[1];s.card_reference.fields[1]=x;}}
    const GridSystem *old=world_find_grid_system(w,s.id);''')),
    mutant('M02-value', 'CR25', change(CR, 'const GridSystem *old=world_find_grid_system(w,s.id);', '''if(s.card_reference.set){ParameterRef refs[2]={{true,s.card_reference.parameter_id,s.card_reference.fields[0]},{true,s.card_reference.parameter_id,s.card_reference.fields[1]}};char error[512];Coord u,v;
        if(parameters_evaluate_refs(w,refs,2,error,sizeof error)&&parameter_coord(w,refs[0],&u)&&parameter_coord(w,refs[1],&v)&&u>v){uint32_t x=s.card_reference.fields[0];s.card_reference.fields[0]=s.card_reference.fields[1];s.card_reference.fields[1]=x;}}
    const GridSystem *old=world_find_grid_system(w,s.id);''')),
    mutant('M03-distinct', 'CR07', change(K_GRID, 'if (r->fields[0] == r->fields[1])', 'if (false)')),
    mutant('M03-complete', 'CR11',
           change(CR, '"parameterId,uFieldId,vFieldId",""', '"parameterId,uFieldId","vFieldId"'),
           change(CR, 'bool v=parameter_u32(j,geo_json_member(j,t,"vFieldId"),&r->fields[1]);', 'bool v=true;r->fields[1]=r->fields[0];')),
    mutant('M03-same-card', 'CR07',
           change(CR, '"parameterId,uFieldId,vFieldId",""', '"parameterId,uFieldId,vFieldId","vParameterId"'),
           change(CR, 'if(geo_json_member(j,t,"uParameterId")>=0||geo_json_member(j,t,"vParameterId")>=0)', 'if(false)')),
    mutant('M04-source', 'CR11', change(K_GRID, 'if (!a->card_length || a->parameters[slot].set)', 'if (false)')),
    mutant('M04-token', 'CR31', change(GS, 'if(previous && previous->card_reference.set && !s.card_reference.set)', 'if(false)')),
    mutant('M05-dimension', 'CR08', change(K_PAR, 'if(f->type!=GEO_PARAMETER_DIMENSION)', 'if(false)')),
    mutant('M05-positive', 'CR09',
           change(K_GRID, 'if (value <= 0) {', 'if (false) {'),
           change(K_GRID, 'a->step > 0 && geo_coord_in_range(a->step)', '(a->card_length || a->step > 0) && geo_coord_in_range(a->step)'),
           change(K_GRID, 'a->source == GEO_GRID_SOURCE_REPEAT_BODY_GAP) return a->body > 0', 'a->source == GEO_GRID_SOURCE_REPEAT_BODY_GAP) return (a->card_length || a->body > 0)')),
    mutant('M05-integer', 'CR09', change(K_PAR, 'if(value.den!=1||!geo_coord_in_range(value.num))', 'if(!geo_coord_in_range(value.num))')),
    mutant('M05-range', 'CR09',
           change(K_PAR, 'if(value.den!=1||!geo_coord_in_range(value.num))', 'if(value.den!=1)'),
           change(K_GRID, 'a->step > 0 && geo_coord_in_range(a->step)', 'a->step > 0 && (a->card_length || geo_coord_in_range(a->step))')),
    mutant('M05-precision', 'CR10', change(K_EXACT, 'if(y&&x>INT64_MAX/y)', 'if(false)')),
    mutant('M06-card', 'CR26', change(PAR, 'if(r->set&&r->parameter_id==id&&parameter_reference_unhandled(w,id,field,PARAM_OWNER_GRID_CARD,s->id,0))', 'if(false)')),
    mutant('M06-extra-field', 'CR06', change(K_PAR, 'if(i<0)return geo_parameter_error(e->error,GEO_PARAMETER_MISSING_FIELD,id,field);', 'if(i<0){*out=(GeoQuantity){7,1,1};return true;}')),
    mutant('M07', 'CR12', change(EB, 'for(size_t i=0;i<candidate->wood.timber_count&&ok;++i)', 'if(!ok)g_world=*candidate;\n    for(size_t i=0;i<candidate->wood.timber_count&&ok;++i)')),
    mutant('M08', 'CR03', change(CR, 'uint32_t u=s->card_reference.fields[0];', 'GridAxisDef axis=s->axis[0];s->axis[0]=s->axis[1];s->axis[1]=axis;uint32_t u=s->card_reference.fields[0];')),
    mutant('M09', 'CR13', change(CR, 'if(!parameters_evaluate_refs(w,refs,2,error,sizeof error)||!grid_card_resolve(w,s,error,sizeof error))', 'if(false)')),
    mutant('M10', 'CR15', change(W_GRID, 'for(size_t i=0;i<geo_grid_bindings_count(c->sources);++i){WoodGridApplication derived={0};', 'for(size_t i=0;i<geo_grid_bindings_count(c->sources)&&i<1;++i){WoodGridApplication derived={0};')),
    mutant('M11-expiry', 'CR17',
           change(EB, 'if(g_history.grouping||g_preview.revision!=g_definition_revision||!app_world_candidate_current(g_preview.transaction,&g_world))', 'if(g_history.grouping)'),
           change(K_CANDIDATE, 'if(live_revision!=candidate->base_revision)return GEO_CANDIDATE_REVISION_CHANGED;', '(void)live_revision;'),
           change(H_CANDIDATE, 'return equal(live,candidate->before,opaque)?GEO_CANDIDATE_OK:GEO_CANDIDATE_STATE_CHANGED;', 'return GEO_CANDIDATE_OK;')),
    mutant('M11-revalidation', 'CR17',
           change(EB, 'if(!app_world_candidate_revalidate(g_preview.transaction,&g_world)){', 'if(false){'),
           change(H_CANDIDATE, '!app_candidate_hash_matches(candidate->after,candidate->snapshot_size,candidate->after_hash,candidate->after_bytes))return GEO_CANDIDATE_STATE_CHANGED;\n    return equal(', 'false)return GEO_CANDIDATE_STATE_CHANGED;\n    return equal('),
           change(K_CANDIDATE, 'if(!geo_candidate_digest_matches(binding->current,binding->size,binding->current_hash,binding->current_bytes))return GEO_CANDIDATE_STATE_CHANGED;', '((void)0);')),
    mutant('M11-undo', 'CR17', change(MAIN, '    if(!app_history_undo(&g_history,w,app_history_restore_world,NULL))return false;', '''    uint32_t old_ids[WORLD_MAX_GRID_SYSTEMS];GridCardReference old_cards[WORLD_MAX_GRID_SYSTEMS];size_t old_count=geo_grid_systems_count(&w->geo.grid_store);
    for(size_t k=0;k<old_count;++k){old_ids[k]=geo_grid_systems_at(&w->geo.grid_store,k)->id;old_cards[k]=geo_grid_systems_at(&w->geo.grid_store,k)->card_reference;}
    if(!app_history_undo(&g_history,w,app_history_restore_world,NULL))return false;
    for(size_t k=0;k<geo_grid_systems_count(&w->geo.grid_store);++k)for(size_t j=0;j<old_count;++j){GridSystem s=*geo_grid_systems_at(&w->geo.grid_store,k);
        if(s.id==old_ids[j]&&s.card_reference.set&&old_cards[j].set){s.card_reference.fields[1]=old_cards[j].fields[1];(void)geo_grid_systems_put(&w->geo.grid_store,&s);}}''')),
    mutant('M13-unused', 'CR19', change(GS, 'const GridSystem *s=geo_grid_systems_at(&w->geo.grid_store,i); fprintf(out,', '''const GridSystem *s=geo_grid_systems_at(&w->geo.grid_store,i);bool used=false;
        for(size_t k=0;k<geo_grid_bindings_count(&w->geo.grid_store);++k)if(geo_grid_bindings_at(&w->geo.grid_store,k)->system_id==s->id)used=true;
        if(!used)continue; fprintf(out,''')),
    mutant('M13-capability', 'CR20', change(MAIN, 'if(ok && grid_card_used(out_world) && (!grid_card_scene_required||!fs_scene_parameters))', 'if(false)')),
    mutant('M14-legacy', 'CR21', change(GS, '{WoodGridContext c=app_grid_context(w);return wood_grid_systems_rebuild(&c,error,cap);}', '''{for(size_t i=0;i<geo_grid_systems_count(&w->geo.grid_store);++i){GridSystem s=*geo_grid_systems_at(&w->geo.grid_store,i);ParameterRef u=s.axis[0].parameters[1],v=s.axis[1].parameters[1];
        if(!s.card_reference.set&&u.set&&v.set&&u.parameter_id==v.parameter_id){s.card_reference=(GridCardReference){true,u.parameter_id,{u.field_id,v.field_id}};s.axis[0].card_length=s.axis[1].card_length=true;memset(&s.axis[0].parameters[1],0,sizeof u);memset(&s.axis[1].parameters[1],0,sizeof v);(void)geo_grid_systems_put(&w->geo.grid_store,&s);}}
    WoodGridContext c=app_grid_context(w);return wood_grid_systems_rebuild(&c,error,cap);}''')),
    mutant('M14-import', 'CR22', change(PAR, 'while(parameter_find(w,candidate))++candidate;fresh[k]=candidate++;', '''while(parameter_find(w,candidate))++candidate;fresh[k]=candidate++;
        char imported_name[PARAM_NAME_MAX];if(geo_json_string(j,geo_json_member(j,c,"name"),imported_name,sizeof imported_name))for(size_t i=0;i<geo_parameters_card_count(&w->geo.parameters);++i)if(!strcmp(geo_parameters_cards(&w->geo.parameters)[i].name,imported_name)){fresh[k]=geo_parameters_cards(&w->geo.parameters)[i].id;break;}''')),
    mutant('M16', 'CR26', change(PAR, '{ return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }', '{ if(parameter_find(w,id))return false;return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }')),
    mutant('M17', 'CR13', change(CR, 'char error[512];\n                /* Read THIS ordered step;', '''char error[512];
                int ops=geo_json_member(j,0,"operations");for(int k=0;k<geo_json_size(j,ops);++k){int item=geo_json_at(j,ops,k);char name[40];if(item>t&&geo_json_string(j,geo_json_member(j,item,"op"),name,sizeof name)&&!strcmp(name,"put-parameter"))parameter_put(w,j,geo_json_member(j,item,"value"));}
                /* Read THIS ordered step;''')),
    mutant('M18-numbers', 'CR29',
           change(GS, 'if(s->card_reference.set)fprintf(out," card-reference %u %u %u",', 'if(false)fprintf(out," card-reference %u %u %u",'),
           change(GS, 'if(a->card_length)fputs("card",out);else grid_parameter_dump(out,a->step,a->parameters[1]);', 'grid_parameter_dump(out,a->step,a->parameters[1]);'),
           change(MAIN, 'if(grid_card_used(world)) fputs("requires " GRID_CARD_CAPABILITY', 'if(false) fputs("requires " GRID_CARD_CAPABILITY'), model=True),
    mutant('M18-refs', 'CR29',
           change(GS, 'if(s->card_reference.set)fprintf(out," card-reference %u %u %u",', 'if(false)fprintf(out," card-reference %u %u %u",'),
           change(GS, 'if(a->card_length)fputs("card",out);else grid_parameter_dump(out,a->step,a->parameters[1]);', 'if(a->card_length)fprintf(out,"param:%u:%u",s->card_reference.parameter_id,s->card_reference.fields[axis]);else grid_parameter_dump(out,a->step,a->parameters[1]);'),
           change(MAIN, 'if(grid_card_used(world)) fputs("requires " GRID_CARD_CAPABILITY', 'if(false) fputs("requires " GRID_CARD_CAPABILITY'), model=True),
    mutant('M18-closure', 'CR29', change(PAR, 'const ParameterSet *c=&geo_parameters_cards(&w->geo.parameters)[i];char q[600];', '''const ParameterSet *c=&geo_parameters_cards(&w->geo.parameters)[i];
        if(grid_card_used(w)){bool direct=false;for(size_t k=0;k<geo_grid_systems_count(&w->geo.grid_store);++k)
            if(geo_grid_systems_at(&w->geo.grid_store,k)->card_reference.set&&geo_grid_systems_at(&w->geo.grid_store,k)->card_reference.parameter_id==c->id)direct=true;
            if(!direct)continue;}char q[600];'''), model=True),
    mutant('M18-capability', 'CR29', change(MODEL, 'if(grid_card_used(world)){', 'if(false){'), model=True),
    mutant('M19-order', 'CR28', change(PAR, '{ return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }', '{ return parameter_declared_at(w,kind,owner,slot)==0&&parameter_field_generation(w,id,field)>0; }')),
    mutant('M19-axis-missing', 'CR13', change(CR, 'if(!parameter_declare(w,PARAM_OWNER_GRID_SYSTEM,id,a*6+slot+1))return false;', '((void)0);')),
    mutant('M19-axis-scope', 'CR13', change(PAR, '{ return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }', '{ const ParameterCandidateLedger *ledger=parameter_ledger(w);if(kind==PARAM_OWNER_GRID_SYSTEM)for(size_t i=0;ledger&&i<ledger->declaration_count;++i){const ParameterDeclaration *d=&ledger->declarations[i];if(d->kind==kind&&d->id==owner&&d->at>parameter_field_generation(w,id,field))return false;}return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }')),
    mutant('M19-partial-owner', 'CR27', change(PAR, '{ return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }', '{ const ParameterCandidateLedger *ledger=parameter_ledger(w);for(size_t i=0;ledger&&i<ledger->declaration_count;++i)if(ledger->declarations[i].kind==PARAM_OWNER_GRID_CARD)return false;return parameter_field_generation(w,id,field)>parameter_declared_at(w,kind,owner,slot); }')),
    mutant('M20', 'CR30', change(K_GRID, 'if (!a->stagger_set) return true;', 'if (!a->stagger_set || system->card_reference.set) return true;')),
    mutant('M21', 'CR22', change(PAR, 'uint32_t id=r->parameter_id;ParameterUses uses;', 'uint32_t id=r->parameter_id;ParameterUses uses;if(parameter_find(w,id))continue;')),
    mutant('M22', 'CR32',
           change(PAR, 'if(!retained)ok=parameter_retire_field(w,id,old->fields[i]);', 'if(false)ok=parameter_retire_field(w,id,old->fields[i]);'),
           change(PAR, '{return parameter_field_generation((const World *)state,id,field)!=0;}', '{return parameter_ledger((const World *)state)!=NULL;}')),
    mutant('M24', 'CR33', change('geometry-core/engineering_commands.inc', '(strcmp(name,"put-parameter")&&strcmp(name,"delete-parameter")&&strcmp(name,"import-parameters"))', '(strcmp(name,"put-parameter")&&strcmp(name,"delete-parameter")&&strcmp(name,"import-parameters")&&strcmp(name,"unbind-grid-card-reference"))')),
    mutant('P146-error-fields', 'P146_ERROR', change('tests/test_grid_card_reference.py', "errors = [v.get('message', '') for v in result['preview']['violations']]", 'errors = [json.dumps(result, ensure_ascii=False)]')),
    mutant('P146-use-field-path', 'CR26', change(PAR,
           'parameter_use(u,"grid-system %u card-reference %c field %u",s->id,a?\'v\':\'u\',field);',
           'parameter_use(u,"grid-system %u card-reference %c",s->id,a?\'v\':\'u\');')),
    mutant('P146-same-card-grid-id', 'CR07', change(CR,
           'return grid_card_fail("I74 SAME_CARD: grid-system %u parameter %u u field %u v field %u requires one parameterId, not per-axis card ids",grid_id,r->parameter_id,r->fields[0],r->fields[1]);',
           'return eng_fail("I74 SAME_CARD: expected one card");')),
    mutant('P146-complete-grid-id', 'CR11', change(CR,
           'return grid_card_fail("I74 COMPLETE_MAPPING: grid-system %u parameter %u requires parameterId and both uFieldId/vFieldId",grid_id,r->parameter_id);',
           'return eng_fail("I74 COMPLETE_MAPPING: expected both fields");')),
    mutant('P146-mode-grid-id', 'CR11', change(CR,
           'return grid_card_fail("I74 MODE_SCOPE: grid-system %u %c parameter %u field %u requires repeat or repeat-panel",s->id,a?\'v\':\'u\',s->card_reference.parameter_id,s->card_reference.fields[a]);',
           'return eng_fail("I74 MODE_SCOPE: both axes must use repeat or repeat-panel");')),
    mutant('P154-format-code', 'P154_GRID', change(CR,
           'D29 GRID_DEFINITION: grid-system %u requires id, name, mainAlong, u and v',
           'I74 COMPLETE_MAPPING: grid-system %u requires id, name, mainAlong, u and v')),
    mutant('P154-format-id', 'P154_GRID', change(CR,
           'no unknown keys",s.id);', 'no unknown keys",0u);')),
    mutant('P154-identity-boundary', 'P154_IDENTITY', change('tests/test_grid_card_reference.py',
           "re.search(r'\\b' + re.escape(part) + r'\\b', message)", 'part in message')),
    mutant('P154-identity-one-message', 'P154_IDENTITY', change('tests/test_grid_card_reference.py',
           'matching = [message for message in errors if reason in message]',
           "matching = ['\\n'.join(errors)] if any(reason in message for message in errors) else []")),
]
