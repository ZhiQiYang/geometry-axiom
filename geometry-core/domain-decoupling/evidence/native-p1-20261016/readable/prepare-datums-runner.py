"""Replace an unexecuted N2b-only stage with frozen N2c linear+datum evidence."""
from pathlib import Path

root = Path(__file__).resolve().parent
old = (root / 'run-native-grid.py').read_text(encoding='utf-8')
new = old.replace('6985cbd4bdbba0b0ecb1eaa572978c3845a53dfb', '1e55c9b999fe6297c4821690b588b419cae50f69')
new = new.replace('6985cbd4', '1e55c9b9').replace('original 27 tests', 'original 13 linear+datum tests')
new = new.replace('native-grid', 'native-datums').replace('N1c fixed', 'N2c fixed')
with (root / 'run-native-datums.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(new)
exercise = (root / 'exercise-native-grid.py').read_text(encoding='utf-8')
exercise = exercise.replace("('kernel', 'geometry', 'grid')", "('linear', 'datums')")
exercise = exercise.replace('build = modules[0]._BUILD', "build = importlib.import_module('tests.test_geo261_native_kernel')._BUILD")
exercise = exercise.replace('result.testsRun == 27', 'result.testsRun == 13')
with (root / 'exercise-native-datums.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(exercise)
