"""Run the second-template sequence inside a K-only Python installation."""
import argparse
import importlib.abc
import json
from pathlib import Path
import sys


class RejectApplicationImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in ("modeling", "geometry_app", "geometry_woodworking"):
            raise AssertionError("Application or first-template import: " + fullname)
        return None


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--library",type=Path,required=True)
    parser.add_argument("--events",type=Path,required=True)
    parser.add_argument("--binary-sha256",required=True)
    args=parser.parse_args()
    library=args.library.resolve()
    sys.meta_path.insert(0,RejectApplicationImports())
    sys.path.insert(0,str(library))
    from geometry_kernel import ProgramSession
    from geometry_rectangular import RejectedView,compile_view,decode_view
    events=args.events.read_text(encoding="utf-8").splitlines()
    assert len(events)==3,"Native producer must emit two results and one rejection"
    stamp=("rectangular-core-only",args.binary_sha256)
    first=decode_view(events[0],execution_identity=stamp)
    second=decode_view(events[1],execution_identity=stamp)
    assert tuple(source.key for source in first.sources)==tuple(source.key for source in second.sources)
    program,request=compile_view(first)
    session=ProgramSession(program,request)
    initial=session.snapshot
    assert len(initial.result.records)==15
    assert {record.mesh["volume_mm3"] for record in initial.result.records}=={"400000"}
    assert {len(record.mesh["triangles"]) for record in initial.result.records}=={12}
    replacement,request=compile_view(second)
    token,candidate=session.preview(replacement,request,evaluator_stamp=stamp)
    assert {record.mesh["volume_mm3"] for record in candidate.result.records}=={"480000"}
    assert session.snapshot==initial
    committed=session.confirm(token,evaluator_stamp=stamp)
    assert session.revision==1
    before=session.snapshot
    try:
        decode_view(events[2],execution_identity=stamp)
    except RejectedView as error:
        assert error.code=="FRACTIONAL_CELL"
    else:
        raise AssertionError("Rejected native candidate produced a geometry view")
    assert session.snapshot==before and session.revision==1
    assert tuple(source.key for source in before.program.sources)==tuple(source.key for source in program.sources)
    loaded={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
            if name.startswith(("geometry_kernel","geometry_rectangular"))}
    assert loaded and all(Path(path).is_relative_to(library) for path in loaded.values())
    assert not any(name.split(".")[0] in ("modeling","geometry_app","geometry_woodworking") for name in sys.modules)
    print(json.dumps({"status":"OK","member_counts":[len(initial.result.records),len(committed.result.records)],
        "total_volumes_mm3":[str(sum(int(record.mesh["volume_mm3"]) for record in result.records))
                              for result in (initial.result,committed.result)],
        "source_keys_stable":True,"rejected":"FRACTIONAL_CELL","revision_after_rejection":session.revision,
        "loaded_modules":loaded},sort_keys=True))


if __name__=="__main__":
    main()
