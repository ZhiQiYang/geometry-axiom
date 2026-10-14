# Existing aggregate evidence, readable transport

These ASCII base64 parts reproduce the existing `../aggregate-raw.tar.gz` byte for byte. They contain no new test run or changed results. The source run used clean d9c5aef86274045a46aa4d40ba1b0f58a51582e8; evidence-only delivery was 6afb6d7df308ad7e1c5e7784e7c10d8589c41a94.

Read parts in manifest order, concatenate and base64-decode while ignoring whitespace. Verify archive bytes/SHA against manifest, then independently verify all 190 file members against `../aggregate-members.json`. `verify.py.txt` performs these checks without extracting or executing archive contents. Run it with Python from any directory. This transport verification does not rerun suites or replace final integration/WSL judgment.
