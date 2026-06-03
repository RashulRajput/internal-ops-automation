const tabs = [
  ["dashboard", "Dashboard", "layout-dashboard"],
  ["tickets", "Tickets", "ticket"],
  ["leave", "Leave", "calendar"],
  ["meetings", "Meetings", "users"],
  ["documents", "Docs Q&A", "file-search"],
  ["tasks", "Tasks", "check"],
  ["reports", "Reports", "chart"]
];

let active = "dashboard";
let data = {};
let activeProvider = "Local";
let chat = [{ role: "ai", text: "Ask me about tickets, leave, meetings, tasks, or risk." }];

const q = (s, r = document) => r.querySelector(s);
const view = q("#view");
const viewTitle = q("#viewTitle");
const pageTitle = q("#pageTitle");
const toast = q("#toast");

const icons = {
  "layout-dashboard": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>',
  ticket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4Z"/><path d="M13 5v14"/></svg>',
  calendar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M8 2v4M16 2v4M3 10h18"/><rect x="3" y="4" width="18" height="18" rx="2"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  "file-search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h6"/><path d="M14 2v6h6"/><circle cx="17" cy="17" r="3"/><path d="m21 21-2-2"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m20 6-11 11-5-5"/></svg>',
  chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-7"/></svg>',
  send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 5v14M5 12h14"/></svg>',
  spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m12 3 1.9 5.7L20 11l-6.1 2.3L12 19l-1.9-5.7L4 11l6.1-2.3Z"/></svg>'
};

function icon(name) {
  return `<span class="button-icon" aria-hidden="true">${icons[name] || ""}</span>`;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, s => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[s]));
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || "Request failed");
  return body;
}

function nav() {
  q("#nav").innerHTML = tabs.map(([id, label, ic]) => `
    <button class="nav-button ${id === active ? "active" : ""}" data-tab="${id}" type="button">
      ${icons[ic]}<span>${label}</span>
    </button>
  `).join("");
}

async function load() {
  // Fetch health to detect active AI provider
  try {
    const health = await api("/health");
    activeProvider = health.ai_provider || "Local";
    const isLLM = activeProvider !== "Local";
    const statusEl = q("#apiStatus");
    const dotEl = q("#statusDot");
    const stripEl = q("#statusStrip");
    statusEl.textContent = isLLM ? `AI: ${activeProvider}` : "Local AI, no keys";
    dotEl.style.background = isLLM ? "#4fd1c5" : "#7ad66d";
    dotEl.style.boxShadow = isLLM
      ? "0 0 16px rgba(79,209,197,.8)"
      : "0 0 16px rgba(122,214,109,.8)";
    stripEl.style.borderColor = isLLM
      ? "rgba(79,209,197,.35)"
      : "rgba(122,214,109,.25)";
    stripEl.style.color = isLLM ? "#4fd1c5" : "";
    const badge = q("#agentProviderBadge");
    if (badge) badge.textContent = activeProvider;
  } catch (_) {
    activeProvider = "Local";
    q("#apiStatus").textContent = "Local AI, no keys";
  }
  data = await api("/api/summary");
  renderMetrics();
  render();
  renderAgent();
}

function renderMetrics() {
  const m = data.ticket_metrics || {};
  q("#metricTickets").textContent = m.total || 0;
  q("#metricCritical").textContent = m.critical || 0;
  q("#metricLeaves").textContent = (data.leaves || []).filter(x => x.status === "pending").length;
  q("#metricTasks").textContent = (data.tasks || []).filter(x => x.status !== "done").length;
  q("#tinyChart").innerHTML = tinyChart([m.open || 0, m.high || 0, m.critical || 0, (data.tasks || []).length, (data.meetings || []).length]);
}

function tinyChart(values) {
  const max = Math.max(1, ...values);
  const points = values.map((v, i) => `${12 + i * 36},${48 - (v / max) * 34}`).join(" ");
  return `<svg viewBox="0 0 170 58" width="170" height="58" aria-hidden="true"><polyline points="${points}" fill="none" stroke="#4fd1c5" stroke-width="3"/><path d="M0 50H170" stroke="rgba(255,255,255,.12)"/></svg>`;
}

