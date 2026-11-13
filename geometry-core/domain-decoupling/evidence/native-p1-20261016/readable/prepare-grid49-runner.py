"""Create separately named, unexecuted N1c receipt scripts for the replacement SHA."""
from pathlib import Path

root = Path(__file__).resolve().parent
old = (root / 'run-native-grid.py').read_text(encoding='utf-8')
new = old.replace('6985cbd4bdbba0b0ecb1eaa572978c3845a53dfb', '49f03842cca4f70e0e38a82d120c06edd1b16189')
new = new.replace('6985cbd4', '49f03842').replace('original 27 tests', 'original 28 tests')
new = new.replace('exercise-native-grid.py', 'exercise-native-grid49.py').replace("'run-native-grid.py'", "'run-native-grid49.py'")
target = root / 'run-native-grid49.py'
with target.open('x', encoding='utf-8', newline='\n') as output:
    output.write(new)
exercise = (root / 'exercise-native-grid.py').read_text(encoding='utf-8').replace('result.testsRun == 27', 'result.testsRun == 28')
with (root / 'exercise-native-grid49.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(exercise)
