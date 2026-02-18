/* ═══════════════════════════════════════════════════════
   AdaptiveRAG · app.js
   Handles: tab nav, URL management, ingest pipeline,
            agentic query, trace rendering, logs
═══════════════════════════════════════════════════════ */

// ── Config ──────────────────────────────────────────────────
const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : window.location.origin; // ← update to your FastAPI base URL

const ENDPOINTS = {
  ingest: `${API_BASE}/save-data-vectordb`,
  query:  `${API_BASE}/agentic-query`,
};

// ── DOM refs ─────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Tab navigation ──────────────────────────────────────────
document.querySelectorAll(".nav-pill").forEach(btn => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll(".nav-pill").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    $(`tab-${tab}`).classList.add("active");
  });
});

// ── API status ping ──────────────────────────────────────────
async function checkApiStatus() {
  const dot  = document.querySelector(".status-dot");
  const text = $("api-status-text");
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      dot.className = "status-dot online";
      text.textContent = "API Online";
    } else { throw new Error(); }
  } catch {
    dot.className = "status-dot offline";
    text.textContent = "API Offline";
  }
}
checkApiStatus();
setInterval(checkApiStatus, 15000);

// ── URL management ───────────────────────────────────────────
const urlList = $("url-list");

function addUrlRow(value = "") {
  const row = document.createElement("div");
  row.className = "url-row";
  row.innerHTML = `
    <input type="url" class="url-input" placeholder="https://example.com/document" value="${value}" />
    <button class="remove-url-btn" title="Remove">×</button>
  `;
  row.querySelector(".remove-url-btn").addEventListener("click", () => {
    row.style.opacity = "0";
    row.style.transition = "opacity 0.2s";
    setTimeout(() => row.remove(), 200);
  });
  urlList.appendChild(row);
}

// Start with one empty row
addUrlRow();
$("add-url-btn").addEventListener("click", () => addUrlRow());

function getUrls() {
  return Array.from(urlList.querySelectorAll(".url-input"))
    .map(i => i.value.trim())
    .filter(Boolean);
}

// ── Pipeline step helpers ────────────────────────────────────
const STEPS = ["fetch", "chunk", "embed", "index"];
const STEP_MSGS = {
  fetch:  { running: "Fetching…",    done: "Fetched",     error: "Fetch failed" },
  chunk:  { running: "Splitting…",   done: "Chunked",     error: "Split failed" },
  embed:  { running: "Embedding…",   done: "Embedded",    error: "Embed failed" },
  index:  { running: "Indexing…",    done: "Indexed ✓",  error: "Index failed" },
};

function setStep(step, state) {
  const el = document.querySelector(`.pipe-step[data-step="${step}"]`);
  if (!el) return;
  el.className = `pipe-step ${state}`;
  const stateEl = el.querySelector(".pipe-state");
  if (state === "running") stateEl.textContent = STEP_MSGS[step].running;
  else if (state === "done") stateEl.textContent = STEP_MSGS[step].done;
  else if (state === "error") stateEl.textContent = STEP_MSGS[step].error;
  else stateEl.textContent = "—";
}

function resetSteps() {
  STEPS.forEach(s => setStep(s, "idle"));
  const res = $("ingest-result");
  res.style.display = "none";
}

async function animateSteps(delayMs = 600) {
  for (const step of STEPS) {
    setStep(step, "running");
    await sleep(delayMs);
    setStep(step, "done");
  }
}

