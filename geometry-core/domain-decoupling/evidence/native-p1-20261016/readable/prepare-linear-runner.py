"""Prepare the independent fixed native linear/named-value evidence stage."""
from pathlib import Path

root = Path(__file__).resolve().parent
old = (root / 'run-native-grid.py').read_text(encoding='utf-8')
new = old.replace('6985cbd4bdbba0b0ecb1eaa572978c3845a53dfb', '2755228747a6ba86bd59ef0f34adfce7aabde441')
new = new.replace('6985cbd4', '27552287').replace('original 27 tests', 'original 6 tests')
new = new.replace('native-grid', 'native-linear').replace('N1c fixed', 'N2b fixed')
with (root / 'run-native-linear.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(new)
exercise = (root / 'exercise-native-grid.py').read_text(encoding='utf-8')
exercise = exercise.replace("('kernel', 'geometry', 'grid')", "('linear',)")
exercise = exercise.replace('build = modules[0]._BUILD', "build = importlib.import_module('tests.test_geo261_native_kernel')._BUILD")
exercise = exercise.replace('result.testsRun == 27', 'result.testsRun == 6')
with (root / 'exercise-native-linear.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(exercise)
