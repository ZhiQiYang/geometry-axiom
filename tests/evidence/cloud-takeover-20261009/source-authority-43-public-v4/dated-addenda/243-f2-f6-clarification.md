# F2/F6 clarification, 2026-10-09 UTC

This dated append corrects the remaining-verification wording in `issue123-43-followup-243326/issue123-43-source-followup-243326.md` without rewriting that historical packet or its receipt.

On full clean source `243326b512896ace70e068f62c8f3d6397f6000d`, the already executed full Space suite was228/0, exit0, completed. Its original `command.log` contains these passed390px checks:

- Line202: `PASS GEO210 undefined projection retains a usable setup area and fully visible primary confirmation at 390x844`.
- Line211: `PASS GEO210 confirmation and create fit without hiding setup at 390x844`.

The first source assertion (`space_model_test.js:522`) checks confirmation top≥settings top and confirmation bottom≤setup bottom, a usable settings area, and viewport/overflow constraints. The second (`:543`) checks confirmation/create inside the screen, a usable settings area, and no horizontal overflow. These are actual passed same-version observations; F2/F6 must not describe those original390 confirmation-reachability checks as wholly unexecuted.

The original receipt path is `<original-evidence-root>/after-final-243326b5-full-space-20261009/receipt.json`, SHA256 `2f4f712f2caf1adc775cde1e11d6104c969c8f2e17abd446b9d505c87928e3c1`. The raw log path in that directory is `command.log`, SHA256 `81dfd5af1fc439332c8d428ffc55c3358adb95ac9c38314b4c342e94f4b86972`; the result is `space-artifacts/result.json`, SHA256 `687c82739d8dc3f7a74cadca37e50dff076d8684aa3987362640984133e64fe8`. The original source/runtime/executable identity and explicit timber omissions remain bound to that receipt.

Shared face-caption vertical bounds are a separate assertion. The original full Space font/layout block checks `titleWidth>0`; it does not measure title/eyebrow top/bottom or prove their placement inside the header. Caption remains independent pending verification at the later frozen caption source. The prepared standalone candidate is not a browser pass. No new source version borrows the243 result, and no private ZIP/all43/fullCDP acceptance follows from these two passed checks.
