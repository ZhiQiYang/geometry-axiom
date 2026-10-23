ulimit -s 16384
test -x "$GEOMETRY_CHROME"
# WSL canvas wait trace
# Clear inherited flags for all other jobs.
unset GEOMETRY_WAIT_TRACE
unset GEOMETRY_WAIT_TRACE_RUN_ID
case "$GEOMETRY_BROWSER_SUITE:$(uname -r)" in
  canvas:*[Mm]icrosoft*) export GEOMETRY_WAIT_TRACE=1 ;;
esac
if [ "${GEOMETRY_WAIT_TRACE-}" = 1 ]; then
  export GEOMETRY_WAIT_TRACE_RUN_ID="$(python3 geometry-web/prepare_wait_trace.py)"
fi
if [ -n "${GITHUB_ENV-}" ]; then
  printf 'GEOMETRY_WAIT_TRACE=%s\n' "${GEOMETRY_WAIT_TRACE-}" >> "$GITHUB_ENV"
fi
python3 -u geometry-web/start_local.py --port 19893 > /tmp/g288p88f3/tmp/workflow/canvas/geometry-integration-server.log 2>&1 &
server=$!
cleanup() {
  original_status=$?
  set +e
  kill "$server" 2>/dev/null || true
  wait "$server" 2>/dev/null || true
  if [ "$GEOMETRY_BROWSER_SUITE" = canvas ]; then
    python3 geometry-web/archive_wait_trace.py /tmp/g288p88f3/tmp/workflow/canvas/geometry-wait-trace-artifact
    archive_status=$?
    if [ "$original_status" -eq 0 ] && [ "$archive_status" -ne 0 ]; then original_status=$archive_status; fi
  fi
  exit "$original_status"
}
trap cleanup EXIT
for attempt in $(seq 1 30); do
  if ! kill -0 "$server" 2>/dev/null; then
    cat /tmp/g288p88f3/tmp/workflow/canvas/geometry-integration-server.log
    exit 1
  fi
  if python3 geometry-web/runtime_version.py --probe 19893 > /dev/null 2>&1; then break; fi
  sleep 1
done
python3 geometry-web/runtime_version.py --probe 19893
# Independent matrix jobs expose each result promptly. They use
# separate runners/servers and do not cancel siblings on failure.
# The full canvas run retains its strict golden comparison.
set +e
case "$GEOMETRY_BROWSER_SUITE" in
  assembly) GEOMETRY_CDP_PORT=9367 GEOMETRY_ASSEMBLY_ONLY=1 node geometry-web/cdp_test.js ;;
  grid) GEOMETRY_CDP_PORT=9334 GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js ;;
  canvas) node geometry-web/cdp_test.js ;;
  space) GEOMETRY_CDP_PORT=9347 node geometry-web/space_model_test.js ;;
  timber) GEOMETRY_CDP_PORT=9348 GEOMETRY_TIMBER_ONLY=1 node geometry-web/space_model_test.js ;;
  documents) GEOMETRY_CDP_PORT=9366 node geometry-web/documents_browser_test.js ;;
  *) echo "Unknown browser suite"; exit 2 ;;
esac
status=$?
cat /tmp/g288p88f3/tmp/workflow/canvas/geometry-integration-server.log
exit "$status"
