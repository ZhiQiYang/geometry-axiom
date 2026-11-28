"""Generate PF6 App author fragments with the original encoder.

This writes author declarations, not cost, count, mutation or architecture
evidence. Official measurement/import must still be run after adoption.
"""
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import architecture_contract as architecture

MANIFEST = ROOT / 'geometry-core/domain-decoupling/product-architecture.json'
SOURCES = {
    'geometry-web/panel-fill-builder-session.js': ('javascript', 'PF-6 App proposal and selected-candidate owner: exact typed input, leases and original receipt recovery; native remains the only geometry evaluator'),
    'geometry-web/panel-fill-builder-workspace.js': ('javascript', 'PF-6 subform in the existing face inspector: explicit sources and selected set, human-readable same-candidate results and one confirmation action area'),
    'geometry-web/panel_fill_builder_transport.py': ('python', 'PF-6 closed App JSON transport and receipt admission: mandatory session/request/version, server-owned files and empty pre/post; native owns geometry'),
}
EXCLUSION = 'geometry-web/canvas_sections/P1286.js'
ROUTER_BEFORE = '751b98128e9ac089d39b0e6e01263174ab33ba36aea9f0a74048b85fd4f521aa'
ROUTER_REVIEWED = '05d9bb2b7292605f70e540cbd48039315ce811c9b8f1dbaecea16620f6d422dc'
ROUTE_FRAGMENT = 'htmlEmbedRoutes/6bbfa20cf83da82d0d08fa4622ffd85653822c7ff44f4a3ed8b7a98894b92766.json'
UI14_SOURCE = 'geometry-web/panel_fill_workflow_test.js'
UI14_BEFORE = 'db33ed38673fc783bdf8d2acf6fa47f3a873b742793e277cf9da3280f7c37d36'
UI14_REVIEWED = '8093ece2c8f8948444b74e4acbcb4ef2b473f5f625653ece8108397abffc8b5c'


def main():
    value = architecture.load_manifest(MANIFEST)
    touched = set()
    for relative, (language, purpose) in SOURCES.items():
        if not (ROOT / relative).is_file():
            raise SystemExit('PF6_APP_STAGE_MISSING: ' + relative)
        item = {'path': relative, 'language': language, 'layer': 'H', 'purpose': purpose}
        current = next((e for e in value['sources'] if e['path'] == relative), None)
        if current is not None and current != item:
            raise SystemExit('PF6_APP_STAGE_EXISTING_SOURCE_DIFFERS: ' + relative)
        if current is None:
            value['sources'].append(item)
        touched.add('sources/' + relative + '.json')
    raw = (ROOT / EXCLUSION).read_bytes()
    if b'\r' in raw:
        raise SystemExit('PF6_APP_STAGE_REQUIRES_LF')
    if any(e['path'] == EXCLUSION for e in value['sources']):
        raise SystemExit('PF6_APP_STAGE_CANNOT_EXCLUDE_PRODUCT')
    item = {'path': EXCLUSION, 'hashMode': 'lf', 'sha256': hashlib.sha256(raw).hexdigest(),
            'reason': 'PF-6 P1286 strict independent canvas module: real-CDP normal face form, explicit set, exact preview, cancellation and one-step history; dispatched only by canvas_registry.js, never a product dependency.'}
    value['exclusions'] = [e for e in value['exclusions'] if e['path'] != EXCLUSION] + [item]
    touched.add('exclusions/' + EXCLUSION + '.json')
    # This is a reviewed source pin, never a refresh-all operation. The reviewed
    # serve.py delta only adds PF6 bounded POST admission and path conversion;
    # do_GET, scenario query routing, index selection and iframe driver are
    # byte-identical to b3c4b981. Any later router edit requires another review.
    router = ROOT / 'geometry-web/serve.py'
    if hashlib.sha256(router.read_bytes().replace(b'\r\n', b'\n')).hexdigest() != ROUTER_REVIEWED:
        raise SystemExit('PF6_APP_ROUTER_REVIEW_REQUIRED')
    routes = [e for e in value['htmlEmbedRoutes'] if e['router'] == 'geometry-web/serve.py']
    if len(routes) != 1 or routes[0]['routerSha256'] not in {ROUTER_BEFORE, ROUTER_REVIEWED}:
        raise SystemExit('PF6_APP_ROUTER_PREVIOUS_PIN_DIFFERS')
    routes[0]['routerSha256'] = ROUTER_REVIEWED
    touched.add(ROUTE_FRAGMENT)
    # R2 explicitly migrates the existing one-check UI14 contract. Its original
    # five actions stay ordered; exactly PF6 is added, the real entry is unique
    # and disabled while the parent candidate is pending. Count/golden stay put.
    ui14 = (ROOT / UI14_SOURCE).read_bytes().replace(b'\r\n', b'\n')
    entries = [e for e in value['exclusions'] if e['path'] == UI14_SOURCE]
    if (hashlib.sha256(ui14).hexdigest() != UI14_REVIEWED or len(entries) != 1
            or entries[0]['sha256'] not in {UI14_BEFORE, UI14_REVIEWED}):
        raise SystemExit('PF6_APP_UI14_REVIEW_REQUIRED')
    entries[0]['sha256'] = UI14_REVIEWED
    touched.add('exclusions/' + UI14_SOURCE + '.json')
    generated = architecture.fragment_manifest_files(value)
    for relative in sorted(touched):
        name = architecture.FRAGMENT_DIRECTORY + '/' + relative
        target = MANIFEST.parent / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(generated[name])
        print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
