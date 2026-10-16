"""Pure exact geometry API; no application, transport or template bootstrap."""
from .canonical import canonical_bytes, digest, strict_json_loads
from .errors import EvaluationError
from .types import (BoxDef, CoordinateDomain, FrameDef, Provenance, Quantity,
                    QuantityType, RegionDef, RegionSetDef, SourceKey, Unit,
                    box, frame, region)

__all__ = ["BoxDef", "CoordinateDomain", "EvaluationError", "FrameDef", "Provenance",
           "Quantity", "QuantityType", "RegionDef", "RegionSetDef", "SourceKey", "Unit",
           "box", "canonical_bytes", "digest", "frame", "region", "strict_json_loads"]
