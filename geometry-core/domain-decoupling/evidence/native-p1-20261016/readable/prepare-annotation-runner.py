"""Prepare the separate fixed native draw-annotation evidence stage."""
from pathlib import Path

root = Path(__file__).resolve().parent
old = (root / 'run-native-grid.py').read_text(encoding='utf-8')
new = old.replace('6985cbd4bdbba0b0ecb1eaa572978c3845a53dfb', 'b370f753f22d0d119835c59d23b0a78344f8ee55')
new = new.replace('6985cbd4', 'b370f753').replace('original 27 tests', 'original 4 tests')
new = new.replace('native-grid', 'native-annotation').replace('N1c fixed', 'Draw annotation fixed')
with (root / 'run-native-annotation.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(new)
exercise = (root / 'exercise-native-grid.py').read_text(encoding='utf-8')
exercise = exercise.replace("[importlib.import_module('tests.test_geo261_native_' + name) for name in ('kernel', 'geometry', 'grid')]", "[importlib.import_module('tests.test_geo261_draw_annotation')]")
exercise = exercise.replace('build = modules[0]._BUILD', "build = importlib.import_module('tests.test_geo261_native_kernel')._BUILD")
exercise = exercise.replace('result.testsRun == 27', 'result.testsRun == 4')
with (root / 'exercise-native-annotation.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(exercise)
