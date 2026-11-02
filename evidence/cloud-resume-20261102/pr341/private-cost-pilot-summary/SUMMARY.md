# One private F340 pilot — all raw retained, not formal B1

R2 source `edf556eedc204bb285fb4504e246e4310f4e1e88`; externally held seal `5044e6b39de80072660d5f33c6a4c153bede940c9194bb5db7fb31713aa84c51`. Exactly24 children exited0, no timeout/problem/unrun, no retry. Window451648143ns (0.451648143s); complete pre/post input checks passed.

Collector measurements below are one observation each, with separate work-only children. CPU is user+system in microseconds and includes timer/rusage bracket overhead. No statistical or speed verdict follows.

| Recipe | C wall µs / CPU µs | Rf wall µs / CPU µs | Rj wall µs / CPU µs |
|---|---:|---:|---:|
| U | 35.343 / 41 | 34.351 / 39 | 101.239 / 111 |
| S | 34.1 / 40 | 33.429 / 39 | 105.426 / 111 |
| D | 16.855 / 22 | 14.481 / 21 | 13.49 / 18 |
| X | 21269.608 / 21278 | 22963.481 / 22973 | 24338.132 / 24211 |

U/S C/Rf execute343 and have identical work vectors. They do not measure standalone341 no/low-duplicate fallback costs. Rj is the joint341+343 pipeline withdrawal with common unique bookkeeping retained.

For D, C avoided126memmoves/390096bytes but made8509pair visits and8127inactive skips; Rf/Rj each made382pair visits. The C one-point wall was16855ns, above Rf14481ns and Rj13490ns. This unfavorable observation is retained without claiming statistical regression.

X has exactly the same complete work vector in all variants, while one-point wall varies21.270/22.963/24.338ms. It supplies no new path-benefit claim.

All24 RSS readings are42308KiB. This driver-end OS high-water metric does not resolve collector/bitmap storage; report UNMEASURABLE, not zero memory cost. Full child CPU and supervisor wall remain separately labeled in TIMED_SAMPLES.csv.

All ordered returned nine-field outputs and original uncollected-tail oracles passed; each recipe has one identical canonical stdout across all six variant/mode combinations. RAW_MANIFEST.json hashes every original file; the producer originals were not edited.

Formal B1/R16/512World/newmain acceptance remains UNVERIFIED. The future65-fact no/low-duplicate public-helper case is UNRUN and was not added. X is helper-only, not larger World capacity. No full14/41, restored-C, additional samples, source edits or branch changes occurred.
