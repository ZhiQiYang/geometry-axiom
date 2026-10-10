"""Execute exact v8 scratch publisher with own complete Space source references.
Only the unrelated automatic common-source Git loop is skipped; it otherwise
rewrites existing saved snapshots. All copy/projection/receipt/collector code is
the original v8 implementation, with --only-extra and one Space config.
"""
from pathlib import Path
import importlib.util
import subprocess
from types import SimpleNamespace
path = Path(__file__).resolve().parent / 'prepare_ui_history_packet_v8.py'
spec = importlib.util.spec_from_file_location('space_publication_v8', path)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
skipped = []
def skip_unrelated_default_source_reference(command, **kwargs):
    assert command[:2] == ['git', 'show'], command
    skipped.append(command)
    return subprocess.CompletedProcess(command, 1, b'', b'Explicit scratch publication policy: unrelated default source references supplied separately; existing saved snapshots preserved.')
publisher.COMMON_SOURCES = []
publisher.subprocess = SimpleNamespace(run=skip_unrelated_default_source_reference)
publisher.main()
assert len(skipped) == 6
