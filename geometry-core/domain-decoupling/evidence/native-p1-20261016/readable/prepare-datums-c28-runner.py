"""Fresh receipt names for the unexecuted datum cache-semantics correction."""
from pathlib import Path

root = Path(__file__).resolve().parent
old = (root / 'run-native-datums.py').read_text(encoding='utf-8')
new = old.replace('1e55c9b999fe6297c4821690b588b419cae50f69', 'c28ea9639b79881f30995cd79ce843346373c31e')
new = new.replace('1e55c9b9', 'c28ea963')
new = new.replace('exercise-native-datums.py', 'exercise-native-datums-c28.py').replace("'run-native-datums.py'", "'run-native-datums-c28.py'")
with (root / 'run-native-datums-c28.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write(new)
with (root / 'exercise-native-datums-c28.py').open('x', encoding='utf-8', newline='\n') as output:
    output.write((root / 'exercise-native-datums.py').read_text(encoding='utf-8'))
