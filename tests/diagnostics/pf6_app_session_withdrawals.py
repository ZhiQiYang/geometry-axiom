"""Named PF-6 App owner withdrawals in isolated source copies; no ledger edits."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'geometry-web/panel-fill-builder-session.js'
TEST = 'tests/test_panel_fill_builder_session.js'
DEPENDENCY = 'geometry-web/panel-fill-adapter.js'
REAL_HOST_INPUTS = ['tests/fixtures/reference_workspace_vm.cjs',
                    'geometry-web/app.js', 'geometry-web/reference-workspace.js']
WITHDRAWALS = [
    ('PF6_APP_ALLOW_INCOMPLETE_CAPABILITIES', 'PF6_APP_EMBEDDED_CAPABILITIES',
     'PF6_APP_EMBEDDED_CAPABILITIES', [
         ('same(c.supportedActions,A.ACTIONS)',
          "['read','read-layout','read-support','create-from-fill-grid'].every(action=>c.supportedActions.includes(action))")]),
    ('PF6_APP_KEEP_OLD_SELECTION_TOKEN', 'PF6_APP_SELECTION_REVOKES_TOKEN_BEFORE_CANCEL_REPLY',
     'PF6_APP_KEEP_OLD_SELECTION_TOKEN', [
         ('revoke(){if(this.lease)this.host.clearTimberPreviewToken(this.lease);this.candidate=null;}',
          'revoke(){this.candidate=null;}')]),
    ('PF6_APP_TOKEN_MEANS_VALID', 'PF6_APP_INVALID_AND_INCOMPLETE_NEVER_CONFIRM',
     'PF6_APP_TOKEN_MEANS_VALID invalid', [
         ("||p.valid!==true||p.phase!=='SELECTED'", "||p.phase!=='SELECTED'"),
         ('else if(p.valid&&p.appView.completeForScope&&p.appView.uiContract.completeForScope',
          'else if(p.appView.completeForScope&&p.appView.uiContract.completeForScope')]),
    ('PF6_APP_ACCEPT_ZERO_TOKEN', 'PF6_APP_TOKEN_ZERO_IS_REJECTED',
     'PF6_APP_TOKEN_ZERO_IS_REJECTED', [
         (r"const token=v=>uint(v)&&v>0?String(v):typeof v==='string'&&/^[1-9]\d{0,9}$/.test(v)&&uint(Number(v))?v:null;",
          r"const token=v=>uint(v)?String(v):typeof v==='string'&&/^(0|[1-9]\d{0,9})$/.test(v)&&uint(Number(v))?v:null;")]),
    ('PF6_APP_RELEASE_NOOP_LEASE', 'PF6_APP_SUGGEST_AND_NOOP_HOLD_NULL_LEASE',
     'PF6_APP_NOOP_SHARED_LEASE', [
         ("if(p.phase==='NO_OP'){this.phase='suggested';", "if(p.phase==='NO_OP'){this.release();this.phase='suggested';")]),
    ('PF6_APP_ALLOW_INVALID_ANALYSIS_PREFIX', 'PF6_APP_INVALID_ANALYSIS_PREFIX_IS_NOT_SELECTABLE',
     'PF6_APP_INVALID_ANALYSIS_PREFIX_IS_NOT_SELECTABLE', [
         ('check(r?.valid===true&&r.appView?.completeForScope===true&&Array.isArray(selected)',
          'check(r?.appView?.completeForScope===true&&Array.isArray(selected)')]),
    ('PF6_APP_OMIT_TEMPORARY_ID_FLAG', 'PF6_APP_PREVIEW_IDS_ARE_TEMPORARY_AND_MAP_IS_RECEIPT_ONLY',
     'PF6_APP_TEMPORARY_ID_GUARD missing-flag', [
         ("check(p.candidateIdsAreTemporary===true,'候選缺少暫號聲明，不能當作正式定義。'); // PF6_APP_TEMPORARY_ID_FLAG",
          '/* PF6_APP_TEMPORARY_ID_FLAG withdrawn */')]),
    ('PF6_APP_ALLOW_PREVIEW_ID_MAP', 'PF6_APP_PREVIEW_IDS_ARE_TEMPORARY_AND_MAP_IS_RECEIPT_ONLY',
     'PF6_APP_TEMPORARY_ID_GUARD early-map', [
         ("check(p.idMap===null,'正式識別映射只能來自確認回執。'); // PF6_APP_NO_PREVIEW_ID_MAP",
          '/* PF6_APP_NO_PREVIEW_ID_MAP withdrawn */')]),
    ('PF6_APP_ALLOW_FORMAL_ID_IN_PREVIEW', 'PF6_APP_PREVIEW_IDS_ARE_TEMPORARY_AND_MAP_IS_RECEIPT_ONLY',
     'PF6_APP_TEMPORARY_ID_GUARD formal-id', [
         ("row=>keys(row,['kind','tempKey','candidateId'])&&['timber','placement','grid'].includes(row.kind)",
          "row=>row&&['timber','placement','grid'].includes(row.kind)")]),
    ('PF6_APP_ALLOW_DUPLICATE_TEMP_KEY', 'PF6_APP_PREVIEW_IDS_ARE_TEMPORARY_AND_MAP_IS_RECEIPT_ONLY',
     'PF6_APP_TEMPORARY_ID_GUARD duplicate-temp-key', [
         ("check(new Set(p.createdDefinitions.map(row=>row.tempKey)).size===p.createdDefinitions.length,'候選暫時鍵重複。'); // PF6_APP_UNIQUE_TEMP_KEYS",
          '/* PF6_APP_UNIQUE_TEMP_KEYS withdrawn */')]),
    ('PF6_APP_REJECT_SHARED_CANDIDATE_ID', 'PF6_APP_DEDUPLICATED_SOURCES_SHARE_A_CANDIDATE_ID',
     'PF6_APP_DEDUPLICATED_SOURCES_SHARE_A_CANDIDATE_ID', [
         ("check(new Set(p.createdDefinitions.map(row=>row.tempKey)).size===p.createdDefinitions.length,'候選暫時鍵重複。'); // PF6_APP_UNIQUE_TEMP_KEYS",
          "check(new Set(p.createdDefinitions.map(row=>row.kind+':'+row.candidateId)).size===p.createdDefinitions.length,'候選暫號重複。');")]),
    ('PF6_APP_DROP_INVALID_CLEANUP_TOKEN', 'PF6_APP_INVALID_SELECTED_RETAINS_POSITIVE_CLEANUP_TOKEN',
     'PF6_APP_INVALID_SELECTED_CLEANUP_TOKEN', [
         ('const p=reply.preview;this.cleanupToken=token(p?.token);',
          'const p=reply.preview;this.cleanupToken=p?.valid?token(p.token):null;')]),
    ('PF6_APP_UINT64_REQUEST_NUMBER_ROUNDTRIP', 'PF6_APP_UINT64_REVISION_GENERATION_FLOW',
     'PF6_APP_UINT64_REQUEST_EXACT', [
         ('expectedRevision:this.revision,setKey:r.setKey,generation:r.generation,selected:this.selected.slice()',
          'expectedRevision:String(Number(this.revision)),setKey:r.setKey,generation:String(Number(r.generation)),selected:this.selected.slice()')]),
    ('PF6_APP_DROP_CONFIRMED_TEMP_KEYS', 'PF6_APP_FORMAL_ID_MAP_COMES_ONLY_FROM_CONFIRM_RECEIPT',
     'PF6_APP_CONFIRMED_TEMP_KEYS_RETAINED', [
         ('this.committedDefinitions=r?.ok?clone(this.candidate?.createdDefinitions||[]):[];',
          'this.committedDefinitions=[];')]),
    ('PF6_APP_RECEIPT_CURRENT_SESSION', 'PF6_APP_UNKNOWN_CONFIRM_ORIGINAL_RECEIPT_ONLY',
     'PF6_APP_RECEIPT_CURRENT_SESSION', [
         ("if(this.phase!=='unknown'||command!==this.pendingCommand||originSession!==this.owner.session)return false; // PF6_APP_RECEIPT_CURRENT_SESSION",
          "if(this.phase!=='unknown'||command!==this.pendingCommand)return false; // PF6_APP_RECEIPT_CURRENT_SESSION")]),
    ('PF6_APP_CANVAS_POS_EXPIRES', 'PF6_APP_SOURCE_CHANGE_INVALIDATES_BUT_CANVAS_POS_PRESERVES',
     'PF6_APP_CANVAS_POS_EXPIRES', [
         ('if(!this.lease||this.host.refreshTimberPreviewPresentation?.(this.lease)!==true)return false; // PF6_APP_CANVAS_POS_EXPIRES',
          'return false; // PF6_APP_CANVAS_POS_EXPIRES')]),
    ('PF6_APP_OMIT_WORLD_GEOMETRY_GUARD', 'PF6_APP_MISSING_WORLD_GEOMETRY_IS_NOT_COMPLETE',
     'PF6_APP_COMPLETE_GEOMETRY origin', [
         ("check(view.timbers.every(row=>timberState(row.before,true)&&timberState(row.after,row.before!==null)&&!(row.before===null&&row.after===null)),'完整投影缺少角材尺寸、中線或世界幾何。'); // PF6_APP_COMPLETE_GEOMETRY",
          '/* PF6_APP_COMPLETE_GEOMETRY withdrawn */')]),
    ('PF6_APP_CANCEL_UNSENT_AS_UNKNOWN', 'PF6_APP_REAL_UNSENT_CANCEL_WAITS_FOR_CONNECTION_NOT_A_PHANTOM_RECEIPT',
     'PF6_APP_CANCEL_UNSENT_IS_NOT_UNKNOWN', [
         ("if(r?.transport&&r.sent===false){this.phase='cleanup-required';this.pendingCommand=null;this.reason='取消尚未送出，沒有待查回執；連線恢復後請取消這一個候選。';throw Object.assign(fail('PF6_NOT_SENT',this.reason),{transport:true,sent:false});} // PF6_APP_CANCEL_UNSENT_IS_NOT_UNKNOWN",
          '/* PF6_APP_CANCEL_UNSENT_IS_NOT_UNKNOWN withdrawn */')]),
    ('PF6_APP_CONFIRM_UNSENT_AS_UNKNOWN', 'PF6_APP_REAL_UNSENT_CONFIRM_CAN_RETRY_OR_CANCEL_WITHOUT_RESENDING_A_MUTATION',
     'PF6_APP_CONFIRM_UNSENT_IS_NOT_UNKNOWN', [
         ("if(r?.transport&&r.sent===false){this.phase='confirm-not-sent';this.pendingCommand=null;this.reason='確認尚未送出，沒有待查回執；連線恢復並核對來源後，可再按確認或取消。';this.emit();return r;} // PF6_APP_CONFIRM_UNSENT_IS_NOT_UNKNOWN",
          '/* PF6_APP_CONFIRM_UNSENT_IS_NOT_UNKNOWN withdrawn */')]),
]


def input_closure():
    """Copy the real App/host fixture's literal CJS dependencies into isolation."""
    pending = [SOURCE, TEST, DEPENDENCY, *REAL_HOST_INPUTS]
    inputs = {}
    literal_require = re.compile(r'''\brequire(?:\.resolve)?\(\s*['"](\.[^'"]+)['"]\s*\)''')
    while pending:
        rel = pending.pop()
        if rel in inputs:
            continue
        path = ROOT / rel
        inputs[rel] = path.read_bytes()
        if path.suffix not in ('.js', '.cjs'):
            continue
        for requested in literal_require.findall(inputs[rel].decode('utf-8')):
            candidate = path.parent / requested
            options = [candidate, candidate.with_suffix('.js'), candidate.with_suffix('.cjs'),
                       candidate.with_suffix('.json'), candidate / 'index.js']
            dependency = next((p.resolve() for p in options if p.is_file()), None)
            if dependency is None or not dependency.is_relative_to(ROOT):
                raise AssertionError('unresolved local CJS input: ' + rel + ' -> ' + requested)
            pending.append(dependency.relative_to(ROOT).as_posix())
    return dict(sorted(inputs.items()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('--out must be outside the checkout')
    out.mkdir(parents=True, exist_ok=True)
    inputs = input_closure()
    original = inputs[SOURCE]
    environment = dict(os.environ)
    environment.pop('GEOMETRY_TEST_REFERENCE_WORKSPACE', None)
    records = []
    with tempfile.TemporaryDirectory(prefix='pf6-app-withdraw-') as raw:
        stage = Path(raw)
        for rel in inputs:
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, target)
        for name, pattern, marker, edits in WITHDRAWALS:
            changed = original.decode('utf-8')
            for before, after in edits:
                if changed.count(before) != 1:
                    raise AssertionError(name + ': unique product anchor changed')
                changed = changed.replace(before, after, 1)
            codes, failures = [], []
            command = ['node', '--test', '--test-name-pattern=' + pattern, TEST]
            for label, data in [('baseline', original), ('withdrawn', changed.encode('utf-8')), ('restored', original)]:
                (stage / SOURCE).write_bytes(data)
                result = subprocess.run(command, cwd=stage, env=environment, capture_output=True, timeout=30)
                (out / (name + '-' + label + '.stdout')).write_bytes(result.stdout)
                (out / (name + '-' + label + '.stderr')).write_bytes(result.stderr)
                codes.append(result.returncode)
                failures.append((result.stdout + result.stderr).decode('utf-8', 'replace'))
            if codes != [0, 1, 0] or marker not in failures[1] or 'ERR_ASSERTION' not in failures[1]:
                raise AssertionError(name + ': expected named assertion 0/1/0, got ' + repr(codes))
            records.append({'name': name, 'command': command, 'exit_codes': codes,
                            'assertion': marker, 'source_sha256': hashlib.sha256(original).hexdigest(),
                            'withdrawn_sha256': hashlib.sha256(changed.encode('utf-8')).hexdigest()})
    for rel, data in inputs.items():
        if (ROOT / rel).read_bytes() != data:
            raise AssertionError('input changed during isolated withdrawals: ' + rel)
    report = {'schema': 'pf6-app-local-withdrawals/1', 'official_mutation_evidence': False,
              'inputs': [{'path': rel, 'bytes': len(data),
                          'sha256': hashlib.sha256(data).hexdigest()}
                         for rel, data in inputs.items()], 'records': records}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
