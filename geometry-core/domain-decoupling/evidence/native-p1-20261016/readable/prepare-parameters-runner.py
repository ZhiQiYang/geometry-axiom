"""Produce new fixed-SHA evidence scripts without changing product/tests."""
from pathlib import Path

root = Path(__file__).resolve().parent
old = (root / 'run-native-grid.py').read_text(encoding='utf-8')
new = old.replace('6985cbd4bdbba0b0ecb1eaa572978c3845a53dfb', '4aabd21cf82d495f5ab4902bedc9330ca5ed4e3b')
new = new.replace('6985cbd4', '4aabd21c').replace('original 27 tests', 'original 35 tests')
new = new.replace('native-grid', 'native-parameters').replace('native grid', 'native parameters').replace('N1c fixed', 'N2a fixed')
with (root / 'run-native-parameters.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(new)
exercise = (root / 'exercise-native-grid.py').read_text(encoding='utf-8')
exercise = exercise.replace("('kernel', 'geometry', 'grid')", "('kernel', 'geometry', 'grid', 'parameters')")
exercise = exercise.replace('result.testsRun == 27', 'result.testsRun == 35')
with (root / 'exercise-native-parameters.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(exercise)
