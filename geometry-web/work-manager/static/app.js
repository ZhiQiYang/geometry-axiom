"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const executionLabels = { unknown: "待核", unassigned: "未接手", active: "執行中", stopped: "已停止・待接續", blocked: "阻塞", finished: "執行已結束" };
  const deliveryLabels = { no_pr: "尚未交 PR", awaiting_review: "待審", awaiting_integration: "待整合", verification_pending: "驗證待補", approval_blocked: "待批准・交付阻塞", done: "已完成並整合", unknown: "待核" };
  const statusLabels = { ...executionLabels, ...deliveryLabels, approved: "已批准", granted: "已批准", required: "需要批准", pending: "待批准", denied: "未批准", held: "暫緩", hold: "暫緩", passed: "通過", pass: "通過", success: "成功", failed: "失敗", failure: "失敗", skipped: "未執行", not_run: "未執行", not_executed: "未執行", expired: "已過期", stale: "已過期", valid: "有效", invalid: "無效", merged: "已整合", error: "讀取失敗", ok: "已讀取", healthy: "已讀取", available: "可用", unavailable: "來源失聯", missing: "缺少資料", manual: "手動匯入", fetched: "已讀取", stopped: "已停止", completed: "執行已結束", cancelled: "已取消", assigned: "已派工", released: "已釋放", reserved: "曾保留", revoked: "已撤回", approved_review: "審查通過", changes_requested: "審查要求修改" };
  const actionLabels = { work: "執行工作", assign: "登記派工", assignment: "登記派工", review: "審查", merge: "合併 PR", publish: "發布", retry: "重試", execute: "執行工作", integrate: "整合", approve: "批准", verify: "補驗證", wait: "等待", reconcile: "重新核對", resume: "接續工作", review_pr: "核對 PR 與驗收證據", review_integration: "核對整合條件", verify_acceptance: "核對必要驗收", inspect_scope: "核對工作範圍", request_approval: "整理待批准事項", continue_work: "接續範圍內的工作" };
  const severityLabels = { critical: "必須處理", error: "需處理", warning: "請留意", warn: "請留意", info: "待確認" };
  const freshnessLabels = { current: "近期快照", stale: "超過同步期限", future: "時間在未來", error: "讀取失敗", unknown: "待核" };
  const modeLabels = { read_only: "唯讀核對", write: "可寫入工作", wait: "等待／待批准", none: "無新動作" };
  const validityLabels = { ...statusLabels, future: "時間在未來", ci_failed: "CI 失敗", ci_unknown: "CI 待核", merged_commit: "合併 commit 綁定", tree_equivalent: "已證明 tree 等價" };
  const sourceKindLabels = { github: "GitHub 讀取", github_live: "GitHub 讀取", git: "Git 版本讀取", operator: "CLI 手動登記", api: "API 讀取", live: "API 讀取", manual: "手動匯入", manual_snapshot: "手動匯入快照", snapshot: "手動匯入快照", parent_snapshot: "父任務快照（手動匯入）", parent: "父任務快照（手動匯入）" };
  let state = null;
  let busy = false;
  const expanded = new Set();
  const dates = new Intl.DateTimeFormat("zh-TW", { timeZone: "UTC", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" });

  function text(value, fallback = "待核") {
    if (value === null || value === undefined || value === "") return fallback;
    if (Array.isArray(value)) return value.map((part) => text(part, "")).filter(Boolean).join("、");
    if (typeof value === "object") {
      return text(value.message ?? value.reason ?? value.title ?? value.description ?? value.label ?? value.action ?? value.id, fallback);
    }
    return String(value);
  }

  function el(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = text(value, "");
    return node;
  }

  function array(value) {
    if (Array.isArray(value)) return value;
    if (value === undefined || value === null || value === "") return [];
    return [value];
  }

  function stamp(value) {
    if (!value) return "待核";
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? text(value) : dates.format(date).replaceAll("/", "-");
  }

  function age(value) {
    if (!value) return "";
    const ms = Date.parse(value);
    if (!Number.isFinite(ms)) return "時間格式待核";
    const minutes = Math.floor((Date.now() - ms) / 60000);
    if (minutes < -1) return "來源時間在未來，請核對";
    if (minutes < 1) return "不到 1 分鐘前";
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} 小時前`;
    return `${Math.floor(minutes / 1440)} 天前`;
  }

  function safeURL(value) {
    if (typeof value !== "string") return null;
    try {
      const url = new URL(value);
      return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null;
    } catch { return null; }
  }

  function link(value, label, className) {
    const href = safeURL(value);
    if (!href) return el("span", className, label || "連結無效／待核");
    const node = el("a", className, label || href);
    node.href = href;
    node.target = "_blank";
    node.rel = "noopener noreferrer";
    return node;
  }

  function tone(status) {
    if (["blocked", "denied", "failed", "failure", "ci_failed", "error", "invalid", "unavailable"].includes(status)) return "red";
    if (["stopped", "no_pr", "awaiting_review", "awaiting_integration", "verification_pending", "approval_blocked", "draft", "pending", "required", "held", "hold", "expired", "stale", "future", "not_run", "not_executed", "skipped"].includes(status)) return "amber";
    if (["active", "assigned"].includes(status)) return "blue";
    if (["done", "approved", "granted", "passed", "pass", "success", "valid", "merged"].includes(status)) return "green";
    return "";
  }

  function badge(status, labels = statusLabels) {
    return el("span", `badge ${tone(status)}`.trim(), labels[status] || text(status));
  }

  function actionText(value) {
    if (typeof value === "string") return actionLabels[value] || value;
    if (!value) return "核對來源與前置條件";
    return text(value.message ?? value.description ?? value.label ?? value.reason ?? actionLabels[value.action] ?? value.action, "核對來源與前置條件");
  }

  function alertText(value) { return typeof value === "string" ? value : text(value?.message ?? value?.reason ?? value?.description ?? value?.code, "待確認警示"); }
  function actionMode(task) {
    return el("span", `mode-tag ${modeLabels[task.next_action_mode] ? task.next_action_mode : ""}`, task.next_action_completed === true ? "已完成本輪核對" : modeLabels[task.next_action_mode] || "操作模式待核");
  }
  function setFilter(filter) {
    $("search-input").value = "";
    $("status-filter").value = filter;
    renderQueue();
    $("work-queue").scrollIntoView();
  }
  function alertTaskId(value) { return typeof value === "object" && value ? text(value.task_id ?? value.task, "") : ""; }
  function findTask(id) { return state?.tasks.find((task) => task.id === id); }
  function readyTasks() { return array(state?.ready).map((entry) => typeof entry === "string" ? findTask(entry) : findTask(entry.id) || entry).filter(Boolean); }
  function taskAlerts(task) { return array(task.alerts); }
  function invalidStore() { return state?.store_health?.status === "invalid"; }
  function isUmbrella(task) { return task.node_kind === "umbrella"; }
  function childTasks(task) { return state.tasks.filter((candidate) => candidate.parent_id === task.id); }

  function openTask(id) {
    if (!findTask(id)) return;
    expanded.add(id);
    $("search-input").value = "";
    $("status-filter").value = "all";
    renderQueue();
    const row = [...$("task-rows").querySelectorAll(".task-row")].find((node) => node.dataset.taskId === id);
    if (row) {
      row.scrollIntoView({ behavior: "auto", block: "start" });
      row.querySelector(".task-title")?.focus({ preventScroll: true });
    }
  }

  function taskButton(task, className) {
    const button = el("button", className, text(task.title, task.id));
    button.type = "button";
    button.addEventListener("click", () => openTask(task.id));
    return button;
  }

  function hierarchyLink(id) {
    const parent = findTask(id);
    if (parent) return taskButton(parent, "dependency-button");
    return el("span", "subtle", `${text(id)}（來源待核）`);
  }

  function hierarchySummary(task) {
    const summary = el("div", "hierarchy-hint");
    if (isUmbrella(task)) summary.append(el("span", "node-kind", "彙總工單 · 不獨立派工"));
    if (task.parent_id) { summary.append(el("span", "node-kind", "上層"), hierarchyLink(task.parent_id)); }
    return summary;
  }

  function renderStoreHealth() {
    const health = state.store_health;
    $("store-health-error").hidden = !invalidStore();
    if (!invalidStore()) return;
    $("store-health-heading").textContent = "資料校驗失敗";
    $("store-health-summary").textContent = health.backup_preserved === true
      ? "原紀錄已保留；停止派工／完成判定。以下是資料診斷，不是沒有工作的正常空佇列。"
      : "停止派工／完成判定。原紀錄保留狀態待核；以下是資料診斷，不是沒有工作的正常空佇列。";
    const backup = [];
    if (health.read_only === true) backup.push("唯讀診斷模式");
    if (Number.isInteger(health.row_count)) backup.push(`原紀錄 ${health.row_count} 筆`);
    else if (health.row_count && typeof health.row_count === "object") {
      for (const [key, label] of [["sources", "來源"], ["snapshots", "快照"], ["events", "事件"]]) {
        if (Number.isInteger(health.row_count[key])) backup.push(`${label} ${health.row_count[key]} 筆`);
      }
    }
    if (health.backup_checksum) backup.push(`備份 SHA-256：${health.backup_checksum}`);
    $("store-health-backup").textContent = backup.join(" · ");
    const issues = document.createDocumentFragment();
    for (const issue of array(health.issues)) {
      const item = el("li");
      item.append(el("strong", "", alertText(issue)));
      if (typeof issue === "object" && issue !== null) {
        const context = [issue.code, issue.event_id && `事件 ${issue.event_id}`, issue.task_id && `工作 ${issue.task_id}`, issue.source_id && `來源 ${issue.source_id}`].filter(Boolean);
        if (context.length) item.append(el("p", "subtle", context.join(" · ")));
      }
      issues.append(item);
    }
    if (!issues.childNodes.length) issues.append(el("li", "", "診斷細節待核；請保留原資料與備份。"));
    $("store-health-issues").replaceChildren(issues);
  }

  function renderCoverage() {
    const coverage = state.coverage;
    if (invalidStore()) {
      $("coverage-overview-summary").textContent = "資料校驗失敗，來源覆蓋暫停判定。";
      $("coverage-overview-time").textContent = "原紀錄保留狀態見上方診斷。";
      $("coverage-repositories").replaceChildren(el("p", "empty", "資料校驗失敗，無法判定 issue／PR 覆蓋。"));
      return;
    }
    if (!coverage || (!array(coverage.repositories).length && !array(coverage.pr_repositories).length && !array(coverage.pr_links).length)) {
      $("coverage-overview-summary").textContent = "尚未匯入 issue 清單；登記工作數不代表完整覆蓋。";
      $("coverage-overview-time").textContent = "來源清單與工作狀態分別核對。";
      $("coverage-repositories").replaceChildren(el("p", "empty", "尚未匯入 issue 清單，完整來源覆蓋待核。"));
      return;
    }
    $("coverage-overview-summary").textContent = array(coverage.repositories).length ? `快照內開啟 issue ${coverage.count} · 已映射 ${coverage.captured} · 範圍待核 ${coverage.missing_scope}` : "尚未匯入 issue 清單；登記工作數不代表完整覆蓋。";
    $("coverage-overview-time").textContent = array(coverage.repositories).map((repo) => {
      const source = state.sources.find((item) => item.id === repo.source_id);
      return `${sourceKindLabels[source?.kind] || "來源模式待核"} · ${stamp(repo.as_of)} UTC${repo.complete === true ? "" : " · 部分清單"}`;
    }).join("；");
    const repositories = document.createDocumentFragment();
    for (const repo of array(coverage.repositories)) {
      const section = el("section", "coverage-repository");
      const heading = el("div", "coverage-repo-heading");
      heading.append(el("h3", "", repo.repository), el("span", "badge", repo.complete === true ? "完整 issue 清單快照" : "部分 issue 清單快照"), el("span", "subtle", `清單 ${repo.count} · 已映射 ${repo.captured} · 範圍待核 ${repo.missing_scope}`));
      const source = state.sources.find((item) => item.id === repo.source_id);
      section.append(heading, el("p", "coverage-source", `${sourceKindLabels[source?.kind] || "來源模式待核"} · ${repo.source_id} · 版本 ${text(repo.source_version)} · 截至 ${stamp(repo.as_of)} UTC`));
      const wrap = el("div", "coverage-table-wrap");
      const table = el("table", "coverage-table");
      table.append(el("caption", "sr-only", `${repo.repository} 開啟 issue 與登記工作、PR 對照`));
      const thead = el("thead"), header = el("tr");
      for (const label of ["開啟 issue", "對應登記工作", "範圍", "所有關聯 PR"]) { const th = el("th", "", label); th.scope = "col"; header.append(th); }
      thead.append(header); table.append(thead);
      const body = el("tbody");
      for (const issue of array(repo.issues)) {
        const row = el("tr"); row.dataset.issueNumber = String(issue.number);
        const issueCell = el("td");
        issueCell.append(link(issue.url, `Issue #${issue.number}`), el("span", "coverage-issue-title", issue.title || "標題待核"));
        const tasks = el("td"); tasks.dataset.label = "對應登記工作";
        for (const id of array(issue.task_ids)) {
          const task = findTask(id);
          if (task) {
            const button = taskButton(task, "coverage-task");
            if (isUmbrella(task)) button.append(el("span", "node-kind", " · 彙總工單"));
            tasks.append(button);
          } else tasks.append(el("p", "subtle", `${id}（工作來源待核）`));
        }
        if (!tasks.childElementCount) tasks.append(el("span", "subtle", "尚未映射工作；範圍與 owner 待核"));
        const scope = el("td"); scope.dataset.label = "範圍";
        scope.append(el("span", `badge ${issue.scope_status === "missing" ? "amber" : ""}`, issue.scope_status === "known" ? "已登記範圍" : "範圍待核"));
        if (issue.captured === false) scope.append(el("p", "subtle", "尚未映射"));
        const prs = el("td"); prs.dataset.label = "所有關聯 PR";
        const links = el("div", "coverage-pr-links");
        for (const pr of array(issue.pr_links)) links.append(link(pr.url, pr.number ? `PR #${pr.number}` : "PR 連結"));
        if (!links.childElementCount) links.append(el("span", "subtle", "尚無登記連結"));
        prs.append(links); row.append(issueCell, tasks, scope, prs); body.append(row);
      }
      table.append(body); wrap.append(table); section.append(wrap); repositories.append(section);
    }
    if (array(coverage.pr_links).length || array(coverage.pr_repositories).length) repositories.append(prCoverageSection(coverage));
    $("coverage-repositories").replaceChildren(repositories);
  }

  function prCoverageSection(coverage) {
    const section = el("section", "coverage-repository");
    const heading = el("div", "coverage-repo-heading coverage-catalog-heading");
    heading.append(el("h3", "", "全部已知 PR 連結"), el("span", "subtle", `本次 PR 清單 ${text(coverage.pr_count)} · 已映射 ${text(coverage.pr_captured)} · 範圍待核 ${text(coverage.pr_missing_scope)} · 可追溯連結 ${array(coverage.pr_links).length}`));
    section.append(heading);
    for (const repo of array(coverage.pr_repositories)) {
      const source = state.sources.find((item) => item.id === repo.source_id);
      section.append(el("p", "coverage-source", `${repo.repository} · ${sourceKindLabels[source?.kind] || "來源模式待核"} · ${repo.source_id} 版本 ${text(repo.source_version)} · ${stamp(repo.as_of)} UTC · ${repo.complete === true ? "完整 PR 清單快照" : "部分 PR 清單快照"}`));
    }
    const wrap = el("div", "coverage-table-wrap");
    const table = el("table", "coverage-table pr-coverage-table");
    table.append(el("caption", "sr-only", "本次清單及歷史引用中的全部已知 PR 連結，保留來源時間與版本"));
    const thead = el("thead"), header = el("tr");
    for (const label of ["PR", "關聯登記工作", "版本／狀態", "來源快照"]) { const th = el("th", "", label); th.scope = "col"; header.append(th); }
    thead.append(header); table.append(thead);
    const body = el("tbody");
    for (const pr of array(coverage.pr_links)) {
      const row = el("tr"); row.dataset.prNumber = String(pr.number);
      const identity = el("td");
      identity.append(link(pr.url, pr.number ? `PR #${pr.number}` : "PR 連結"), el("span", "coverage-issue-title", pr.title || "標題待核"), el("p", "subtle", pr.listed_in_current_inventory === true ? "本次 PR 清單" : "清單外引用 · 狀態依證據"));
      const tasks = el("td"); tasks.dataset.label = "關聯登記工作";
      for (const id of array(pr.task_ids)) {
        const task = findTask(id);
        if (task) tasks.append(taskButton(task, "coverage-task")); else tasks.append(el("p", "subtle", `${id}（工作來源待核）`));
      }
      if (!tasks.childElementCount) tasks.append(el("span", "subtle", "尚未映射工作"));
      if (pr.scope_status === "missing") tasks.append(el("p", "subtle", "範圍待核"));
      const version = el("td"); version.dataset.label = "版本／狀態";
      if (pr.merged === true) version.append(badge("merged"));
      else version.append(el("span", "badge", pr.merged === false ? "尚未整合" : "整合狀態待核"));
      if (pr.draft === true) version.append(badge("draft", { draft: "草稿 PR" }));
      else version.append(el("span", "badge", pr.draft === false ? "非草稿 PR" : "草稿狀態待核"));
      version.append(el("code", "", `head：${text(pr.head_sha)}`), el("p", "subtle", `base：${text(pr.base)}`));
      if (pr.base_sha) version.append(el("code", "", pr.base_sha));
      const sources = el("td"); sources.dataset.label = "來源快照";
      for (const source of array(pr.sources)) sources.append(el("p", "subtle", `${source.id} · 版本 ${text(source.version)} · ${stamp(source.as_of)} UTC`));
      if (!sources.childElementCount) sources.append(el("span", "subtle", "來源時間待核"));
      row.append(identity, tasks, version, sources); body.append(row);
    }
    table.append(body); wrap.append(table); section.append(wrap);
    return section;
  }

  function renderSync() {
    const kinds = new Set(array(state.sources).map((source) => source.kind));
    const hasManual = [...kinds].some((kind) => !["git", "github", "github_live", "api", "live"].includes(kind));
    $("source-mode").textContent = invalidStore() ? "校驗失敗・來源待核" : state.sources.length ? hasManual ? "含手動匯入快照" : "已讀取來源快照" : "尚無來源";
    $("last-synced").textContent = stamp(state.last_synced_at);
    $("sync-age").textContent = age(state.last_synced_at);
    $("generated-at").textContent = stamp(state.generated_at);
    $("state-hash").textContent = state.state_hash;
    $("copy-hash-button").disabled = false;
    $("schema-version").textContent = `資料契約版本：${text(state.schema_version)}`;
  }

  function renderReady() {
    if (invalidStore()) {
      $("ready-count").textContent = "暫停判定";
      $("ready-mode-counts").replaceChildren(el("span", "subtle", "資料校驗失敗，停止派工／完成判定。"));
      $("ready-list").replaceChildren(el("p", "empty", "請先處理上方資料診斷；目前不提供可派工作或完成結論。"));
      return;
    }
    const tasks = readyTasks();
    $("ready-count").textContent = `${tasks.length} 項動作`;
    const counts = state.ready_counts;
    const modes = document.createDocumentFragment();
    if (counts && Number.isInteger(counts.read_only) && Number.isInteger(counts.write)) {
      const waitCount = Number.isInteger(counts.wait) ? counts.wait : state.tasks.filter((task) => task.next_action_mode === "wait").length;
      for (const [mode, count, label] of [["read_only", counts.read_only, "唯讀核對"], ["write", counts.write, "可寫入"], ["wait", waitCount, "等待"]]) {
        const button = el("button", "mode-count", label);
        button.type = "button";
        button.append(el("strong", "", String(count)));
        button.addEventListener("click", () => setFilter(mode));
        modes.append(button);
      }
    } else modes.append(el("span", "subtle", "操作類型待核；未推斷可派工數量。"));
    $("ready-mode-counts").replaceChildren(modes);
    const fragment = document.createDocumentFragment();
    if (!tasks.length) fragment.append(el("p", "empty", "目前沒有新的可進行動作；可查看等待狀態與已完成本輪核對紀錄。"));
    for (const task of tasks.slice(0, 3)) {
      const button = el("button", "ready-entry");
      button.type = "button";
      button.append(actionMode(task), el("span", "task-id", task.id), el("strong", "", text(task.title, task.id)), el("p", "", actionText(task.next_action)));
      button.addEventListener("click", () => openTask(task.id));
      fragment.append(button);
    }
    if (tasks.length > 1) {
      const button = el("button", `button small ready-more${tasks.length <= 3 ? " only-mobile" : ""}`, `查看全部 ${tasks.length} 項可進行的下一步`);
      button.type = "button";
      button.addEventListener("click", () => setFilter("ready"));
      fragment.append(button);
    }
    $("ready-list").replaceChildren(fragment);
  }

  function refs(task) {
    const list = el("div", "task-refs");
    const items = array(task.refs).slice();
    if (task.pr?.url && !items.some((ref) => ref.url === task.pr.url)) items.push({ kind: "pr", number: task.pr.number, url: task.pr.url });
    for (const ref of items) {
      const kind = text(ref.kind, "來源");
      const label = ref.number ? `${kind.toLowerCase() === "pr" || kind.toLowerCase() === "pull_request" ? "PR" : kind.toLowerCase() === "issue" ? "Issue" : kind} #${ref.number}` : text(ref.title ?? ref.label, kind);
      list.append(link(ref.url, label));
    }
    if (!list.childElementCount) list.append(el("span", "subtle", "來源引用待核"));
    if (task.pr?.draft === true) list.append(badge("draft", { draft: "草稿 PR" }));
    return list;
  }

  function detailField(label, value, full = false) {
    const field = el("div", `detail-field${full ? " full" : ""}`);
    const dd = el("dd");
    if (value instanceof Node) dd.append(value); else dd.textContent = text(value);
    field.append(el("dt", "", label), dd);
    return field;
  }

  function listOf(values, emptyLabel = "尚未登記", code = false) {
    const list = el("ul", "plain-list");
    for (const value of array(values)) {
      const li = el("li");
      li.append(el(code ? "code" : "span", "", text(value)));
      list.append(li);
    }
    if (!list.childElementCount) list.append(el("li", "subtle", emptyLabel));
    return list;
  }

  function approvalList(task) {
    const list = el("ul", "plain-list");
    for (const approval of array(task.approval_constraints)) {
      const li = el("li");
      if (typeof approval === "string") li.textContent = approval;
      else {
        const line = el("div", "approval-line");
        line.append(el("strong", "", actionLabels[approval.action] || text(approval.action, "行動待核")), badge(approval.status || "unknown"));
        line.append(el("span", "subtle", approval.scope === "action" ? "限制此動作" : approval.scope === "completion" ? "完成所需批准" : approval.scope === undefined ? "完成所需批准（預設）" : "適用範圍待核"));
        li.append(line);
        if (approval.reason) li.append(el("span", "approval-reason", approval.reason));
      }
      list.append(li);
    }
    if (!list.childElementCount) list.append(el("li", "subtle", "未登記額外批准條件；仍不代表取得外部操作授權。"));
    return list;
  }

  function acceptanceList(task) {
    if (!array(task.acceptance).length) return listOf(task.required_acceptance, "未登記驗收條件，完成狀態待核");
    const list = el("ul", "plain-list");
    for (const item of task.acceptance) {
      const entry = el("li", "approval-line");
      entry.append(el("span", "", item.criterion), badge(item.result || "unknown"));
      if (item.evidence_id) entry.append(el("code", "subtle", item.evidence_id));
      list.append(entry);
    }
    return list;
  }

  function provenanceList(task) {
    const list = el("ul", "audit-list");
    for (const source of array(task.source_provenance)) {
      const item = el("li", "audit-entry");
      const top = el("div", "audit-meta");
      top.append(el("strong", "", source.id), badge(source.freshness || "unknown", freshnessLabels));
      item.append(top, el("p", "", `${sourceKindLabels[source.kind] || text(source.kind)} · 版本 ${text(source.version)} · 截至 ${stamp(source.as_of)} UTC`));
      if (source.last_verified_at) item.append(el("p", "", `最近觀測：${stamp(source.last_verified_at)} UTC · 觀測版本 ${text(source.observed_version)}`));
      if (source.source_sha) item.append(el("p", "", `來源 SHA：${source.source_sha}`));
      if (source.url) item.append(link(source.url, "開啟來源"));
      list.append(item);
    }
    if (!list.childElementCount) list.append(el("li", "subtle", "工作來源尚未登記；請核對來源與版本。"));
    return list;
  }

  function evidenceSection(task) {
    const section = el("section", "audit-section");
    section.append(el("h4", "", "驗證證據"));
    const evidence = array(task.evidence ?? task.last_verified_evidence);
    if (!evidence.length) { section.append(el("p", "subtle", "尚無驗證證據，完成狀態待核。")); return section; }
    const list = el("ol", "audit-list");
    for (const item of evidence) {
      const entry = el("li", "audit-entry");
      if (!item || typeof item !== "object") { entry.textContent = text(item); list.append(entry); continue; }
      const meta = el("div", "audit-meta");
      meta.append(el("strong", "", text(item.criterion ?? item.kind ?? item.acceptance_id ?? item.name ?? item.id, "證據")), badge(item.effective_result || "unknown"));
      if (item.validity) meta.append(badge(item.validity, validityLabels));
      if (item.status) meta.append(badge(item.status));
      if (item.expired === true || item.stale === true) meta.append(badge("expired"));
      meta.append(el("time", "", stamp(item.timestamp ?? item.verified_at ?? item.at)));
      entry.append(meta);
      const fields = el("ul", "plain-list");
      const sha = item.sha ?? item.head_sha ?? item.commit_sha;
      fields.append(el("li", "", `實際驗證 SHA（原始）：${text(sha)}`));
      for (const [key, label] of [["tree_sha", "Git tree SHA"], ["equivalent_head_sha", "等價映射的 PR head SHA"], ["bound_head_sha", "有效綁定的 head SHA"], ["binding_kind", "綁定依據"]]) {
        if (item[key] !== undefined && item[key] !== null) fields.append(el("li", "", `${label}：${text(item[key])}`));
      }
      if (item.applicable_to_current_head !== undefined) fields.append(el("li", "", `適用目前 head：${item.applicable_to_current_head === true ? "是" : item.applicable_to_current_head === false ? "否" : "待核"}`));
      fields.append(el("li", "", `原始結果紀錄：${statusLabels[item.result] || text(item.result)}；有效判定以上方狀態為準。`));
      for (const [key, label] of [["criterion", "驗收條件"], ["acceptance_id", "驗收條件"], ["kind", "證據類型"], ["expires_at", "有效期限 UTC"], ["source_id", "來源"], ["source_version", "來源版本"], ["event_id", "事件 ID"], ["runner_count", "Runner 數"], ["runner_id", "Runner ID"], ["steps", "步驟"], ["step_count", "步驟數"], ["reason", "說明"]]) {
        if (item[key] !== undefined) fields.append(el("li", "", `${label}：${Array.isArray(item[key]) && key === "steps" ? item[key].length : text(item[key])}`));
      }
      if (item.url) { const li = el("li"); li.append(link(item.url, "開啟驗證證據")); fields.append(li); }
      entry.append(fields);
      list.append(entry);
    }
    section.append(list);
    return section;
  }

  function prSection(task) {
    if (!task.pr) return null;
    const pr = task.pr;
    const section = el("section", "audit-section");
    section.append(el("h4", "", "PR 交付紀錄"));
    const fields = el("dl", "detail-grid");
    fields.append(
      detailField("Pull request", link(pr.url, pr.number ? `PR #${pr.number}` : "開啟 PR")),
      detailField("PR 草稿狀態", pr.draft === true ? "草稿 PR" : pr.draft === false ? "非草稿 PR" : "待核"),
      detailField("目前 head 的有效審查", ({ approved: "目前 head 審查通過", pending: "待審", changes_requested: "要求修改", unknown: "審查綁定待核", stale: "舊 head 審查已過期" })[pr.effective_review_state] || "審查綁定待核"),
      detailField("來源原始審查宣稱", ({ approved: "宣稱審查通過（須核對 SHA）", pending: "待審", changes_requested: "要求修改", unknown: "待核" })[pr.review_state] || text(pr.review_state)),
      detailField("審查綁定 SHA", el("code", "", text(pr.reviewed_sha)), true),
      detailField("PR 整合紀錄", pr.merged === true ? "已整合；工作驗收仍以交付狀態為準" : pr.merged === false ? "尚未整合" : "待核"),
      detailField("PR 已發布 head SHA", el("code", "", text(task.published_head_sha ?? pr.head_sha))),
      detailField("整合時 head SHA", el("code", "", text(pr.merged_head_sha)), true),
      detailField("合併 commit SHA", el("code", "", text(pr.merge_commit_sha)), true)
    );
    section.append(fields);
    if (array(task.ci_runs ?? pr.ci_runs).length) section.append(ciRunsSection(task.ci_runs ?? pr.ci_runs));
    if (array(task.ci ?? pr.ci).length) {
      const list = el("ul", "audit-list");
      list.classList.add("audit-section");
      for (const job of array(task.ci ?? pr.ci)) {
        const item = el("li", "audit-entry");
        const meta = el("div", "audit-meta");
        meta.append(el("strong", "", text(job.name, "CI 工作")), badge(job.effective_result || "unknown"));
        item.append(meta);
        item.append(el("p", "", `原始紀錄：${statusLabels[job.status] || text(job.status)} · ${statusLabels[job.conclusion] || text(job.conclusion)}；以有效判定為準。`));
        item.append(el("p", "", `SHA：${text(job.sha)}`), el("p", "", `Runner：${text(job.runner_id)} · 步驟數：${Array.isArray(job.steps) ? job.steps.length : text(job.steps)}`));
        if (job.id !== undefined || job.run_id !== undefined || job.attempt !== undefined) item.append(el("p", "", `Job ID：${text(job.id)} · Workflow run：${text(job.run_id)} · 執行次數：${text(job.attempt)}`));
        if (job.validity) item.append(badge(job.validity, validityLabels));
        for (const [key, label] of [["tree_sha", "Git tree SHA"], ["equivalent_head_sha", "等價映射 head SHA"], ["bound_head_sha", "有效綁定 head SHA"], ["binding_kind", "綁定依據"]]) {
          if (job[key] !== undefined && job[key] !== null) item.append(el("p", "", `${label}：${text(job[key])}`));
        }
        if (job.evaluation) item.append(el("p", "", text(job.evaluation)));
        if (job.url) item.append(link(job.url, "CI 紀錄"));
        list.append(item);
      }
      section.append(list);
    }
    return section;
  }

  function ciRunsSection(runs) {
    const section = el("section", "ci-runs audit-section");
    section.append(el("h4", "", "Workflow 整體結果"), el("p", "subtle", "整體結果與個別 job 分別列示；交付狀態依資料校驗結果判定。"));
    const list = el("ul", "audit-list");
    for (const run of array(runs)) {
      const item = el("li", "ci-run-entry");
      const meta = el("div", "audit-meta");
      meta.append(el("strong", "", `Run ${text(run.id)}`), badge(run.effective_result || "unknown"));
      item.append(meta, el("p", "", `實際 run SHA：${text(run.sha)}`), el("p", "", `執行次數：${text(run.attempt)} · 來源記錄 jobs：${text(run.job_count)}`));
      if (run.observed_job_count !== undefined) item.append(el("p", "", `已對應的 job 紀錄：${text(run.observed_job_count)}`));
      if (run.job_count === 0) item.append(el("p", "ci-no-jobs", "未取得 job 紀錄；請核對 workflow run 與來源觀測。"));
      item.append(el("p", "", `原始 run 紀錄：${statusLabels[run.status] || text(run.status)} · ${statusLabels[run.conclusion] || text(run.conclusion)}；以上方有效結果為準。`));
      if (run.url) item.append(link(run.url, "Workflow run 紀錄"));
      list.append(item);
    }
    section.append(list);
    return section;
  }

  function completedActionsSection(task) {
    const section = el("section", "audit-section");
    section.append(el("h4", "", "已完成的操作紀錄"));
    if (task.next_action_completed === true) section.append(el("p", "subtle", "已完成本輪核對；相同輸入版本不重複列為下一步，等待相關輸入更新。"));
    const receipts = array(task.completed_actions);
    if (!receipts.length) { section.append(el("p", "subtle", "尚未登記完成收據。")); return section; }
    const list = el("ol", "audit-list");
    for (const receipt of receipts) {
      const item = el("li", "audit-entry");
      const top = el("div", "audit-meta");
      top.append(el("strong", "", actionLabels[receipt.action] || text(receipt.action, "操作待核")), el("time", "", stamp(receipt.timestamp)));
      item.append(top, el("p", "", "本次操作綁定的輸入版本"), el("code", "input-pin", text(receipt.input_pin)));
      if (receipt.summary) item.append(el("p", "", receipt.summary));
      list.append(item);
    }
    section.append(list);
    return section;
  }

  function historySection(task) {
    const section = el("section", "audit-section");
    section.append(el("h4", "", "派工與所有權紀錄"));
    const history = array(task.assignment_history);
    if (!history.length) { section.append(el("p", "subtle", "尚無可追溯的所有權事件。")); return section; }
    const list = el("ol", "audit-list");
    for (const raw of history) {
      const entry = el("li", "audit-entry");
      if (!raw || typeof raw !== "object") { entry.textContent = text(raw); list.append(entry); continue; }
      const item = { ...raw.data, ...raw };
      const meta = el("div", "audit-meta");
      meta.append(el("strong", "", statusLabels[item.action] || actionLabels[item.action] || actionLabels[item.kind] || text(item.action ?? item.kind, "所有權事件")), el("time", "", stamp(item.occurred_at ?? item.timestamp ?? item.at ?? item.as_of)));
      entry.append(meta);
      const fields = el("ul", "plain-list");
      if (item.applied !== undefined) fields.append(el("li", "", item.applied ? "事件已套用" : "事件未套用；保留供追溯"));
      for (const [key, label] of [["owner_thread", "Owner thread"], ["previous_owner_thread", "前任 owner"], ["status", "狀態"], ["execution_status", "執行狀態"], ["reserved", "保留標記"], ["branch", "分支"], ["event_id", "事件 ID"], ["source_id", "來源"], ["source_version", "來源版本"], ["version", "事件版本"], ["reason", "說明"]]) {
        if (item[key] !== undefined) fields.append(el("li", "", `${label}：${["status", "execution_status"].includes(key) ? statusLabels[item[key]] || text(item[key]) : text(item[key])}`));
      }
      if (item.url) { const li = el("li"); li.append(link(item.url, "事件依據")); fields.append(li); }
      entry.append(fields);
      list.append(entry);
    }
    section.append(list);
    return section;
  }

  function taskDetail(task) {
    const panel = el("div", "task-detail");
    const top = el("div", "detail-topline");
    top.append(el("h3", "", `工作紀錄 · ${task.id}`));
    const close = el("button", "button small", "收起");
    close.type = "button";
    close.addEventListener("click", () => { expanded.delete(task.id); renderQueue(); const row = [...$("task-rows").querySelectorAll(".task-row")].find((node) => node.dataset.taskId === task.id); row?.querySelector(".task-title")?.focus({ preventScroll: true }); });
    top.append(close);
    panel.append(top);
    const details = el("dl", "detail-grid");
    details.append(detailField("節點類型", isUmbrella(task) ? "彙總工單（不獨立派工）" : "工作"));
    if (task.head_alignment === "different") details.append(detailField("版本待核", el("p", "head-alignment-warning", "工作與已發布 head 不同；待核是否有尚未發布變更。不推定哪個版本較新。"), true));
    if (task.parent_id) details.append(detailField("父工單", hierarchyLink(task.parent_id)));
    const children = childTasks(task);
    if (isUmbrella(task) || children.length) {
      const list = el("ul", "plain-list");
      for (const child of children) { const item = el("li"); item.append(taskButton(child, "dependency-button")); list.append(item); }
      if (!children.length) list.append(el("li", "subtle", "未登記子工作；不推斷已完成。"));
      details.append(detailField("關聯子工作", list, true));
    }
    details.append(detailField("範圍", task.scope, true), detailField("檔案範圍", listOf(task.files, "尚未登記檔案範圍", true), true), detailField("Owner thread", el("code", "", text(task.owner_thread, "未登記"))), detailField("分支", el("code", "", text(task.branch))), detailField("工作 head SHA", el("code", "", text(task.head_sha)), true), detailField("PR 已發布 head SHA", el("code", "", text(task.published_head_sha ?? task.pr?.head_sha)), true));
    if (task.head_origin) details.append(detailField("工作 head 來源", ({ work: "工作紀錄", pr: "PR metadata（尚無獨立工作 head 紀錄）", unknown: "待核" })[task.head_origin] || "待核", true));
    details.append(detailField("最早可開始 · UTC", task.not_before ? stamp(task.not_before) : "未定日期"), detailField("最近適用驗證 · UTC", task.last_verified_evidence?.timestamp ? stamp(task.last_verified_evidence.timestamp) : "尚無適用目前 head 的有效驗證紀錄"));
    const dependencies = el("ul", "plain-list");
    for (const dependency of array(task.dependencies)) {
      const id = typeof dependency === "string" ? dependency : text(dependency.id ?? dependency.task_id, "");
      const li = el("li");
      const button = el("button", "dependency-button", id || text(dependency));
      button.type = "button";
      button.addEventListener("click", () => openTask(id));
      if (!findTask(id)) { button.disabled = true; button.textContent += "（來源待核）"; }
      li.append(button);
      dependencies.append(li);
    }
    if (!dependencies.childElementCount) dependencies.append(el("li", "subtle", "未登記依賴"));
    details.append(detailField("工作依賴", dependencies), detailField("必須通過的驗收條件", acceptanceList(task), true), detailField("批准限制", approvalList(task), true), detailField("下一步操作類型", actionMode(task)), detailField("下一步綁定的輸入版本", el("code", "input-pin", text(task.next_action_pin)), true), detailField("建議下一步", actionText(task.next_action), true), detailField("本工作來源與版本", provenanceList(task), true));
    if (taskAlerts(task).length) details.append(detailField("工作警示", listOf(taskAlerts(task).map(alertText)), true));
    panel.append(details);
    const pr = prSection(task);
    if (pr) panel.append(pr);
    else if (array(task.ci_runs).length) panel.append(ciRunsSection(task.ci_runs));
    panel.append(evidenceSection(task), completedActionsSection(task), historySection(task));
    return panel;
  }

  function matchesFilter(task, filter, readyIds) {
    switch (filter) {
      case "ready": return readyIds.has(task.id);
      case "read_only": return readyIds.has(task.id) && task.next_action_mode === "read_only";
      case "write": return readyIds.has(task.id) && task.next_action_mode === "write";
      case "wait": return task.next_action_mode === "wait";
      case "checked": return task.next_action_completed === true;
      case "attention": return taskAlerts(task).length > 0 || array(state.alerts).some((alert) => alertTaskId(alert) === task.id);
      case "review": return ["awaiting_review", "awaiting_integration"].includes(task.delivery_status);
      case "blocked": return task.execution_status === "blocked" || task.delivery_status === "approval_blocked";
      case "stopped": return task.execution_status === "stopped";
      case "unknown": return !task.execution_status || task.execution_status === "unknown" || !task.delivery_status || task.delivery_status === "unknown";
      case "done": return task.delivery_status === "done";
      default: return true;
    }
  }

  function renderQueue() {
    if (!state) return;
    $("search-input").disabled = invalidStore();
    $("status-filter").disabled = invalidStore();
    if (invalidStore()) {
      $("task-count").textContent = "待核";
      $("filter-summary").textContent = "校驗診斷中；目前不判定工作數量或完成狀態。";
      $("task-rows").replaceChildren();
      $("queue-empty").textContent = "下列空白不代表沒有工作，請先處理上方資料診斷。";
      $("queue-empty").hidden = false;
      return;
    }
    $("queue-empty").textContent = "沒有符合條件的工作。";
    const query = $("search-input").value.trim().toLocaleLowerCase();
    const filter = $("status-filter").value;
    const readyIds = new Set(readyTasks().map((task) => task.id));
    const tasks = state.tasks.filter((task) => {
      const haystack = [task.id, task.title, task.branch, ...array(task.files), ...array(task.refs).map((ref) => `${ref.kind || ""} ${ref.number || ""}`)].map((value) => text(value, "")).join(" ").toLocaleLowerCase();
      return (!query || haystack.includes(query)) && matchesFilter(task, filter, readyIds);
    });
    const umbrellas = state.tasks.filter(isUmbrella).length;
    $("task-count").textContent = umbrellas ? `${state.tasks.length - umbrellas} 工作 · ${umbrellas} 彙總` : `${state.tasks.length} 工作`;
    $("filter-summary").textContent = `顯示 ${tasks.length} / ${state.tasks.length} 筆登記紀錄 · 點名稱查看證據與關聯`;
    const fragment = document.createDocumentFragment();
    for (const [index, task] of tasks.entries()) {
      const isOpen = expanded.has(task.id);
      const row = el("tr", `task-row${isOpen ? " is-open" : ""}`);
      row.dataset.taskId = task.id;
      const work = el("td");
      work.append(el("span", "task-id", task.id));
      const title = el("button", "task-title", text(task.title, task.id));
      title.type = "button";
      title.setAttribute("aria-expanded", String(isOpen));
      title.setAttribute("aria-controls", `task-detail-${index}`);
      title.addEventListener("click", () => { if (expanded.has(task.id)) expanded.delete(task.id); else expanded.add(task.id); renderQueue(); const next = [...$("task-rows").querySelectorAll(".task-row")].find((node) => node.dataset.taskId === task.id); next?.querySelector(".task-title")?.focus({ preventScroll: true }); });
      work.append(title);
      if (isUmbrella(task) || task.parent_id) work.append(hierarchySummary(task));
      work.append(refs(task), el("span", "detail-hint", isOpen ? "紀錄已展開" : "查看紀錄"));
      row.append(work);
      const execution = el("td");
      execution.dataset.label = "執行";
      execution.append(badge(task.execution_status || "unknown", executionLabels));
      const delivery = el("td");
      delivery.dataset.label = "交付";
      delivery.append(badge(task.delivery_status || "unknown", deliveryLabels));
      const owner = el("td");
      owner.dataset.label = "執行者／版本";
      owner.append(el("span", "owner-state", task.owner_thread ? "已登記執行者" : "未登記執行者"));
      const sha = el("code", "sha", task.head_sha ? String(task.head_sha).slice(0, 12) : "SHA 待核");
      sha.title = text(task.head_sha);
      owner.append(sha);
      const manualSources = array(task.source_provenance).filter((source) => source.kind === "manual_snapshot" && source.as_of).sort((a, b) => Date.parse(a.as_of) - Date.parse(b.as_of));
      if (manualSources.length) owner.append(el("span", "source-asof", `${manualSources.length > 1 ? "最早" : "手動"}快照 ${stamp(manualSources[0].as_of)} UTC`));
      if (manualSources[0]?.last_verified_at && manualSources[0].last_verified_at !== manualSources[0].as_of) owner.append(el("span", "source-asof", `最近觀測 ${stamp(manualSources[0].last_verified_at)} UTC`));
      const action = el("td", "next-action");
      action.append(actionMode(task), el("span", "", actionText(task.next_action)));
      action.dataset.label = "下一步";
      if (taskAlerts(task).length) action.append(el("span", "row-alert", `${taskAlerts(task).length} 項警示`));
      row.append(execution, delivery, owner, action);
      const detail = el("tr", "detail-row");
      detail.id = `task-detail-${index}`;
      detail.hidden = !isOpen;
      const cell = el("td");
      cell.colSpan = 5;
      if (isOpen) cell.append(taskDetail(task));
      detail.append(cell);
      fragment.append(row, detail);
    }
    $("task-rows").replaceChildren(fragment);
    $("queue-empty").hidden = tasks.length > 0;
  }

  function renderAlerts() {
    if (invalidStore()) {
      $("alert-count").textContent = "待核";
      $("alerts-list").replaceChildren(el("p", "empty", "工作警示暫停判定，資料診斷見上方。"));
      return;
    }
    const alerts = array(state.alerts);
    $("alert-count").textContent = String(alerts.length);
    const fragment = document.createDocumentFragment();
    for (const alert of alerts) {
      const entry = el("article", "alert-entry");
      const severity = typeof alert === "object" ? alert.severity : "warning";
      const label = el("span", `badge ${["error", "critical"].includes(severity) ? "red" : severity === "info" ? "" : "amber"}`, severityLabels[severity] || "請留意");
      entry.append(label);
      const task = findTask(alertTaskId(alert));
      if (task) entry.append(taskButton(task, "alert-task"));
      entry.append(el("p", "", alertText(alert)));
      if (typeof alert === "object" && alert.code) entry.append(el("code", "alert-code", alert.code));
      fragment.append(entry);
    }
    if (!alerts.length) fragment.append(el("p", "empty", "目前快照沒有警示；仍請核對來源時間。"));
    $("alerts-list").replaceChildren(fragment);
  }

  function scheduleEntry(task, dated) {
    const entry = el("li", dated ? "schedule-entry" : "undated-entry");
    if (dated) { const time = el("time", "", stamp(task.not_before)); time.dateTime = task.not_before; entry.append(time); }
    const body = el("div");
    body.append(taskButton(task, "schedule-title"));
    body.append(el("p", "", `${executionLabels[task.execution_status] || text(task.execution_status)} · ${deliveryLabels[task.delivery_status] || text(task.delivery_status)}`));
    if (array(task.dependencies).length) body.append(el("p", "", `依賴：${text(task.dependencies)}`));
    entry.append(body);
    return entry;
  }

  function renderSchedule() {
    if (invalidStore()) {
      $("dated-schedule").replaceChildren(el("li", "empty", "資料校驗失敗，排程暫停判定。"));
      $("undated-schedule").replaceChildren(el("li", "empty", "資料校驗失敗，未定日期工作暫停判定。"));
      return;
    }
    const dated = state.tasks.filter((task) => !isUmbrella(task) && task.not_before).slice().sort((a, b) => Date.parse(a.not_before) - Date.parse(b.not_before) || a.id.localeCompare(b.id));
    const undated = state.tasks.filter((task) => !isUmbrella(task) && !task.not_before);
    const datedFragment = document.createDocumentFragment();
    const undatedFragment = document.createDocumentFragment();
    for (const task of dated) datedFragment.append(scheduleEntry(task, true));
    for (const task of undated) undatedFragment.append(scheduleEntry(task, false));
    if (!dated.length) datedFragment.append(el("li", "empty", "沒有已登記日期的工作。"));
    if (!undated.length) undatedFragment.append(el("li", "empty", "沒有未定日期的工作。"));
    $("dated-schedule").replaceChildren(datedFragment);
    $("undated-schedule").replaceChildren(undatedFragment);
  }

  function renderSources() {
    const fragment = document.createDocumentFragment();
    for (const source of state.sources) {
      const entry = el("article", "source-entry");
      const title = el("div", "source-title");
      title.append(el("strong", "", source.id), badge(source.status || "unknown"));
      if (source.freshness) title.append(badge(source.freshness, freshnessLabels));
      entry.append(title);
      const fields = el("dl");
      fields.append(el("dt", "", "來源類型"), el("dd", "", sourceKindLabels[source.kind] || `${text(source.kind)}（匯入來源）`), el("dt", "", "來源截至 UTC"), el("dd", "", stamp(source.as_of)), el("dt", "", "來源版本"), el("dd", "", text(source.version)));
      if (source.last_success_at) fields.append(el("dt", "", "上次成功 UTC"), el("dd", "", stamp(source.last_success_at)));
      const shaValue = source.source_sha ?? source.sha ?? source.head_sha;
      if (shaValue) { const sha = el("dd"); sha.append(el("code", "", shaValue)); fields.append(el("dt", "", "來源 SHA"), sha); }
      if (source.url) { const url = el("dd"); url.append(link(source.url, "開啟來源")); fields.append(el("dt", "", "來源連結"), url); }
      entry.append(fields);
      if (source.error) entry.append(el("p", "source-error", `讀取失敗：${text(source.error)}。保留上次已知資料，請重新核對。`));
      if (array(source.ci).length || array(source.ci_runs).length) entry.append(sourceCI(source));
      fragment.append(entry);
    }
    if (!state.sources.length) fragment.append(el("p", "empty", invalidStore() ? "校驗未通過，來源紀錄暫停判定。" : "尚無已登記來源，請先匯入通過校驗的快照。"));
    $("sources-list").replaceChildren(fragment);
  }

  function sourceCI(source) {
    const jobs = array(source.ci);
    const runs = array(source.ci_runs);
    const section = el("details", "source-ci");
    const notRun = jobs.filter((job) => job.effective_result === "not_run").length;
    const passed = jobs.filter((job) => job.effective_result === "passed").length;
    const summary = el("summary");
    summary.append(el("span", "", `CI jobs ${jobs.length} 項 · 未執行 ${notRun} · 通過 ${passed}`));
    if (runs.length) {
      const results = new Map();
      for (const run of runs) { const result = run.effective_result || "unknown"; results.set(result, (results.get(result) || 0) + 1); }
      const counts = [...results].map(([result, count]) => `${statusLabels[result] || result} ${count}`).join(" · ");
      summary.append(el("span", "run-summary", `Workflow ${runs.length} 次：${counts}`));
    }
    section.append(summary);
    section.append(el("p", "subtle", `CI 最近觀測：${stamp(source.ci_observed_at)} UTC。以下依有效結果列示。`));
    if (runs.length) section.append(ciRunsSection(runs));
    const list = el("ul", "audit-list");
    for (const job of jobs) {
      const item = el("li", "audit-entry");
      const meta = el("div", "audit-meta");
      meta.append(el("strong", "", text(job.name, "CI 工作")), badge(job.effective_result || "unknown"));
      item.append(meta, el("p", "", `實際 CI SHA：${text(job.sha)}`), el("p", "", `Runner：${text(job.runner_id)} · 步驟數：${Array.isArray(job.steps) ? job.steps.length : text(job.steps)}`));
      if (job.id !== undefined || job.run_id !== undefined || job.attempt !== undefined) item.append(el("p", "", `Job ID：${text(job.id)} · Workflow run：${text(job.run_id)} · 執行次數：${text(job.attempt)}`));
      item.append(el("p", "", `原始紀錄：${statusLabels[job.status] || text(job.status)} · ${statusLabels[job.conclusion] || text(job.conclusion)}；以有效判定為準。`));
      if (job.url) item.append(link(job.url, "CI 紀錄"));
      list.append(item);
    }
    section.append(list);
    return section;
  }

  function validateState(payload) {
    const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
    const optionalArray = (value, test) => value === undefined || value === null || (Array.isArray(value) && value.every(test));
    if (!object(payload) || payload.schema_version !== 1 || !Array.isArray(payload.tasks) || !Array.isArray(payload.sources) || !Array.isArray(payload.alerts) || !Array.isArray(payload.ready) || typeof payload.state_hash !== "string" || !/^[0-9a-f]{64}$/i.test(payload.state_hash)) throw new Error("API 回應不符合資料契約");
    if (!payload.tasks.every((task) => object(task) && typeof task.id === "string" && task.id && typeof task.title === "string"
      && optionalArray(task.refs, (ref) => object(ref) && typeof ref.kind === "string" && typeof ref.url === "string")
      && optionalArray(task.approval_constraints, (item) => object(item) && typeof item.action === "string" && typeof item.status === "string")
      && optionalArray(task.assignment_history, object)
      && optionalArray(task.source_provenance, object)
      && optionalArray(task.acceptance, object)
      && optionalArray(task.ci, object)
      && optionalArray(task.ci_runs, object)
      && optionalArray(task.evidence, object)
      && optionalArray(task.completed_actions, (receipt) => object(receipt) && typeof receipt.action === "string" && typeof receipt.input_pin === "string" && /^[0-9a-f]{64}$/i.test(receipt.input_pin) && typeof receipt.timestamp === "string")
      && (task.node_kind === undefined || ["work", "umbrella"].includes(task.node_kind))
      && (task.parent_id === undefined || task.parent_id === null || typeof task.parent_id === "string")
      && (task.head_alignment === undefined || ["same", "different", "unknown"].includes(task.head_alignment))
      && (task.next_action_pin === undefined || (typeof task.next_action_pin === "string" && /^[0-9a-f]{64}$/i.test(task.next_action_pin)))
      && (task.next_action_mode === undefined || Object.prototype.hasOwnProperty.call(modeLabels, task.next_action_mode))
      && (!task.pr || (object(task.pr) && optionalArray(task.pr.ci, object) && optionalArray(task.pr.ci_runs, object))))) throw new Error("API 工作資料不符合資料契約");
    if (new Set(payload.tasks.map((task) => task.id)).size !== payload.tasks.length) throw new Error("API 工作 ID 重複，未套用此回應");
    if (!payload.sources.every((source) => object(source) && typeof source.id === "string" && source.id && typeof source.kind === "string" && typeof source.status === "string" && optionalArray(source.ci, object) && optionalArray(source.ci_runs, object))) throw new Error("API 來源資料不符合資料契約");
    if (!payload.alerts.every((alert) => typeof alert === "string" || object(alert))) throw new Error("API 警示資料不符合資料契約");
    if (!payload.ready.every((entry) => typeof entry === "string" ? payload.tasks.some((task) => task.id === entry) : object(entry) && typeof entry.id === "string" && payload.tasks.some((task) => task.id === entry.id))) throw new Error("API 可接手工作缺少對應來源");
    if (payload.ready_counts !== undefined && (!object(payload.ready_counts) || !["all", "read_only", "write"].every((key) => Number.isInteger(payload.ready_counts[key]) && payload.ready_counts[key] >= 0))) throw new Error("API 操作類型計數不符合資料契約");
    if (payload.store_health !== undefined && (!object(payload.store_health) || !["ok", "invalid"].includes(payload.store_health.status))) throw new Error("API 資料健康狀態不符合資料契約");
    if (payload.coverage !== undefined && payload.store_health?.status !== "invalid") {
      const nonnegative = (value) => Number.isInteger(value) && value >= 0;
      const prLink = (value) => object(value) && typeof value.url === "string" && optionalArray(value.task_ids, (id) => typeof id === "string") && optionalArray(value.sources, object);
      const issue = (value) => object(value) && Number.isInteger(value.number) && typeof value.url === "string" && optionalArray(value.task_ids, (id) => typeof id === "string") && optionalArray(value.pr_links, prLink);
      const repository = (value) => object(value) && typeof value.repository === "string" && typeof value.source_id === "string" && optionalArray(value.issues, issue) && optionalArray(value.prs, prLink);
      const coverage = payload.coverage;
      if (!object(coverage) || !["count", "captured", "missing_scope"].every((key) => nonnegative(coverage[key])) || !optionalArray(coverage.repositories, repository) || !optionalArray(coverage.pr_repositories, repository) || !optionalArray(coverage.pr_links, prLink)) throw new Error("API 來源覆蓋資料不符合資料契約");
    }
    return payload;
  }

  async function refresh() {
    if (busy) return;
    busy = true;
    $("refresh-button").disabled = true;
    $("refresh-button").textContent = "讀取中…";
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch("/api/state", { cache: "no-store", signal: controller.signal, headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const candidate = validateState(await response.json());
      const previous = state;
      try {
        state = candidate;
        renderStoreHealth(); renderSync(); renderCoverage(); renderReady(); renderQueue(); renderAlerts(); renderSchedule(); renderSources();
      } catch (error) {
        state = previous;
        if (state) { renderStoreHealth(); renderSync(); renderCoverage(); renderReady(); renderQueue(); renderAlerts(); renderSchedule(); renderSources(); }
        throw error;
      }
      $("fetch-error").hidden = true;
      $("status-message").textContent = invalidStore() ? "資料校驗失敗，已切換唯讀診斷；停止派工／完成判定。" : `已讀取 ${state.tasks.length} 筆登記紀錄，${state.alerts.length} 項警示。`;
      document.documentElement.dataset.stateHash = state.state_hash;
      document.body.dataset.stateHash = state.state_hash;
      document.documentElement.dataset.stateLoaded = "true";
    } catch (error) {
      const reason = error?.name === "AbortError" ? "本機 API 回應逾時" : text(error?.message, "連線失敗");
      $("fetch-error").textContent = `狀態讀取失敗：${reason}。${state ? "畫面保留上次成功讀取的資料與雜湊，尚未同步本次變更。" : "尚未取得可信狀態。請確認服務已啟動，然後重新讀取。"}`;
      $("fetch-error").hidden = false;
      $("status-message").textContent = "狀態讀取失敗。";
      if (!state) {
        $("ready-list").replaceChildren(el("p", "empty", "尚未取得可核對的工作資料。"));
        $("filter-summary").textContent = "狀態未知；不推斷工作已完成。";
      }
    } finally {
      clearTimeout(timer);
      busy = false;
      $("refresh-button").disabled = false;
      $("refresh-button").textContent = "重新讀取狀態";
    }
  }

  $("refresh-button").addEventListener("click", refresh);
  $("search-input").addEventListener("input", renderQueue);
  $("status-filter").addEventListener("change", renderQueue);
  $("print-button").addEventListener("click", () => window.print());
  $("copy-hash-button").addEventListener("click", async () => {
    if (!state) return;
    try {
      await navigator.clipboard.writeText(state.state_hash);
      $("copy-hash-button").textContent = "已複製";
      $("status-message").textContent = "已複製完整狀態雜湊。";
      setTimeout(() => { $("copy-hash-button").textContent = "複製雜湊"; }, 1800);
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents($("state-hash"));
      selection.removeAllRanges(); selection.addRange(range);
      $("status-message").textContent = "無法使用剪貼簿，已選取雜湊，請複製選取文字。";
    }
  });
  refresh();
})();
