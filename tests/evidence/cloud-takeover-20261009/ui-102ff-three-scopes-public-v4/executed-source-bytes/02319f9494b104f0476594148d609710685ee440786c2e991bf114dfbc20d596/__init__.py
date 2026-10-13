"""Makes `tests` a regular package so `python -m unittest tests.test_x` and `from tests import _bridge` both resolve.

Test files also work as plain scripts (`python tests/test_x.py`): those that import from `tests` put the repo root on
sys.path first.  tests/run_all.py and tests/_unittest_runner.py load files by path and are unaffected.
"""
