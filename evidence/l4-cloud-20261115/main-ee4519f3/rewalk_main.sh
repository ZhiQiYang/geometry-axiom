#!/bin/bash
# Re-walk #417's eight fixes on a clean worktree of main (private test servers only; not a user's service).
# usage: rewalk_main.sh <part>   part = a (findings 1-4, 6), b (finding 7 + D15), c (finding 5 + 8)
S=/tmp/claude-0/-home-user-geometry-axiom/c161fbcc-185e-5abd-ba3d-eaec6a803bff/scratchpad
W=$S/main2-wt; O=$S/l4-main; X=$W/evidence/l4-cloud-20261115/scripts
mkdir -p $O/fix $O/d17/screens $O/d15/screens $O/d18 $O/save-timing $O/formal-gate
serve() { bash $S/serve-wt.sh main2-wt 18839 2>&1 | tail -1 | cut -c1-140; }
stop() { pkill -f "start_local.py --port 18839"; pkill -f "serve.py 18839"; sleep 1; }
run() { local name=$1; shift; ( cd $X && env "$@" ) > $O/$name.log 2>&1; echo "$name exit=$?"; }
case "$1" in
  a)
    serve
    run verify_param_fix OUT=$O/fix timeout 600 node verify_param_fix.js
    run verify_asm_fix OUT=$O/fix timeout 600 node verify_asm_fix.js
    run walk_d17 OUT=$O/d17 timeout 900 node walk_d17.js
    stop ;;
  b)
    serve
    run walk_d15 OUT=$O/d15 timeout 900 node walk_d15.js
    stop; serve
    for mode in cancel save pause; do run leave-$mode OUT=$O/d15 TAG=main EDIT=1 MODE=$mode timeout 600 node verify_scenario_leave.js; done
    stop; serve
    run leave-cancel-stay OUT=$O/d15 TAG=main EDIT=1 MODE=cancel STAY=1 timeout 600 node verify_scenario_leave.js
    stop ;;
  c)
    serve
    run verify_grid_card OUT=$O/d18 SRC=$W/evidence/l4-cloud-20261115/d18/d18.gcanvas NAME=main HEAD_SHA=$(git -C $W rev-parse HEAD) GEOMETRY_TEST_URL=http://localhost:18839/ timeout 300 node verify_grid_card.js
    run capture_timing GEOMETRY_TEST_URL=http://127.0.0.1:18839/ timeout 1500 node capture_timing.js $O/save-timing/main-ee4519f3.json 0 3 6
    stop
    bash $S/run_formal_gate.sh $W 18842 $O/formal-gate main-ee4519f3 2>&1 | head -1 ;;
  d)
    mkdir -p $O/r20/screens $O/r21/screens $O/d18full/screens
    serve
    run walk_r20 OUT=$O/r20 timeout 900 node walk_r20.js
    stop; serve
    run walk_d18 OUT=$O/d18full SRC=$O/r20/r20.gcanvas timeout 900 node walk_d18.js
    run walk_d18b OUT=$O/d18full timeout 900 node walk_d18b.js
    stop; serve
    run walk_r21 OUT=$O/r21 timeout 900 node walk_r21.js
    stop ;;
esac
git -C $W status --short | wc -l
