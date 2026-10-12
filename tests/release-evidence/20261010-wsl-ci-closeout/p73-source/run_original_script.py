"""Run an archived WSL-only generator script UNMODIFIED except for the one clone-path literal (/root/p73-verify/src -> a Windows path).
usage: python -I run_original_script.py <script.py> <clone dir>"""
import sys, pathlib
script, clone = pathlib.Path(sys.argv[1]), sys.argv[2]
text = script.read_text(encoding='utf-8')
needle = "pathlib.Path('/root/p73-verify/src')"
assert text.count(needle) == 1, text.count(needle)
text = text.replace(needle, "pathlib.Path(%r)" % clone)
exec(compile(text, str(script), 'exec'), {'__name__': '__main__', '__file__': str(script)})
