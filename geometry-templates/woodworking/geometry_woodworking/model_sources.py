"""Bind a complete native source catalog to woodworking template inputs.

The host supplies opaque typed references and legacy root associations. This
policy does not parse scene syntax, execute processes or construct geometry.
"""
from dataclasses import dataclass, replace

from geometry_kernel import QuantityType, SourceRef, Unit, ValueType
from .model_policy import PolicyIssue


def _fail(message):
    raise PolicyIssue("BASE_SOURCE_BINDING", "I32", message, status="UNSUPPORTED")


@dataclass(frozen=True)
class TemplateSources:
    sources: tuple
    placements: tuple
    solids: tuple
    specs: tuple
    profiles: tuple
    provenance: tuple


def bind_sources(base, sources, roots):
    """Bind ``(association, SourceRef, faces)`` records without decoding keys.

    Association is (kind, id, slot, member_id, name); box faces are
    (axis, side, legacy_feature, opaque_feature_hex). Extra parameter roots are
    retained as native definitions but never promoted to geometry templates.
    """
    catalog = {source.key: source for source in sources}
    associations = {}
    for association, reference, faces in roots:
        if association in associations or not isinstance(reference, SourceRef):
            _fail("Native template source associations must be unique and typed.")
        descriptor = catalog.get(reference.key)
        if descriptor is None or reference.value_type != descriptor.value_type or reference.context != descriptor.context:
            _fail("Native template source reference disagrees with its descriptor.")
        associations[association] = (reference, faces)
    consumed = set()

    def take(kind, identity, slot, expected, member=None, name=None):
        association = (kind, identity, slot, member, name)
        if association not in associations:
            _fail("Native source graph is missing a template root association.")
        reference, faces = associations[association]
        if reference.value_type != expected:
            _fail("Native template root has the wrong source type.")
        value = catalog[reference.key].value
        if slot in ("spec.value", "profile.length") and value is not None:
            if value.value_type != QuantityType.DIMENSION or value.unit != Unit.MM or value.denominator != 1:
                _fail("Native geometry length roots require exact integral dimensions.")
        consumed.add(association)
        return reference, faces

    placements, solids, specs, profiles, provenance = [], [], [], [], {}
    updates = {}
    for placement in base["placements"]:
        identity = placement["id"]
        frame, _ = take("placement", identity, "placement.frame", ValueType.FRAME)
        region, _ = take("placement", identity, "placement.region", ValueType.REGION_SET)
        if frame.context != region.context:
            _fail("Native placement frame and region use different source contexts.")
        placements.append((("placement", identity), frame, region))
    for solid in base["solids"]:
        key = (solid["kind"], solid["id"])
        reference, faces = take(*key, "solid.box", ValueType.BOX)
        expected = {face["feature"] for face in solid["faces"]}
        if len(faces) != 6 or len(expected) != 6 or {face[2] for face in faces} != expected:
            _fail("Native box source faces disagree with legacy provenance.")
        by_side = {(axis, side): (feature, opaque) for axis, side, feature, opaque in faces}
        if set(by_side) != {(a, s) for a in range(3) for s in range(2)}:
            _fail("Native box source faces do not cover every local side.")
        descriptor = catalog[reference.key]
        if descriptor.value is not None:
            origins = []
            for index, origin in enumerate(descriptor.value.face_origins):
                feature, opaque = by_side[divmod(index, 2)]
                if origin.feature_key != ("face", opaque):
                    _fail("Native box feature identity disagrees with its association.")
                wire = (*key, solid.get("placement_id"), solid.get("boundary_id"), feature, -1, -1)
                opaque_key = (origin.origin_handle, origin.feature_key)
                if opaque_key in provenance and provenance[opaque_key] != wire:
                    _fail("A native feature cannot identify two legacy source records.")
                provenance[opaque_key] = wire
                origins.append(replace(origin, order_token=(*key, feature, -1, -1)))
            replacement = replace(descriptor, value=replace(descriptor.value, face_origins=tuple(origins)))
            if reference.key in updates and updates[reference.key] != replacement:
                _fail("Native box roots disagree about deterministic feature ordering.")
            updates[reference.key] = replacement
        solids.append((key, reference))
    for spec in base["specs"]:
        reference, _ = take("spec", 0, "spec.value", ValueType.QUANTITY, name=spec["name"])
        specs.append((spec["name"], reference))
    for run in base.get("profile_runs", ()):
        for member in (*[item["id"] for item in run["members"]], None):
            values = tuple(take("profile-run", run["id"], slot, expected, member=member)[0]
                           for slot, expected in (("profile.frame", ValueType.FRAME),
                                                  ("profile.region", ValueType.REGION_SET),
                                                  ("profile.length", ValueType.QUANTITY)))
            if values[0].context != values[1].context:
                _fail("Native profile frame and region use different source contexts.")
            profiles.append(((run["id"], member), values))
    parameters = set()
    for association in set(associations) - consumed:
        kind, identity, slot, member, name = association
        if kind != "parameter" or slot != "parameter.value" or member is None:
            _fail("Native source graph contains an unbound template root association.")
        if associations[association][0].value_type != ValueType.QUANTITY:
            _fail("Native parameter roots require typed quantities.")
        if (identity, member) in parameters:
            _fail("Native parameter fields cannot have multiple root names.")
        parameters.add((identity, member))
    return TemplateSources(tuple(updates.get(source.key, source) for source in sources),
        tuple(placements), tuple(solids), tuple(specs), tuple(profiles), tuple(provenance.items()))
