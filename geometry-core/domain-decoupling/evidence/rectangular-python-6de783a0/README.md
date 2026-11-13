# Source contract follow-up receipt

Source: `6de783a0b1f35357441d6dec7b6d25d43a977344`.
All twelve portable suites executed from a Git archive of this fixed commit.

```text
python tests/geometry_kernel_receipt.py --suite-set rectangular-python --source 6de783a0b1f35357441d6dec7b6d25d43a977344 --out <TEMP>/geometry-tests/geo261-rectangular-python-6de783a0
```

All 154 discovered tests passed with zero failures or skips. This includes the
same second-template, isolation and shared-engine negative controls documented
in `../rectangular-python-11cdeea8/README.md`, plus two contract corrections:

- Native woodworking length roots must contain integral dimension quantities
  with length units, including roots not selected for an output.
- Rectangular fields may share a typed source key. Repeated resolved slots must
  agree on value and revision, while the K graph retains a single descriptor
  and a single dependency edge for each referenced source.

The alias case uses fixed synthetic native-result coordinates for a 600×600,
5×3 grid. It yields fifteen 240000 mm³ members, preserves one shared source
identity, and rejects conflicting revisions. It does not implement subdivision.

The native bridge suite was not run by this portable command. Actual C→Python
execution still requires the separately frozen PR275 recipe and the shared
compiler queue. No product source-graph activation or complete native graph
coverage is claimed by this receipt.
