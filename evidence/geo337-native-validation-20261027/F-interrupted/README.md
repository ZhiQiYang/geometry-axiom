# Recovery F interrupted launcher attempt

SHA `cbf0fb621888596aa14ad5f2349b503e23b1b72d`. This attempt was safely interrupted and is not a complete native acceptance run.

The launcher's orphan-reaper thread failed because this kernel does not expose `/proc/PID/task/TID/children`. The original thread exception was returned by the execution tool (session 99780, chunk ac7312); the launcher source and interruption reason are retained here. The test stdout/stderr streams were captured separately and remain unmodified. No product/test file was changed.

The runner received SIGINT through its existing cleanup path and returned 130 after 129.954 seconds; it did not reach the 35-minute timeout. See `INTERRUPTION.json` and `RESULT.json`. All original native output was archived and hashed, then the owned directory was renamed to `/tmp/geo337-F-cbf0fb62-interrupted-output-preserved`; no files were deleted.

A separate attempt uses a corrected, self-tested process-local subreaper based on `/proc/PID/stat`, preserving all test assertions. Its results must be read separately.