function render() {
  nav();
  const tab = tabs.find(x => x[0] === active);
  pageTitle.textContent = tab[1] === "Docs Q&A" ? "Document Q&A" : tab[1];
  viewTitle.textContent = pageTitle.textContent;
  ({
    dashboard: renderDashboard,
    tickets: renderTickets,
    leave: renderLeave,
    meetings: renderMeetings,
    documents: renderDocuments,
    tasks: renderTasks,
    reports: renderReports
  }[active])();
}

function renderDashboard() {
  const recentTickets = (data.tickets || []).slice(0, 4);
  const actions = (data.tasks || []).filter(x => x.status !== "done").slice(0, 5);
  view.innerHTML = `
    <div class="split">
      <div class="list">
        <span class="label">Priority Stream</span>
        ${recentTickets.length ? recentTickets.map(ticketItem).join("") : empty("No tickets yet")}
      </div>
      <div class="list">
        <span class="label">Action Queue</span>
        ${actions.length ? actions.map(taskItem).join("") : empty("No open actions")}
      </div>
    </div>
  `;
}

function renderTickets() {
  view.innerHTML = `
    <div class="split">
      <form class="form" data-endpoint="/api/tickets" data-ok="Ticket classified">
        <h3>New ticket</h3>
        ${field("title", "Title", "text", true)}
        ${field("submitter_name", "Submitter", "text", true)}
        ${field("submitter_email", "Email", "email", true)}
        ${area("description", "Description", 4, true)}
        <button class="primary" type="submit">${icon("spark")}Classify ticket</button>
      </form>
      <div class="list">
        <span class="label">Tickets</span>
        ${(data.tickets || []).length ? data.tickets.map(ticketItem).join("") : empty("No tickets yet")}
      </div>
    </div>
  `;
}

function ticketItem(t) {
  return `
    <article class="item">
      <div class="item-top">
        <h3>${esc(t.title)}</h3>
        <span class="chip ${esc(t.priority)}">${esc(t.priority)}</span>
      </div>
      <p class="muted">${esc(t.ai_summary || t.description)}</p>
      <div class="chips">
        <span class="chip">${esc(t.category)}</span>
        <span class="chip ${esc(t.status)}">${esc(t.status)}</span>
        <span class="chip">${esc(t.assigned_to)}</span>
        <span class="chip">${esc(t.estimated_hours)}h</span>
      </div>
    </article>
  `;
}

function renderLeave() {
  view.innerHTML = `
    <div class="split">
      <form class="form" data-endpoint="/api/leave" data-ok="Leave request analyzed">
        <h3>Leave request</h3>
        <div class="grid2">
          ${field("employee_name", "Employee", "text", true)}
          ${field("employee_email", "Email", "email", true)}
        </div>
        <div class="grid2">
          ${field("department", "Department")}
          <label class="field"><span>Leave type</span><select name="leave_type"><option value="annual">Annual</option><option value="sick">Sick</option><option value="emergency">Emergency</option><option value="unpaid">Unpaid</option></select></label>
        </div>
        <div class="grid2">
          ${field("start_date", "Start date", "date", true)}
          ${field("end_date", "End date", "date", true)}
        </div>
        ${area("reason", "Reason", 4, true)}
        <button class="primary" type="submit">${icon("spark")}Analyze request</button>
      </form>
      <div class="list">
        <span class="label">Leave queue</span>
        ${(data.leaves || []).length ? data.leaves.map(leaveItem).join("") : empty("No leave requests")}
      </div>
    </div>
  `;
}

function leaveItem(l) {
  return `
    <article class="item">
      <div class="item-top">
        <h3>${esc(l.employee_name)}</h3>
        <span class="chip ${esc(l.ai_recommendation)}">${esc(l.ai_recommendation)}</span>
      </div>
      <p class="muted">${esc(l.ai_reasoning)}</p>
      <div class="chips">
        <span class="chip">${esc(l.leave_type)}</span>
        <span class="chip">${esc(l.total_days)} days</span>
        <span class="chip ${esc(l.status)}">${esc(l.status)}</span>
      </div>
    </article>
  `;
}

