"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const executionLabels = { unknown: "待核", unassigned: "未接手", active: "執行中", stopped: "已停止・待接續", blocked: "阻塞", finished: "執行已結束" };
  const deliveryLabels = { no_pr: "尚未交 PR", awaiting_review: "待審", awaiting_integration: "待整合", verification_pending: "驗證待補", done: "已完成並整合", unknown: "待核" };
  const statusLabels = { ...executionLabels, ...deliveryLabels, approved: "已批准", granted: "已批准", required: "需要批准", pending: "待批准", denied: "未批准", held: "暫緩", hold: "暫緩", passed: "通過", pass: "通過", success: "成功", failed: "失敗", failure: "失敗", skipped: "未執行", not_run: "未執行", not_executed: "未執行", expired: "已過期", stale: "已過期", valid: "有效", invalid: "無效", merged: "已整合", error: "讀取失敗", ok: "已讀取", healthy: "已讀取", available: "可用", unavailable: "來源失聯", missing: "缺少資料", manual: "手動匯入", fetched: "已讀取", stopped: "已停止", completed: "執行已結束", cancelled: "已取消", assigned: "已派工", released: "已釋放", reserved: "曾保留", revoked: "已撤回", approved_review: "審查通過", changes_requested: "審查要求修改" };
  const actionLabels = { work: "執行工作", assign: "登記派工", assignment: "登記派工", review: "審查", merge: "合併 PR", publish: "發布", retry: "重試", execute: "執行工作", integrate: "整合", approve: "批准", verify: "補驗證", wait: "等待", reconcile: "重新核對", resume: "接續工作" };
  const severityLabels = { critical: "必須處理", error: "需處理", warning: "請留意", warn: "請留意", info: "待確認" };
  const freshnessLabels = { current: "近期快照", stale: "超過同步期限", future: "時間在未來", error: "讀取失敗", unknown: "待核" };
  const sourceKindLabels = { github: "GitHub 讀取", github_live: "GitHub 讀取", git: "Git 版本讀取", operator: "CLI 手動登記", api: "API 讀取", live: "API 讀取", manual: "手動匯入", manual_snapshot: "手動匯入快照", snapshot: "手動匯入快照", parent_snapshot: "父任務快照（手動匯入）", parent: "父任務快照（手動匯入）" };
  let state = null;
  let busy = false;
  const expanded = new Set();
  const dates = new Intl.DateTimeFormat("zh-TW", { timeZone: "UTC", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });

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
    if (["blocked", "denied", "failed", "failure", "error", "invalid", "unavailable"].includes(status)) return "red";
    if (["stopped", "no_pr", "awaiting_review", "awaiting_integration", "verification_pending", "pending", "required", "held", "hold", "expired", "stale", "future", "not_run", "not_executed", "skipped"].includes(status)) return "amber";
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
  function alertTaskId(value) { return typeof value === "object" && value ? text(value.task_id ?? value.task, "") : ""; }
  function findTask(id) { return state?.tasks.find((task) => task.id === id); }
  function readyTasks() { return array(state?.ready).map((entry) => typeof entry === "string" ? findTask(entry) : findTask(entry.id) || entry).filter(Boolean); }
  function taskAlerts(task) { return array(task.alerts); }

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

  function renderSync() {
    const kinds = new Set(array(state.sources).map((source) => source.kind));
    const hasManual = [...kinds].some((kind) => !["git", "github", "github_live", "api", "live"].includes(kind));
    $("source-mode").textContent = state.sources.length ? hasManual ? "含手動匯入快照" : "已讀取來源快照" : "尚無來源";
    $("last-synced").textContent = stamp(state.last_synced_at);
    $("sync-age").textContent = age(state.last_synced_at);
    $("generated-at").textContent = stamp(state.generated_at);
    $("state-hash").textContent = state.state_hash;
    $("copy-hash-button").disabled = false;
    $("schema-version").textContent = `資料契約版本：${text(state.schema_version)}`;
  }

  function renderReady() {
    const tasks = readyTasks();
    $("ready-count").textContent = `${tasks.length} 項`;
    const fragment = document.createDocumentFragment();
    if (!tasks.length) fragment.append(el("p", "empty", "目前沒有通過前置檢查的工作。先核對警示、依賴與批准條件。"));
    for (const task of tasks.slice(0, 3)) {
      const button = el("button", "ready-entry");
      button.type = "button";
      button.append(el("span", "task-id", task.id), el("strong", "", text(task.title, task.id)), el("p", "", actionText(task.next_action)));
      button.addEventListener("click", () => openTask(task.id));
      fragment.append(button);
    }
    if (tasks.length > 1) {
      const button = el("button", `button small ready-more${tasks.length <= 3 ? " only-mobile" : ""}`, `查看全部 ${tasks.length} 項可進行的下一步`);
      button.type = "button";
      button.addEventListener("click", () => { $("search-input").value = ""; $("status-filter").value = "ready"; renderQueue(); $("work-queue").scrollIntoView(); });
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
      if (item.validity) meta.append(badge(item.validity, { ...statusLabels, future: "時間在未來" }));
      if (item.status) meta.append(badge(item.status));
      if (item.expired === true || item.stale === true) meta.append(badge("expired"));
      meta.append(el("time", "", stamp(item.timestamp ?? item.verified_at ?? item.at)));
      entry.append(meta);
      const fields = el("ul", "plain-list");
      const sha = item.sha ?? item.head_sha ?? item.commit_sha;
      fields.append(el("li", "", `驗證 SHA：${text(sha)}`));
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
    fields.append(detailField("Pull request", link(pr.url, pr.number ? `PR #${pr.number}` : "開啟 PR")), detailField("目前 head 的審查", ({ approved: "審查通過", pending: "待審", changes_requested: "要求修改", unknown: "待核", stale: "舊 head 審查已過期" })[pr.effective_review_state] || "待核"), detailField("來源原始審查紀錄", ({ approved: "審查通過（須核對 head）", pending: "待審", changes_requested: "要求修改", unknown: "待核" })[pr.review_state] || text(pr.review_state)), detailField("PR 整合紀錄", pr.merged === true ? "已整合；工作驗收仍以交付狀態為準" : pr.merged === false ? "尚未整合" : "待核"), detailField("PR head SHA", el("code", "", text(pr.head_sha))), detailField("整合時 head SHA", el("code", "", text(pr.merged_head_sha)), true));
    section.append(fields);
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
        if (job.evaluation) item.append(el("p", "", text(job.evaluation)));
        if (job.url) item.append(link(job.url, "CI 紀錄"));
        list.append(item);
      }
      section.append(list);
    }
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
    details.append(detailField("範圍", task.scope, true), detailField("檔案範圍", listOf(task.files, "尚未登記檔案範圍", true), true), detailField("Owner thread", el("code", "", text(task.owner_thread, "未登記"))), detailField("分支", el("code", "", text(task.branch))), detailField("目前 head SHA", el("code", "", text(task.head_sha)), true), detailField("最早可開始 · UTC", task.not_before ? stamp(task.not_before) : "未定日期"), detailField("最近有效驗證 · UTC", task.last_verified_evidence?.timestamp ? stamp(task.last_verified_evidence.timestamp) : "尚無目前 head 的有效驗證紀錄"));
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
    details.append(detailField("工作依賴", dependencies), detailField("必須通過的驗收條件", acceptanceList(task), true), detailField("批准限制", approvalList(task), true), detailField("建議下一步", actionText(task.next_action), true), detailField("本工作來源與版本", provenanceList(task), true));
    if (taskAlerts(task).length) details.append(detailField("工作警示", listOf(taskAlerts(task).map(alertText)), true));
    panel.append(details);
    const pr = prSection(task);
    if (pr) panel.append(pr);
    panel.append(evidenceSection(task), historySection(task));
    return panel;
  }

  function matchesFilter(task, filter, readyIds) {
    switch (filter) {
      case "ready": return readyIds.has(task.id);
      case "attention": return taskAlerts(task).length > 0 || array(state.alerts).some((alert) => alertTaskId(alert) === task.id);
      case "review": return ["awaiting_review", "awaiting_integration"].includes(task.delivery_status);
      case "blocked": return task.execution_status === "blocked";
      case "stopped": return task.execution_status === "stopped";
      case "unknown": return !task.execution_status || task.execution_status === "unknown" || !task.delivery_status || task.delivery_status === "unknown";
      case "done": return task.delivery_status === "done";
      default: return true;
    }
  }

  function renderQueue() {
    if (!state) return;
    const query = $("search-input").value.trim().toLocaleLowerCase();
    const filter = $("status-filter").value;
    const readyIds = new Set(readyTasks().map((task) => task.id));
    const tasks = state.tasks.filter((task) => {
      const haystack = [task.id, task.title, task.branch, ...array(task.files), ...array(task.refs).map((ref) => `${ref.kind || ""} ${ref.number || ""}`)].map((value) => text(value, "")).join(" ").toLocaleLowerCase();
      return (!query || haystack.includes(query)) && matchesFilter(task, filter, readyIds);
    });
    $("task-count").textContent = String(state.tasks.length);
    $("filter-summary").textContent = `顯示 ${tasks.length} / ${state.tasks.length} 項 · 點工作名稱查看證據與派工紀錄`;
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
      work.append(title, refs(task), el("span", "detail-hint", isOpen ? "紀錄已展開" : "查看紀錄"));
      row.append(work);
      const execution = el("td");
      execution.dataset.label = "執行";
      execution.append(badge(task.execution_status || "unknown", executionLabels));
      const delivery = el("td");
      delivery.dataset.label = "交付";
      delivery.append(badge(task.delivery_status || "unknown", deliveryLabels));
      const owner = el("td");
      owner.dataset.label = "執行者／版本";
      owner.append(el("span", "owner-state", task.owner_thread ? "已登記執行者" : "尚無執行者"));
      const sha = el("code", "sha", task.head_sha ? String(task.head_sha).slice(0, 12) : "SHA 待核");
      sha.title = text(task.head_sha);
      owner.append(sha);
      const manualSources = array(task.source_provenance).filter((source) => source.kind === "manual_snapshot" && source.as_of).sort((a, b) => Date.parse(a.as_of) - Date.parse(b.as_of));
      if (manualSources.length) owner.append(el("span", "source-asof", `${manualSources.length > 1 ? "最早" : "手動"}快照 ${stamp(manualSources[0].as_of)} UTC`));
      const action = el("td", "next-action", actionText(task.next_action));
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
    const dated = state.tasks.filter((task) => task.not_before).slice().sort((a, b) => Date.parse(a.not_before) - Date.parse(b.not_before) || a.id.localeCompare(b.id));
    const undated = state.tasks.filter((task) => !task.not_before);
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
      fragment.append(entry);
    }
    if (!state.sources.length) fragment.append(el("p", "empty", "尚無已登記來源，請先匯入通過校驗的快照。"));
    $("sources-list").replaceChildren(fragment);
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
      && optionalArray(task.evidence, object)
      && (!task.pr || (object(task.pr) && optionalArray(task.pr.ci, object))))) throw new Error("API 工作資料不符合資料契約");
    if (new Set(payload.tasks.map((task) => task.id)).size !== payload.tasks.length) throw new Error("API 工作 ID 重複，未套用此回應");
    if (!payload.sources.every((source) => object(source) && typeof source.id === "string" && source.id && typeof source.kind === "string" && typeof source.status === "string")) throw new Error("API 來源資料不符合資料契約");
    if (!payload.alerts.every((alert) => typeof alert === "string" || object(alert))) throw new Error("API 警示資料不符合資料契約");
    if (!payload.ready.every((entry) => typeof entry === "string" ? payload.tasks.some((task) => task.id === entry) : object(entry) && typeof entry.id === "string" && payload.tasks.some((task) => task.id === entry.id))) throw new Error("API 可接手工作缺少對應來源");
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
        renderSync(); renderReady(); renderQueue(); renderAlerts(); renderSchedule(); renderSources();
      } catch (error) {
        state = previous;
        if (state) { renderSync(); renderReady(); renderQueue(); renderAlerts(); renderSchedule(); renderSources(); }
        throw error;
      }
      $("fetch-error").hidden = true;
      $("status-message").textContent = `已讀取 ${state.tasks.length} 項工作，${state.alerts.length} 項警示。`;
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
