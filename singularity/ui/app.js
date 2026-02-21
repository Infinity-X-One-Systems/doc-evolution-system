/**
 * app.js — Singularity Prime Enterprise Dashboard
 *
 * Loads JSON data files from the same origin (GitHub Pages),
 * renders all dashboard panels, and powers the admin controls.
 *
 * All network requests use relative paths so the dashboard works
 * on any GitHub Pages deployment without configuration.
 */

"use strict";

// ─── Data paths (relative to Pages root) ───────────────────────────────────
const PATHS = {
  state:      "../singularity/_STATE/state.json",
  history:    "../singularity/_STATE/history.json",
  transitions:"../singularity/_STATE/transitions.json",
  roadmap:    "../singularity/blueprint/roadmap.json",
  validation: "../singularity/evolution/validation_report.json",
  checklist:  "../singularity/evolution/checklist.json",
  tech:       "../singularity/evolution/tech_registry.json",
  memory:     "../singularity/evolution/memory_registry.json",
};

// ─── Utility ────────────────────────────────────────────────────────────────

async function fetchJSON(path) {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[sp-dashboard] Could not load ${path}:`, err.message);
    return null;
  }
}

function el(id) { return document.getElementById(id); }

function statusBadge(status) {
  const map = {
    pass: '<span class="sp-badge sp-badge--pass">✓ pass</span>',
    fail: '<span class="sp-badge sp-badge--fail">✗ fail</span>',
    unknown: '<span class="sp-badge sp-badge--neutral">— unknown</span>',
    completed: '<span class="sp-badge sp-badge--pass">completed</span>',
    in_progress: '<span class="sp-badge sp-badge--warning">in progress</span>',
    planned: '<span class="sp-badge sp-badge--neutral">planned</span>',
  };
  // Fallback to a safe, known status to avoid reflecting arbitrary text into HTML.
  const safeStatus = Object.prototype.hasOwnProperty.call(map, status) ? status : "unknown";
  return map[safeStatus];
}

// ─── Tab navigation ─────────────────────────────────────────────────────────

document.querySelectorAll(".sp-nav__tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".sp-nav__tab").forEach(b => b.classList.remove("sp-nav__tab--active"));
    document.querySelectorAll(".sp-tab").forEach(s => s.classList.remove("sp-tab--active"));
    btn.classList.add("sp-nav__tab--active");
    el(`tab-${btn.dataset.tab}`).classList.add("sp-tab--active");
  });
});

// ─── Render functions ───────────────────────────────────────────────────────

function renderOverview(state, validation, checklist, tech) {
  el("sp-state-badge").textContent = state?.current ?? "—";
  el("sp-version-badge").textContent = `v${state?.version ?? "0.0.0"}`;
  el("ov-state").textContent    = state?.current  ?? "—";
  el("ov-next").textContent     = state?.next     || "—";
  el("ov-version").textContent  = state?.version  ?? "—";

  const overall = validation?.overall ?? "pending";
  el("ov-validation").innerHTML = statusBadge(overall === "pending" ? "unknown" : overall);

  if (checklist?.items) {
    const done  = checklist.items.filter(i => i.completed).length;
    const total = checklist.items.length;
    el("ov-checklist").textContent = `${done} / ${total}`;
  }

  el("ov-tech").textContent = tech?.technologies?.length ?? 0;
}

function renderRoadmap(roadmap) {
  const container = el("roadmap-container");
  if (!roadmap?.milestones) { container.textContent = "No roadmap data."; return; }

  container.innerHTML = roadmap.milestones.map(m => `
    <div class="sp-milestone sp-milestone--${m.status}">
      <div class="sp-milestone__header">
        <span class="sp-milestone__id">${m.id}</span>
        <span class="sp-milestone__title">${m.title}</span>
        ${statusBadge(m.status)}
        <span class="sp-milestone__date">${m.target_date ?? ""}</span>
      </div>
      <ul class="sp-milestone__deliverables">
        ${(m.deliverables ?? []).map(d => `<li>${d}</li>`).join("")}
      </ul>
    </div>
  `).join("");
}

function renderValidation(report) {
  const tbody = el("validation-body");
  if (!report?.checks) { tbody.innerHTML = "<tr><td colspan='4'>No data.</td></tr>"; return; }

  tbody.innerHTML = Object.entries(report.checks).map(([name, v]) => `
    <tr>
      <td><code>${name}</code></td>
      <td>${statusBadge(v.status ?? "unknown")}</td>
      <td>${v.last_run ? new Date(v.last_run).toLocaleString() : "—"}</td>
      <td>${v.result ?? "—"}</td>
    </tr>
  `).join("");

  el("validation-ts").textContent = report.generated_at
    ? new Date(report.generated_at).toLocaleString() : "—";
}

function renderChecklist(checklist) {
  const container = el("checklist-container");
  if (!checklist?.items) { container.textContent = "No checklist data."; return; }

  const byCategory = {};
  checklist.items.forEach(item => {
    (byCategory[item.category] = byCategory[item.category] || []).push(item);
  });

  container.innerHTML = Object.entries(byCategory).map(([cat, items]) => `
    <div class="sp-checklist-group">
      <h3 class="sp-checklist-group__title">${cat}</h3>
      ${items.map(item => `
        <label class="sp-checklist-item ${item.completed ? "sp-checklist-item--done" : ""}">
          <input type="checkbox" ${item.completed ? "checked" : ""} disabled />
          <span>${item.title}</span>
          ${item.required ? '<span class="sp-badge sp-badge--required">required</span>' : ""}
        </label>
      `).join("")}
    </div>
  `).join("");
}

function renderTech(tech) {
  const tbody = el("tech-body");
  if (!tech?.technologies?.length) {
    tbody.innerHTML = "<tr><td colspan='4'>No technologies detected yet.</td></tr>";
    return;
  }
  tbody.innerHTML = tech.technologies.map(t => `
    <tr>
      <td><strong>${t.name}</strong></td>
      <td>${t.category}</td>
      <td><code>${t.detected_via}</code></td>
      <td>${t.file_count}</td>
    </tr>
  `).join("");
}

function renderMemory(memory) {
  const tbody = el("memory-body");
  if (!memory?.entries?.length) {
    tbody.innerHTML = "<tr><td colspan='4'>No memory entries yet.</td></tr>";
    return;
  }
  tbody.innerHTML = [...memory.entries].reverse().map(e => `
    <tr>
      <td>${e.timestamp ? new Date(e.timestamp).toLocaleString() : "—"}</td>
      <td>${e.event ?? "—"}</td>
      <td>${statusBadge(e.overall ?? "unknown")}</td>
      <td><code>${JSON.stringify(e.checks ?? {})}</code></td>
    </tr>
  `).join("");
}

function renderStateHistory(history, transitions) {
  const tbody = el("history-body");
  if (!history?.transitions?.length) {
    tbody.innerHTML = "<tr><td colspan='3'>No transitions recorded yet.</td></tr>";
  } else {
    tbody.innerHTML = [...history.transitions].reverse().map(t => `
      <tr>
        <td><code>${t.from}</code></td>
        <td><code>${t.to}</code></td>
        <td>${t.timestamp ? new Date(t.timestamp).toLocaleString() : "—"}</td>
      </tr>
    `).join("");
  }

  // State diagram
  const diagram = el("state-diagram");
  if (transitions?.allowed) {
    diagram.innerHTML = Object.entries(transitions.allowed).map(([from, tos]) =>
      `<div class="sp-state-node">
        <span class="sp-state-label">${from}</span>
        <span class="sp-state-arrow">→</span>
        <span class="sp-state-label sp-state-label--next">${tos.join(", ")}</span>
      </div>`
    ).join("");
  }
}

// ─── Admin controls ──────────────────────────────────────────────────────────

// In-memory state store for local preview
const localStore = {};

el("form-add-milestone").addEventListener("submit", e => {
  e.preventDefault();
  const title = el("ms-title").value.trim();
  const date  = el("ms-date").value.trim();
  const status = el("ms-status").value;
  if (!title) return;


  const milestoneEl = document.createElement("div");
  milestoneEl.classList.add("sp-milestone", `sp-milestone--${status}`);

  const headerEl = document.createElement("div");
  headerEl.classList.add("sp-milestone__header");

  const idSpan = document.createElement("span");
  idSpan.classList.add("sp-milestone__id");
  idSpan.textContent = id;
  headerEl.appendChild(idSpan);

  const titleSpan = document.createElement("span");
  titleSpan.classList.add("sp-milestone__title");
  titleSpan.textContent = title;
  headerEl.appendChild(titleSpan);

  const statusContainer = document.createElement("span");
  statusContainer.innerHTML = statusBadge(status);
  if (statusContainer.firstElementChild) {
    headerEl.appendChild(statusContainer.firstElementChild);
  } else {
    headerEl.appendChild(statusContainer);
  }

  const dateSpan = document.createElement("span");
  dateSpan.classList.add("sp-milestone__date");
  dateSpan.textContent = date;
  headerEl.appendChild(dateSpan);

  milestoneEl.appendChild(headerEl);
  roadmapEl.appendChild(milestoneEl);

    </div>
  `);
  el("ms-title").value = "";
  showAdminResult("Milestone added to local preview. Commit roadmap.json to persist.");
});

