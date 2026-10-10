# Geometry 102ff28e: formal six pass, caption scroll failure

All three commands below tested clean product `102ff28ecb005a85b42a8ae9cd7f22fdcf8cf01c` in `<workspace-path> isolated service 19180. Before/after runtime was fresh `9d9f3f49720e51d7238a68c8eb3318331d8e5fe326d70ee4351f2618ec206439`, PID 180039, session `45bc8906fb0d4316b7464f714a19570d`. Sources, configured executables/native closure, actual service bridge and clean full SHA matched. Actual Node and sandbox-enabled Chromium executable bytes, process IDs, command lines and new profiles were observed. Every command ended with `problems:[]`, and owned Node/browser processes were checked closed/absent. The root-owned service was not stopped. No product/Git writes, DOM patches, forced actions or pass-seeking retries were made.

These are separate scopes and their counts are not added:

| Actual command scope | Result | Exit | Acceptance complete |
| --- | --- | ---: | --- |
| Original formal six groups, no source override | 198/0 | 0 | true |
| Approved independent seven-width caption probe | 27/1 | 1 | false |
| Separately authorized single-1382 read-only scroll diagnosis | 27/1 | 1 | false; diagnostic only |

## Formal six

Original `tests/issue123_adopted_slices_browser.cjs` SHA256 `6efba5412916a31df431c557a7893019f186bf8adc3fa15aa059098367e272d1` completed colors 8, headers 35, components 28, v3 54, grid-mobile 4 and model 62, plus preflight 4/final 3. Sole canonical UI result, structured results and independent census agreed; `probeVerified:true`. This includes desktop and 390px behavior as defined in each original group, real pointer/keyboard, native-picked V3 selection/clear, ordinary grid-card entry, exact model preview/stale guard/create and actual full archive Save/New/Open/reopen/cancel-height checks.

- Gate: `ui123-102ff28e-gate/receipt.json`, SHA256 `21ce8111778c688050251fc45e61154fe6315d2de522fc179c6c8df2dcafd43c`.
- Raw log: `ui123-102ff28e-gate/command.log`, 32,937 bytes, SHA256 `f2a06e26d41fe55b1dcde27020a05d8ae41f579c79910756c175dd1319c3f8c3`.
- Probe: `<isolated-test-directory> SHA256 `63351c67d948b498d5e0550e8b0209b3ae110e01591594ef95e17ef9e306d4bc`.
- Executed sources: `ui123-102ff28e-gate/executed-sources/manifest.json`, 304 entries, SHA256 `5b0bd8ad41866a6e3a337e8099e5d2b119bbbbc6c7ab4e96b64ecbdf26938dcc`.
- Actual Node 180594 / Chromium 180630, closed and absent.

## Independent caption failure

Approved external source `01744e5910989b2454800ae1cef2c07c9b7db29185c28ece5fec6c65d44e496d` ran with distinct wrapper `9730f8ec7098b46f51c81fa82a0a389254ef5a3bcb683cc47aef7f30b59a949b`, explicitly identified as source override. At the first 1382px fixture, original owner/title, entered and post-pointer caption bounds, normal PAN and SELECT pointer actions passed. The forward seventh Tab reached PAN with real visible focus and outline, but failed original positive `hit` and `insideNav` conditions. PAN remained 73.625 × 34 and inside viewport/header. Reverse Tab/Enter, later caption snapshots, unchanged-native final check and the other six declared widths were not reached. Canonical `completed:true` means the sole group was attempted; gate acceptance is `completed:false`, `probeVerified:false`.

- Gate: `caption-102ff28e-gate/receipt.json`, SHA256 `d089098555a19d059d0f0d330dc6c63ffe738e949aeb958cc7530152d6fa7f57`.
- Raw log: `caption-102ff28e-gate/command.log`, 27,173 bytes, SHA256 `5eabe2b8772d4241753fe7e6c7cb9acb1df59f70bf77a36c8cfc2172560e3794`.
- Probe: `<isolated-test-directory> SHA256 `1e4296a1888ccf41fd205928dad9073bb2b467bb7fc582bfc3655715211532bd`.
- Executed sources: `caption-102ff28e-gate/executed-sources/manifest.json`, 305 entries, SHA256 `0f4647119c6e5ca4bc9ccda60f25d3123f58d0bf7da99b51a749a26a5852f948`.
- Actual failure screenshot: `<isolated-test-directory> actual Node 185343 / Chromium 185395, closed and absent.