// ── Ingest handler ───────────────────────────────────────────
$("ingest-btn").addEventListener("click", async () => {
  const urls = getUrls();
  if (!urls.length) { toast("Add at least one URL", "error"); return; }

  const btn    = $("ingest-btn");
  const loader = $("ingest-loader");

  btn.disabled = true;
  loader.classList.add("active");
  resetSteps();

  addLog("info", `Ingestion started — ${urls.length} URL(s)`);

  try {
    // Animate steps optimistically while waiting for server
    const stepAnimation = animateSteps(700);

    const res = await fetch(ENDPOINTS.ingest, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        urls,
        chunk_size:    parseInt($("chunk-size").value)   || 500,
        chunk_overlap: parseInt($("chunk-overlap").value) || 50,
        db_path:       $("db-path").value || undefined,
      }),
    });

    await stepAnimation;

    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

    const result = $("ingest-result");
    result.style.display = "flex";
    $("ingest-result-text").textContent =
      `${urls.length} document(s) vectorised and stored successfully.`;

    addLog("success", `Vector store updated — ${urls.length} source(s) indexed`);
    toast("Documents ingested successfully!", "success");

  } catch (err) {
    STEPS.forEach(s => setStep(s, "idle"));
    const failStep = STEPS.find(s =>
      document.querySelector(`.pipe-step[data-step="${s}"]`)?.classList.contains("running")
    ) || "fetch";
    setStep(failStep, "error");
    addLog("error", `Ingestion failed: ${err.message}`);
    toast("Ingestion failed — check logs", "error");
  } finally {
    btn.disabled = false;
    loader.classList.remove("active");
  }
});

// ── Query handler ────────────────────────────────────────────
$("query-btn").addEventListener("click", runQuery);
$("question-input").addEventListener("keydown", e => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) runQuery();
});

$("clear-btn").addEventListener("click", () => {
  $("question-input").value = "";
  $("answer-card").style.display = "none";
  $("error-card").style.display  = "none";
  clearTrace();
  $("state-pre").textContent = "// No state yet";
});