el("form-move-state").addEventListener("submit", e => {
  e.preventDefault();
  const current = el("admin-current-state").value;
  const next    = el("admin-next-state").value;
  el("ov-state").textContent  = current;
  el("ov-next").textContent   = next || "—";
  el("sp-state-badge").textContent = current;
  showAdminResult(`State moved to ${current} → ${next || "(none)"} in local preview.`);
});

el("form-edit-milestone").addEventListener("submit", e => {
  e.preventDefault();
  const id     = el("edit-ms-id").value.trim();
  const status = el("edit-ms-status").value;
  const nodes  = document.querySelectorAll(".sp-milestone__id");
  let found    = false;
  nodes.forEach(node => {
    if (node.textContent === id) {
      const card = node.closest(".sp-milestone");
      card.className = `sp-milestone sp-milestone--${status}`;
      const badgeEl = card.querySelector(".sp-badge:not(.sp-milestone__id)");
      if (badgeEl) badgeEl.outerHTML = statusBadge(status);
      found = true;
    }
  });
  showAdminResult(found
    ? `Milestone ${id} updated to '${status}' in local preview.`
    : `Milestone ${id} not found.`);
});

function triggerAction(action) {
  const messages = {
    rebuild:    "Rebuild triggered (submit a PR to run CI).",
    revalidate: "Re-validation triggered (run evolution_engine.py locally).",
    chaos:      "Chaos test triggered (run chaos.yml workflow manually).",
  };
  showAdminResult(messages[action] ?? "Action dispatched.");
}

function showAdminResult(msg) {
  const r = el("admin-action-result");
  r.textContent = msg;
  r.classList.add("sp-admin-result--visible");
  setTimeout(() => r.classList.remove("sp-admin-result--visible"), 5000);
}

// ─── Footer timestamp ───────────────────────────────────────────────────────

el("footer-ts").textContent = new Date().toLocaleString();

// ─── Bootstrap ──────────────────────────────────────────────────────────────

async function init() {
  const [state, history, transitions, roadmap, validation, checklist, tech, memory] =
    await Promise.all([
      fetchJSON(PATHS.state),
      fetchJSON(PATHS.history),
      fetchJSON(PATHS.transitions),
      fetchJSON(PATHS.roadmap),
      fetchJSON(PATHS.validation),
      fetchJSON(PATHS.checklist),
      fetchJSON(PATHS.tech),
      fetchJSON(PATHS.memory),
    ]);

  renderOverview(state, validation, checklist, tech);
  renderRoadmap(roadmap);
  renderValidation(validation);
  renderChecklist(checklist);
  renderTech(tech);
  renderMemory(memory);
  renderStateHistory(history, transitions);
}

init().catch(err => console.error("[sp-dashboard] Init error:", err));
