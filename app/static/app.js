let scenarios = [];
let currentScenario = null;
let sessionId = null;
let capturedFlags = new Set();

const el = (id) => document.getElementById(id);

async function init() {
  const res = await fetch("/api/scenarios");
  scenarios = await res.json();
  el("flag-total").textContent = scenarios.length;
  renderScenarioList();
  loadProviderBadge();
}

async function loadProviderBadge() {
  try {
    const res = await fetch("/api/provider");
    const data = await res.json();
    el("provider-text").textContent = "Running on: " + data.description;
    const dot = document.querySelector(".provider-dot");
    if (data.description.toLowerCase().includes("unknown")) dot.classList.add("error");
  } catch (e) {
    el("provider-text").textContent = "Backend status unknown";
    document.querySelector(".provider-dot").classList.add("error");
  }
}

function renderScenarioList() {
  const list = el("scenario-list");
  list.innerHTML = "";
  scenarios.forEach((s) => {
    const card = document.createElement("div");
    card.className = "scenario-card" + (currentScenario && currentScenario.id === s.id ? " active" : "");
    card.onclick = () => selectScenario(s.id);
    card.innerHTML = `
      <div class="scenario-card-top">
        <span class="scenario-card-id">${s.owasp_id}</span>
        <span class="scenario-card-flag">${capturedFlags.has(s.id) ? "🚩" : ""}</span>
      </div>
      <div class="scenario-card-title">${s.title}</div>
      <div class="scenario-card-tagline">${s.tagline}</div>
    `;
    list.appendChild(card);
  });
}

function updateProgress() {
  el("flag-count").textContent = capturedFlags.size;
  const pct = scenarios.length ? (capturedFlags.size / scenarios.length) * 100 : 0;
  el("progress-fill").style.width = pct + "%";
}

function selectScenario(id) {
  currentScenario = scenarios.find((s) => s.id === id);
  sessionId = null;

  el("empty-state").classList.add("hidden");
  el("scenario-view").classList.remove("hidden");

  el("owasp-chip").textContent = currentScenario.owasp_id;
  el("scenario-title").textContent = currentScenario.title;
  el("scenario-tagline").textContent = currentScenario.tagline;
  el("difficulty-chip").textContent = currentScenario.difficulty;

  el("tab-objective").innerHTML = marked.parse(currentScenario.objective_md);
  el("tab-hints").innerHTML = marked.parse(currentScenario.hints_md);

  const fixLocked = !capturedFlags.has(id);
  el("fix-locked").classList.toggle("hidden", !fixLocked);
  el("fix-content").classList.toggle("hidden", fixLocked);
  el("fix-content").innerHTML = marked.parse(currentScenario.fix_md);

  el("chat-log").innerHTML = "";
  el("tool-log").innerHTML = '<p class="muted">No tool calls yet this session.</p>';
  el("flag-banner").classList.add("hidden");
  switchTab("objective");

  addSystemMsg(`Session started for ${currentScenario.title}. Say hello to begin.`);
  renderScenarioList();
}

function addUserMsg(text) {
  const div = document.createElement("div");
  div.className = "msg msg-user";
  div.textContent = text;
  el("chat-log").appendChild(div);
  el("chat-log").scrollTop = el("chat-log").scrollHeight;
}

function addAgentMsg(text) {
  const div = document.createElement("div");
  div.className = "msg msg-agent";
  div.textContent = text;
  el("chat-log").appendChild(div);
  el("chat-log").scrollTop = el("chat-log").scrollHeight;
}

function addSystemMsg(text) {
  const div = document.createElement("div");
  div.className = "msg msg-system";
  div.textContent = text;
  el("chat-log").appendChild(div);
  el("chat-log").scrollTop = el("chat-log").scrollHeight;
}

function addThinkingMsg() {
  const div = document.createElement("div");
  div.className = "msg msg-agent msg-thinking";
  div.textContent = "Agent is thinking…";
  el("chat-log").appendChild(div);
  el("chat-log").scrollTop = el("chat-log").scrollHeight;

  const timers = [
    setTimeout(() => { if (div.isConnected) div.textContent = "Still thinking… (local models can take a while, especially loading for the first time)"; }, 8000),
    setTimeout(() => { if (div.isConnected) div.textContent = "Still waiting on the model… first-time load of a large local model can take several minutes on CPU. Check your terminal's `docker compose logs ollama` if this goes past ~5 minutes."; }, 30000),
  ];
  const originalRemove = div.remove.bind(div);
  div.remove = () => { timers.forEach(clearTimeout); originalRemove(); };
  return div;
}

function renderToolCalls(toolCalls) {
  if (!toolCalls || toolCalls.length === 0) return;
  const log = el("tool-log");
  if (log.querySelector(".muted")) log.innerHTML = "";
  toolCalls.forEach((tc) => {
    const div = document.createElement("div");
    div.className = "tool-call";
    div.innerHTML = `
      <div class="tool-call-name">${tc.name}(${JSON.stringify(tc.input)})</div>
      <div class="tool-call-field">→ output</div>
      <div class="tool-call-value">${escapeHtml(tc.output)}</div>
    `;
    log.appendChild(div);
  });
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function switchTab(name) {
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".tab-content").forEach((c) => c.classList.toggle("active", c.id === "tab-" + name));
}

document.addEventListener("click", (e) => {
  if (e.target.matches(".tab-btn")) switchTab(e.target.dataset.tab);
});

el("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = el("chat-input");
  const message = input.value.trim();
  if (!message || !currentScenario) return;
  input.value = "";
  addUserMsg(message);

  const sendBtn = e.target.querySelector("button");
  sendBtn.disabled = true;

  const thinkingMsg = addThinkingMsg();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, scenario_id: currentScenario.id, message }),
    });
    const data = await res.json();
    sessionId = data.session_id;

    thinkingMsg.remove();
    addAgentMsg(data.reply || "[no reply]");
    renderToolCalls(data.tool_calls);

    if (data.flag) {
      capturedFlags.add(currentScenario.id);
      el("flag-banner").classList.remove("hidden");
      el("flag-text").textContent = `Flag captured: ${data.flag}`;
      el("fix-locked").classList.add("hidden");
      el("fix-content").classList.remove("hidden");
      el("fix-content").innerHTML = marked.parse(currentScenario.fix_md);
      updateProgress();
      renderScenarioList();
    }
    if (data.hit_turn_limit) {
      addSystemMsg("(hit max tool-call turns for this message — the agent may have been looping)");
    }
  } catch (err) {
    thinkingMsg.remove();
    addSystemMsg("Error talking to the agent: " + err.message);
  } finally {
    sendBtn.disabled = false;
  }
});

el("reset-btn").addEventListener("click", async () => {
  if (!currentScenario || !sessionId) {
    selectScenario(currentScenario.id);
    return;
  }
  await fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, scenario_id: currentScenario.id }),
  });
  capturedFlags.delete(currentScenario.id);
  updateProgress();
  selectScenario(currentScenario.id);
});

init();
