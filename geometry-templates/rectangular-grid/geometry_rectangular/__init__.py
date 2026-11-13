"""A second template that assembles native cells with the public Python K API."""
from dataclasses import dataclass

from geometry_kernel import (AssemblyChild, AssemblyDef, EvaluationRequest,
    ExportRoot, ExtrusionDef, Limits, NodeInput, PlacedRegionDef, ProgramBuilder,
    ProvenanceTemplate, SourceRef, evaluate)


@dataclass(frozen=True)
class GridCell:
    column: int
    row: int
    region: SourceRef
    source: ProvenanceTemplate


@dataclass(frozen=True)
class RectangularGridView:
    sources: tuple
    frame: SourceRef
    thickness: SourceRef
    cells: tuple
    snapshot_identity: tuple


def compile_view(view):
    """Compose native-derived cells; all subdivision belongs to the native K."""
    if not isinstance(view, RectangularGridView):
        raise TypeError("Expected a complete typed rectangular grid view")
    builder = ProgramBuilder(view.sources, snapshot_identity=view.snapshot_identity)
    children = []
    for cell in view.cells:
        order = (cell.row, cell.column)
        placed = builder.add(PlacedRegionDef(view.frame, cell.region, cell.source),
                             order_token=(*order, "region"), declared=False)
        solid = builder.add(ExtrusionDef(placed, 0, view.thickness, cell.source),
                            order_token=(*order, "solid"), declared=False)
        children.append(AssemblyChild(NodeInput(solid), f"{cell.column}:{cell.row}"))
    assembly = builder.add(AssemblyDef(tuple(children)), order_token=("grid",))
    return builder.freeze(), EvaluationRequest((ExportRoot(assembly, output_tag=("rectangular-grid",)),))


def build_mesh(view, *, limits=Limits()):
    program, request = compile_view(view)
    return evaluate(program, request, limits=limits)


from .protocol import RejectedView, decode_view

__all__ = ["GridCell", "RectangularGridView", "compile_view", "build_mesh",
           "RejectedView", "decode_view"]