function renderMeetings() {
  view.innerHTML = `
    <div class="split">
      <form class="form" data-meeting-form>
        <h3>Meeting transcript</h3>
        ${field("title", "Title", "text", true)}
        <div class="grid2">
          ${field("date", "Date", "datetime-local")}
          ${field("duration_minutes", "Minutes", "number")}
        </div>
        ${field("participants", "Participants")}
        ${area("transcript", "Transcript", 8, true)}
        <button class="primary" type="submit">${icon("spark")}Extract summary</button>
      </form>
      <div class="list">
        <span class="label">Meetings</span>
        ${(data.meetings || []).length ? data.meetings.map(meetingItem).join("") : empty("No meetings yet")}
      </div>
    </div>
  `;
}

function meetingItem(m) {
  return `
    <article class="item">
      <div class="item-top">
        <h3>${esc(m.title)}</h3>
        <span class="chip">${esc(m.sentiment)}</span>
      </div>
      <p class="muted">${esc(m.summary)}</p>
      <div class="chips">
        <span class="chip">${(m.participants || []).length} people</span>
        <span class="chip">${(m.action_items || []).length} actions</span>
        <span class="chip">${(m.key_decisions || []).length} decisions</span>
      </div>
    </article>
  `;
}

function renderDocuments() {
  view.innerHTML = `
    <div class="split">
      <div class="form">
        <h3>Knowledge base</h3>
        <form class="doc-drop" data-endpoint="/api/documents" data-ok="Document indexed">
          ${field("name", "Document name", "text", true)}
          ${field("category", "Category")}
          ${area("content", "Paste document text", 7, true)}
          <button class="primary" type="submit">${icon("plus")}Index document</button>
        </form>
        <form class="form" data-qa-form>
          ${area("question", "Question", 3, true)}
          <button class="secondary" type="submit">${icon("file-search")}Ask documents</button>
        </form>
        <div id="qaAnswer" class="qa-answer">Indexed answers will appear here.</div>
      </div>
      <div class="list">
        <span class="label">Indexed documents</span>
        ${(data.documents || []).length ? data.documents.map(docItem).join("") : empty("No documents indexed")}
      </div>
    </div>
  `;
}

function docItem(d) {
  return `
    <article class="item">
      <div class="item-top">
        <h3>${esc(d.name)}</h3>
        <span class="chip">${esc(d.category)}</span>
      </div>
      <div class="chips">
        <span class="chip">${esc(d.file_type)}</span>
        <span class="chip">${esc(d.chunk_count)} chunks</span>
        <span class="chip">${esc(d.file_size_kb)} KB</span>
      </div>
    </article>
  `;
}

function renderTasks() {
  view.innerHTML = `
    <div class="split">
      <form class="form" data-endpoint="/api/tasks" data-ok="Task added">
        <h3>New task</h3>
        ${field("title", "Title", "text", true)}
        <div class="grid2">
          ${field("owner", "Owner")}
          <label class="field"><span>Priority</span><select name="priority"><option>low</option><option selected>medium</option><option>high</option><option>critical</option></select></label>
        </div>
        ${field("due_date", "Due date")}
        <button class="primary" type="submit">${icon("plus")}Add task</button>
      </form>
      <div class="list">
        <span class="label">Task board</span>
        ${(data.tasks || []).length ? data.tasks.map(taskItem).join("") : empty("No tasks yet")}
      </div>
    </div>
  `;
}

function taskItem(t) {
  return `
    <article class="item">
      <div class="item-top">
        <h3>${esc(t.title)}</h3>
        <span class="chip ${esc(t.status)}">${esc(t.status)}</span>
      </div>
      <div class="chips">
        <span class="chip">${esc(t.owner || "Unassigned")}</span>
        <span class="chip ${esc(t.priority)}">${esc(t.priority)}</span>
        <span class="chip">${esc(t.due_date || "open")}</span>
        <span class="chip">${esc(t.source)}</span>
      </div>
    </article>
  `;
}

function renderReports() {
  view.innerHTML = `
    <div class="form">
      <div class="toolbar">
        <button class="primary" id="reportButton" type="button">${icon("chart")}Generate daily report</button>
      </div>
      <div id="reportBox" class="report-box">No report generated in this session.</div>
    </div>
  `;
  q("#reportButton").addEventListener("click", async () => {
    const result = await api("/api/reports/daily");
    q("#reportBox").textContent = `${result.date}\n\n${result.report}`;
  });
}

