import importlib.util
import os
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
port = int(sys.argv[2])
native_dir = Path(sys.argv[3]).resolve()
spec = importlib.util.spec_from_file_location('stage_launcher', root / 'geometry-web/start_local.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
launcher.ensure_stack()
launcher.check_port(port)
registry = launcher.load_registry(root)
paths = launcher.prepare_binaries(native_dir, registry)
environment = launcher.runtime_environment(paths)
environment['GEOMETRY_FEEDBACK_DIR'] = '<isolated-test-directory>' + str(port)
Path(environment['GEOMETRY_FEEDBACK_DIR']).mkdir(mode=0o700, exist_ok=True)
launcher.check_port(port)
os.chdir(root)
os.execve(sys.executable, [sys.executable, '-u', str(root / 'geometry-web/serve.py'), str(port)], environment)