async function runQuery() {
  const question = $("question-input").value.trim();
  if (!question) { toast("Enter a question first", "error"); return; }

  const btn    = $("query-btn");
  const loader = $("query-loader");

  btn.disabled = true;
  loader.classList.add("active");
  $("answer-card").style.display = "none";
  $("error-card").style.display  = "none";
  clearTrace();
  $("state-pre").textContent = "// Waiting for response…";

  addLog("info", `Query: "${question.slice(0, 80)}${question.length > 80 ? "…" : ""}"`);
  addTraceEvent("routing", "running", "Routing query through agent graph…");

  try {
    const start = Date.now();

    const res = await fetch(ENDPOINTS.query, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

    const json  = await res.json();
    const state = json.data || json;
    const elapsed = ((Date.now() - start) / 1000).toFixed(2);

    renderAnswer(state, elapsed);
    renderTrace(state);
    renderState(state);

    addLog("success", `Answer generated in ${elapsed}s`);
    toast("Query complete", "success");

  } catch (err) {
    addTraceEvent("error", "error", err.message);
    $("error-card").style.display = "flex";
    $("error-message").textContent = err.message;
    addLog("error", `Query failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    loader.classList.remove("active");
  }
}

// ── Render helpers ───────────────────────────────────────────

function renderAnswer(state, elapsed) {
  const card = $("answer-card");
  card.style.display = "block";

  // Try common state keys
  const text = state.generation || state.answer || state.output || state.result ||
    (typeof state === "string" ? state : JSON.stringify(state, null, 2));

  $("answer-body").textContent = text;
  $("answer-meta").textContent = `${elapsed}s`;

  // Sources
  const sources = state.documents || state.sources || [];
  const srcEl = $("answer-sources");
  srcEl.innerHTML = "";
  sources.forEach(doc => {
    const url = doc?.metadata?.source || doc?.source || doc;
    if (url) {
      const chip = document.createElement("span");
      chip.className = "source-chip";
      chip.textContent = url;
      chip.title = url;
      srcEl.appendChild(chip);
    }
  });
}

function renderTrace(state) {
  clearTrace();
  const nodes = inferNodeTrace(state);
  nodes.forEach(({ node, status, detail }) => {
    addTraceEvent(node, status, detail);
  });
}

function inferNodeTrace(state) {
  // Build a plausible trace from state keys — adapt to your graph's node names
  const events = [];
  const keys = Object.keys(state);

  if (keys.includes("question"))
    events.push({ node: "retrieve", status: "success", detail: "Retrieved documents from VectorDB" });
  if (keys.includes("documents"))
    events.push({ node: "grade_documents", status: "success", detail: `${(state.documents||[]).length} doc(s) graded` });
  if (state.web_search === "Yes" || state.web_search_needed)
    events.push({ node: "web_search", status: "success", detail: "Supplementary web search performed" });
  if (state.need_rewrite || state.rewritten_question)
    events.push({ node: "rewrite_query", status: "success", detail: "Query rewritten for better retrieval" });
  if (keys.includes("generation") || keys.includes("answer"))
    events.push({ node: "generate", status: "success", detail: "Answer synthesised by LLM" });
  if (!events.length)
    events.push({ node: "complete", status: "success", detail: "Graph execution complete" });

  return events;
}

function clearTrace() {
  const tl = $("trace-timeline");
  tl.innerHTML = `
    <div class="trace-empty">
      <span class="trace-empty-icon">◎</span>
      <span>Graph trace will appear here</span>
    </div>`;
}

function addTraceEvent(node, status, detail) {
  const tl = $("trace-timeline");
  const empty = tl.querySelector(".trace-empty");
  if (empty) empty.remove();

  const now = new Date();
  const ts  = `${now.getHours().toString().padStart(2,"0")}:${now.getMinutes().toString().padStart(2,"0")}:${now.getSeconds().toString().padStart(2,"0")}`;

  const el = document.createElement("div");
  el.className = "trace-event";
  el.innerHTML = `
    <div class="trace-dot ${status}"></div>
    <div class="trace-content">
      <span class="trace-node">${node}</span>
      <span class="trace-msg">${detail}</span>
    </div>
    <span class="trace-time">${ts}</span>
  `;
  tl.appendChild(el);
  tl.scrollTop = tl.scrollHeight;
}

function renderState(state) {
  $("state-pre").innerHTML = syntaxHighlight(JSON.stringify(state, null, 2));
}

function syntaxHighlight(json) {
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    match => {
      if (/^"/.test(match)) {
        if (/:$/.test(match)) return `<span class="key">${match}</span>`;
        return `<span class="str">${match}</span>`;
      }
      if (/true|false/.test(match)) return `<span class="bool">${match}</span>`;
      return `<span class="num">${match}</span>`;
    }
  );
}

// ── Logs ─────────────────────────────────────────────────────
let activeFilter = "all";
const logEntries = [];

$("clear-logs-btn").addEventListener("click", () => {
  logEntries.length = 0;
  const stream = $("log-stream");
  stream.innerHTML = `<div class="log-welcome"><span class="mono">[system] Log cleared.</span></div>`;
});

document.querySelectorAll(".log-filter").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".log-filter").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeFilter = btn.dataset.level;
    renderLogs();
  });
});

function addLog(level, message) {
  const now = new Date();
  const ts  = `${now.getHours().toString().padStart(2,"0")}:${now.getMinutes().toString().padStart(2,"0")}:${now.getSeconds().toString().padStart(2,"0")}`;
  logEntries.push({ level, message, ts });
  renderLogs();
}

function renderLogs() {
  const stream  = $("log-stream");
  const visible = activeFilter === "all" ? logEntries : logEntries.filter(e => e.level === activeFilter);
  stream.innerHTML = visible.map(e => `
    <div class="log-entry">
      <span class="log-ts">${e.ts}</span>
      <span class="log-lvl ${e.level}">${e.level.toUpperCase()}</span>
      <span class="log-msg">${e.message}</span>
    </div>
  `).join("") || `<div class="log-welcome"><span class="mono">// No ${activeFilter} entries yet.</span></div>`;
  stream.scrollTop = stream.scrollHeight;
}

// ── Toast ────────────────────────────────────────────────────
function toast(message, type = "info") {
  const icons = { success: "✓", error: "⚠", info: "◈" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type] || "◈"}</span>${message}`;
  $("toast-container").appendChild(el);
  setTimeout(() => {
    el.classList.add("toast-exit");
    setTimeout(() => el.remove(), 300);
  }, 3000);
}

// ── Utility ──────────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));