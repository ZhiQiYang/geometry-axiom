# Prototype Instructions

## Selected design

The user selected the third displayed Product Design mock on 2026-09-17: a dark axiom reader, with navigation on the left, the active clause in the middle, and a pinned reference pane on the right. The source visual is copied to `qa/reference.png`. Keep the actual project clauses and engineering diagrams authoritative when the generated mock's copy differs. Keep all work in this folder; the geometry project has unrelated concurrent changes.

## 🔴 2026-09-18 使用者拍板:公理層閱讀器只准有一份,而且不是這裡產的

**這個資料夾是設計參考,不是閱讀器來源。** 正典閱讀器是
`geometry-guide/公理層-閱讀器.html`(批註版,使用者批註後逐版取代)。
**禁止**在這裡產生、交付或建議任何「閱讀器」產物,包含 `公理層閱讀器-離線版.html`
與 `dist/` —— 正典本來就已經是零外部引用的單一自足檔,雙擊即可離線開啟,
**不需要也不准再做離線版**。

已撤銷的前一條指示:原本這裡寫著「保留 `npm run build:offline` 與其自足的
`公理層閱讀器-離線版.html` 輸出」。那條指示正是專案一度同時存在 5 份閱讀器的原因
(那份離線版 9.2MB,比正典大 9.4 倍,多出來的幾乎全是內嵌完整字型,離線能力卻完全相同)。
`build:offline` 已從 `package.json` 移除,既有的 9.2MB 檔請勿重建。

完整規則見 repo 根目錄 `AGENTS.md`。要破例只能由使用者當場明示同意,
並在 `BACKLOG.md` 開工單記錄。

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.