function field(name, label, type = "text", required = false) {
  return `<label class="field"><span>${label}</span><input name="${name}" type="${type}" ${required ? "required" : ""}></label>`;
}

function area(name, label, rows = 4, required = false) {
  return `<label class="field"><span>${label}</span><textarea name="${name}" rows="${rows}" ${required ? "required" : ""}></textarea></label>`;
}

function empty(text) {
  return `<div class="empty">${esc(text)}</div>`;
}

function formBody(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function submitForm(path, ok) {
  return async e => {
    e.preventDefault();
    const button = e.submitter;
    button.disabled = true;
    try {
      await api(path, { method: "POST", body: JSON.stringify(formBody(e.currentTarget)) });
      e.currentTarget.reset();
      flash(ok);
      await load();
    } catch (err) {
      flash(err.message);
    } finally {
      button.disabled = false;
    }
  };
}

function renderAgent() {
  q("#agentLog").innerHTML = chat.map(m => `<div class="bubble ${m.role === "user" ? "user" : ""}"><span class="bubble-role">${m.role === "user" ? "You" : (data.provider || "OpsPilot")}</span>${esc(m.text)}</div>`).join("");
  q("#agentForm button").innerHTML = icons.send;
  const log = q("#agentLog");
  if (log) log.scrollTop = log.scrollHeight;
}

document.addEventListener("click", async e => {
  const tabButton = e.target.closest("button[data-tab]");
  if (tabButton) {
    active = tabButton.dataset.tab;
    render();
    return;
  }
  const action = e.target.closest("button[data-action]");
  if (!action) return;
  if (action.dataset.action === "seed") {
    action.disabled = true;
    try {
      await api("/api/demo/seed", { method: "POST", body: "{}" });
      flash("Demo data ready");
      await load();
    } catch (err) {
      flash(err.message);
    } finally {
      action.disabled = false;
    }
  }
});

document.addEventListener("submit", async e => {
  const endpointForm = e.target.closest("form[data-endpoint]");
  if (endpointForm) {
    await submitForm(endpointForm.dataset.endpoint, endpointForm.dataset.ok)(e);
    return;
  }
  const meetingForm = e.target.closest("form[data-meeting-form]");
  if (meetingForm) {
    e.preventDefault();
    const button = e.submitter;
    button.disabled = true;
    try {
      const body = formBody(meetingForm);
      body.participants = body.participants.split(",").map(x => x.trim()).filter(Boolean);
      body.duration_minutes = Number(body.duration_minutes || 0);
      await api("/api/meetings", { method: "POST", body: JSON.stringify(body) });
      meetingForm.reset();
      flash("Meeting analyzed");
      await load();
    } catch (err) {
      flash(err.message);
    } finally {
      button.disabled = false;
    }
    return;
  }
  const qaForm = e.target.closest("form[data-qa-form]");
  if (qaForm) {
    e.preventDefault();
    const button = e.submitter;
    button.disabled = true;
    try {
      const body = formBody(qaForm);
      const answer = await api("/api/documents/query", { method: "POST", body: JSON.stringify(body) });
      q("#qaAnswer").innerHTML = `<strong>Answer</strong><br>${esc(answer.answer)}<br><br><span class="mini">${esc((answer.sources || []).map(x => x.source).join(", ") || "No source match")}</span>`;
    } catch (err) {
      flash(err.message);
    } finally {
      button.disabled = false;
    }
  }
});

q("#agentForm").addEventListener("submit", async e => {
  e.preventDefault();
  const input = q("#agentInput");
  const message = input.value.trim();
  if (!message) return;
  chat.push({ role: "user", text: message });
  input.value = "";
  renderAgent();
  try {
    const res = await api("/api/agent/chat", { method: "POST", body: JSON.stringify({ message }) });
    chat.push({ role: "ai", text: res.response });
  } catch (err) {
    chat.push({ role: "ai", text: err.message });
  }
  renderAgent();
});

function flash(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(flash.timer);
  flash.timer = setTimeout(() => toast.classList.remove("show"), 2800);
}

load().catch(err => {
  q("#apiStatus").textContent = "Server offline";
  view.innerHTML = `<div class="empty">Run the app with python -m app.main, then open http://127.0.0.1:8000</div>`;
  flash(err.message);
});