## One authorized diagnosis

Source `eca2f1083f13751bc4471780ac651699d34c6ffd2e111bebe829f4b0de306484` retains every original assertion, fixture, normal pointer input, exact seven forward Tab steps and footer. Its width is explicitly one 1382px diagnostic, `acceptanceClaim:false`. It adds only DOM geometry/CSS/scroll/hit reads before the original input and Tab assertions. Independent read-only source review was 8/8, receipt `caption-scroll-diagnostic-source-review.json`, SHA256 `b2b216b7b08bf60318d6b131f0c8a5f99432ec6a10e0eab183b03d8e6fdd10d5`; that is static evidence, not browser acceptance.

The fresh profile reproduced the same seventh-Tab failure. At actual pointer PAN sampling, inner nav `scrollLeft=50`, PAN x-range `[895.375,969]`, center 932.1875 hit a contained SPAN. After pointer SELECT and on seventh Tab, nav `scrollLeft=0`, PAN range `[945.375,1019]`, center 982.1875 actually hit `HEADER.object-workspace-topbar`. Inner nav right edge was 977.984375, so PAN was clipped beyond it. Inner nav bbox `[398.59375,977.984375]`, width 579.390625, client width 577, scroll width 699; actual CSS `overflow-x:auto`, `overflow-y:hidden`, `display:flex`. Outer `.workspace-tools-row` had the same bbox, client width/scroll width 579/579 and `scrollLeft=0`, also configured auto/hidden flex. Thus both levels are configured scroll containers, but the outer container had no actual horizontal range in this frame. The diagnosis does not claim the outer actually scrolled or establish the browser algorithm responsible. It establishes the product's keyboard path leaves the inner nav at zero and PAN clipped, while the pointer path scrolls it into view.

All diagnostic readings are independent actual samples from this new command. They do not fill missing rectangles or scroll data in the original failed receipt.

- Gate: `caption-scroll-diagnostic-102ff28e-gate/receipt.json`, SHA256 `af27ccf6714abd41bf5ed5a920aa303ecee8ed6dfc73ef24b5c5028b183b009c`.
- Raw log: corresponding `command.log`, 27,373 bytes, SHA256 `1017dad4063a68971fc6d1551ae54d69f5e14e1b243afd629c01e85994cfaa18`.
- Probe: `<isolated-test-directory> SHA256 `9f82d12dfc4b651775100ad0a4b77e6402175415dc739d9f1e15340d3df75ae5`.
- Executed sources: `caption-scroll-diagnostic-102ff28e-gate/executed-sources/manifest.json`, 305 entries, SHA256 `693477a632d905ee6f86b4bfe080708b45ac81922fdc1b2e92deb92c6d7ff7d7`.
- Actual pointer PAN reading: `<isolated-test-directory> SHA256 `6bfe5f16ef9a601e9e56f6531b0f14c3f98a75cbe245566d45f16356cfe4ac95`.
- Actual failing Tab reading: corresponding `scroll-last_PAN_1382-6.json`, SHA256 `c4fe4a92a15d36a9f780ad4ad51e340ff81953448887c428d959dc610fa41c86`.
- Actual Node 195064 / Chromium 195103, closed and absent.

Remaining work is a product scroll/focus fix and purposefully scoped validation on its new clean SHA, retaining original positive inside-nav and live-hit assertions. No seven-width caption pass is claimed. 243 supplemental 327/0 and full #54 273/0, including six measured costs, remain bound to 243 and were not rerun or rebound. 640 formal six 198/0 remains its own historical run. None of these scopes constitutes full CDP, full Space, all #123, all 43 checklist items, physical phone/touch/IME, OS dialogs or golden/private ZIP comparison. Browser launch policy/flags were verified; kernel sandbox internals were not separately inspected.
