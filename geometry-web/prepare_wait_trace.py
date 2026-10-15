"""Begin an enabled canvas run without deleting any other feedback file."""
import os
from pathlib import Path
import uuid


def prepare():
    if os.environ.get('GEOMETRY_WAIT_TRACE') != '1' or os.environ.get('GEOMETRY_BROWSER_SUITE') != 'canvas':
        return ''
    directory = Path(os.environ['GEOMETRY_FEEDBACK_DIR'])
    directory.mkdir(parents=True, exist_ok=True)
    # Atomic directory-entry removal, only before this run's service starts.
    (directory / 'wait-trace.jsonl').unlink(missing_ok=True)
    return str(uuid.uuid4())


if __name__ == '__main__':
    print(prepare())
