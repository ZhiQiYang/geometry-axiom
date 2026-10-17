from pathlib import Path
source=Path('/tmp/geometry-198-reader-diagnostic.py').read_text().replace("out = Path('/tmp/geometry-198-review/reader-diagnostic')","out = Path('/tmp/geometry-198-review2/reader-diagnostic/artifacts')")
Path('/tmp/geometry-198-review2/reader-diagnostic.py').write_text(source)
