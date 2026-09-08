// Group Chat Semantic Search Engine - Frontend Logic

// Sender avatar color palette (deterministic per name)
const AVATAR_COLORS = [
  '#e74c3c', '#3498db', '#2ecc71', '#f39c12',
  '#9b59b6', '#1abc9c', '#e67e22', '#e84393'
];

function getSenderColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function getSenderInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return parts[0].slice(0, 2).toUpperCase();
}

// Lightweight inline markdown parser (bold, italic, code, newlines)
function renderMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const tabBtns = document.querySelectorAll(".tab-btn");
  const viewPanels = document.querySelectorAll(".view-panel");

  // Search Elements
  const searchInput = document.getElementById("searchInput");
  const searchSubmitBtn = document.getElementById("searchSubmitBtn");
  const suggestionChips = document.querySelectorAll(".suggestion-chip");
  const analysisBanner = document.getElementById("analysisBanner");
  const shapeBadge = document.getElementById("shapeBadge");
  const senderChip = document.getElementById("senderChip");
  const temporalChip = document.getElementById("temporalChip");
  const analysisMetaText = document.getElementById("analysisMetaText");
  const resultsContainer = document.getElementById("resultsContainer");
  const resultsHeader = document.getElementById("resultsHeader");
  const matchStats = document.getElementById("matchStats");
  const resultsList = document.getElementById("resultsList");

  // Chat Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const chatSendBtn = document.getElementById("chatSendBtn");

  // Benchmark Elements
  const runBenchmarkBtn = document.getElementById("runBenchmarkBtn");
  const metricsGrid = document.getElementById("metricsGrid");
  const metricZeroHit = document.getElementById("metricZeroHit");
  const metricHit1 = document.getElementById("metricHit1");
  const metricHit3 = document.getElementById("metricHit3");
  const metricMRR = document.getElementById("metricMRR");
  const metricLatency = document.getElementById("metricLatency");
  const benchFilters = document.getElementById("benchFilters");
  const filterPills = document.querySelectorAll(".filter-pill");
  const benchmarkTableWrapper = document.getElementById("benchmarkTableWrapper");
  const benchmarkTableBody = document.getElementById("benchmarkTableBody");
  const benchmarkPlaceholder = document.getElementById("benchmarkPlaceholder");

  let benchmarkData = [];
  let currentBenchFilter = "all";

  // -------------------------------------------------------------
  // TAB NAVIGATION
  // -------------------------------------------------------------
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      tabBtns.forEach(b => b.classList.remove("active"));
      viewPanels.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const activePanel = document.getElementById(targetTab);
      if (activePanel) activePanel.classList.add("active");
    });
  });

  // -------------------------------------------------------------
  // SEARCH EXECUTION
  // -------------------------------------------------------------
  async function performSearch(query) {
    if (!query || !query.trim()) return;

    searchSubmitBtn.disabled = true;
    searchSubmitBtn.innerHTML = `<span class="spinner"></span> Searching...`;
    resultsList.innerHTML = `
      <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
        <div class="spinner" style="width: 24px; height: 24px; margin-bottom: 0.75rem;"></div>
        <div>Searching through 4,250 messages across 6 months...</div>
      </div>
    `;

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), top_k: 8, context_radius: 3 })
      });

      if (!res.ok) throw new Error(`Search error: ${res.statusText}`);
      const data = await res.json();
      renderSearchResults(data);
    } catch (err) {
      resultsList.innerHTML = `
        <div style="padding: 2rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-md); color: #fca5a5;">
          <strong>Error searching:</strong> ${err.message}
        </div>
      `;
    } finally {
      searchSubmitBtn.disabled = false;
      searchSubmitBtn.textContent = "Search";
    }
  }

  function renderSearchResults(data) {
    const analysis = data.query_analysis || {};
    const results = data.results || [];
    const latency = data.latency_ms || 0;

    // Show Analysis Banner
    analysisBanner.style.display = "flex";
    shapeBadge.className = `shape-badge ${analysis.query_type || "semantic"}`;
    shapeBadge.textContent = (analysis.query_type || "Semantic").toUpperCase();

    if (analysis.sender_filter) {
      senderChip.style.display = "inline-block";
      senderChip.textContent = `\u{1f464} ${analysis.sender_filter}`;
    } else {
      senderChip.style.display = "none";
    }

    if (analysis.date_start) {
      temporalChip.style.display = "inline-block";
      const startClean = analysis.date_start.slice(0, 10);
      const endClean = (analysis.date_end || "").slice(0, 10);
      temporalChip.textContent = `\u{1f4c5} ${startClean} to ${endClean}`;
    } else {
      temporalChip.style.display = "none";
    }

    analysisMetaText.textContent = `Retrieved ${results.length} relevant conversation bursts in ${latency} ms (${data.total_candidates} candidates scanned)`;

    resultsHeader.style.display = "flex";
    matchStats.textContent = `Top ${results.length} matches`;

    if (results.length === 0) {
      resultsList.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: var(--text-tertiary);">
          No matching messages found. Try rephrasing your search query.
        </div>
      `;
      return;
    }

    resultsList.innerHTML = "";
    results.forEach((item, index) => {
      const card = createResultCard(item, index + 1, results.length);
      resultsList.appendChild(card);
    });
  }

  function buildBubbleHtml(c, isTarget) {
    const cDate = new Date(c.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    const color = getSenderColor(c.sender);
    const initials = getSenderInitials(c.sender);

    return `
      <div class="chat-bubble ${isTarget ? 'target-msg' : 'context-msg'}" id="bubble-${c.id}">
        <div class="bubble-avatar" style="background: ${color};">${initials}</div>
        <div class="bubble-body">
          <div class="bubble-meta">
            <span class="bubble-sender" style="color: ${color};">${escapeHtml(c.sender)}</span>
            <span>${cDate}</span>
            <span>#${c.id}</span>
            ${isTarget ? '<span class="bubble-match-pill">MATCH</span>' : ''}
          </div>
          <div class="bubble-text">${escapeHtml(c.text)}</div>
        </div>
      </div>
    `;
  }

  function createResultCard(item, rank, totalResults) {
    const msg = item.message;
    const score = (item.score * 100).toFixed(1);
    const context = item.context || [];

    const card = document.createElement("div");
    card.className = "result-card";
    card.id = `msg-card-${msg.id}`;

    // Subtle opacity taper for lower-ranked results
    const opacityVal = totalResults > 1
      ? 1.0 - ((rank - 1) / totalResults) * 0.25
      : 1.0;
    card.style.opacity = opacityVal.toFixed(2);

    const formattedDate = new Date(msg.timestamp).toLocaleString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });

    let contextHtml = "";
    context.forEach(c => {
      contextHtml += buildBubbleHtml(c, c.is_target);
    });

    card.innerHTML = `
      <div class="card-top">
        <div class="card-top-meta">
          <span style="font-weight: 600; color: var(--text-primary);">#${rank}</span>
          <span>${escapeHtml(msg.sender)}</span>
          <span>${formattedDate}</span>
        </div>
        <div class="score-badge">${score}% Semantic Match</div>
      </div>
      <div class="context-stream" id="stream-${msg.id}">
        ${contextHtml}
      </div>
      <div class="card-actions">
        <button class="expand-btn" data-id="${msg.id}" data-radius="6">
          <span>\u2195</span> Expand Conversation Context (\u00b16 msgs)
        </button>
      </div>
    `;

    const expandBtn = card.querySelector(".expand-btn");
    expandBtn.addEventListener("click", () => expandContext(msg.id, expandBtn));
    return card;
  }

  async function expandContext(messageId, btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Expanding...`;

    try {
      const res = await fetch(`/api/context/${messageId}?radius=7`);
      if (!res.ok) throw new Error("Context fetch failed");
      const data = await res.json();
      const messages = data.messages || [];

      const stream = document.getElementById(`stream-${messageId}`);
      if (stream) {
        let newHtml = "";
        messages.forEach(c => {
          newHtml += buildBubbleHtml(c, c.is_target);
        });
        stream.innerHTML = newHtml;
        btn.textContent = "\u2713 Expanded (\u00b17 Messages)";
      }
    } catch (e) {
      btn.textContent = "Error expanding context";
    }
  }

  // Trigger search listeners
  searchSubmitBtn.addEventListener("click", () => performSearch(searchInput.value));
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") performSearch(searchInput.value);
  });

  suggestionChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const query = chip.getAttribute("data-query");
      searchInput.value = query;
      performSearch(query);
    });
  });

  // -------------------------------------------------------------
  // CHAT COPILOT
  // -------------------------------------------------------------
  async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendChatBubble("user", text);
    chatInput.value = "";

    const loadingId = "loading-" + Date.now();
    appendChatBubble("assistant", `<span class="spinner"></span> Scanning group chat history...`, loadingId);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, top_k: 5 })
      });

      if (!res.ok) throw new Error("Chat request failed");
      const data = await res.json();

      let answer = data.answer || "I could not find an answer in the chat.";
      // Parse markdown first
      answer = renderMarkdown(answer);
      // Then format citation chips [#123]
      answer = answer.replace(/\[#(\d+)\]/g, (match, id) => {
        return `<span class="citation-tag" data-msgid="${id}">${match}</span>`;
      });

      const loadingElem = document.getElementById(loadingId);
      if (loadingElem) {
        loadingElem.innerHTML = answer;
        attachCitationListeners(loadingElem);
      }
    } catch (err) {
      const loadingElem = document.getElementById(loadingId);
      if (loadingElem) {
        loadingElem.textContent = `Sorry, an error occurred: ${err.message}`;
      }
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendChatBubble(role, contentHtml, id = null) {
    const row = document.createElement("div");
    row.className = `chat-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = `chat-avatar ${role}`;
    avatar.textContent = (role === "assistant") ? "AI" : "You";

    const content = document.createElement("div");
    content.className = "chat-content";
    if (id) content.id = id;
    content.innerHTML = contentHtml;

    row.appendChild(avatar);
    row.appendChild(content);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function attachCitationListeners(parent) {
    const tags = parent.querySelectorAll(".citation-tag");
    tags.forEach(tag => {
      tag.addEventListener("click", () => {
        const msgId = tag.getAttribute("data-msgid");
        document.getElementById("tabSearchBtn").click();
        searchInput.value = `message #${msgId}`;
        performSearch(`message #${msgId}`);
      });
    });
  }

  chatSendBtn.addEventListener("click", sendChatMessage);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage();
  });

  // -------------------------------------------------------------
  // BENCHMARK SUITE
  // -------------------------------------------------------------
  runBenchmarkBtn.addEventListener("click", async () => {
    runBenchmarkBtn.disabled = true;
    runBenchmarkBtn.innerHTML = `<span class="spinner"></span> Running 40 Benchmark Queries...`;
    benchmarkPlaceholder.style.display = "none";

    try {
      const res = await fetch("/api/benchmark");
      if (!res.ok) throw new Error("Benchmark failed");
      const data = await res.json();
      renderBenchmarkResults(data);
    } catch (err) {
      alert(`Benchmark error: ${err.message}`);
    } finally {
      runBenchmarkBtn.disabled = false;
      runBenchmarkBtn.innerHTML = `<span>\u25b6</span> Re-run 40 Benchmark Queries`;
    }
  });

  function renderBenchmarkResults(data) {
    const m = data.metrics || {};
    benchmarkData = data.queries || [];

    metricsGrid.style.display = "grid";
    benchFilters.style.display = "flex";
    benchmarkTableWrapper.style.display = "block";

    metricZeroHit.textContent = `${m.zero_lexical_hit_at_3}%`;
    metricHit1.textContent = `${m.hit_at_1}%`;
    metricHit3.textContent = `${m.hit_at_3}%`;
    metricMRR.textContent = `${m.mrr}`;
    metricLatency.textContent = `${m.avg_latency_ms} ms`;

    // Color-code metric values
    colorCodeMetric(metricHit1, m.hit_at_1);
    colorCodeMetric(metricHit3, m.hit_at_3);
    colorCodeMetric(metricMRR, m.mrr * 100);
    if (m.avg_latency_ms < 100) metricLatency.classList.add('score-green');

    renderBenchmarkTable();
  }

  function colorCodeMetric(el, value) {
    el.classList.remove('score-green', 'score-amber');
    if (value >= 95) el.classList.add('score-green');
    else if (value < 75) el.classList.add('score-amber');
  }

  function renderBenchmarkTable() {
    benchmarkTableBody.innerHTML = "";

    const filtered = benchmarkData.filter(q => {
      if (currentBenchFilter === "zero") return q.zero_lexical_overlap;
      if (currentBenchFilter === "semantic") return q.query_type === "semantic";
      if (currentBenchFilter === "attributed") return q.query_type === "attributed";
      if (currentBenchFilter === "temporal") return q.query_type === "temporal";
      return true;
    });

    filtered.forEach(q => {
      const tr = document.createElement("tr");
      const targetText = q.target_message ? q.target_message.text : "";
      const targetSender = q.target_message ? q.target_message.sender : "";

      tr.innerHTML = `
        <td style="color: var(--text-tertiary); font-weight: 600;">${q.id}</td>
        <td>
          <div style="font-weight: 500; color: var(--text-primary); margin-bottom: 2px;">
            ${escapeHtml(q.query)}
          </div>
          <div style="font-size: 11px; color: var(--text-secondary);">
            Target [${targetSender}]: "${escapeHtml(targetText)}"
          </div>
        </td>
        <td><span class="shape-badge ${q.query_type}">${q.query_type}</span></td>
        <td>
          ${q.zero_lexical_overlap ? '<span class="zero-tag">YES (Zero)</span>' : '<span style="color: var(--text-tertiary);">No</span>'}
        </td>
        <td style="font-family: monospace; font-size: 11.5px;">#${q.target_message_id}</td>
        <td style="font-weight: 600;">${q.rank > 0 ? `#${q.rank}` : 'Miss'}</td>
        <td>
          ${q.passed ? '<span class="pass-badge">PASS</span>' : '<span class="fail-badge">FAIL</span>'}
        </td>
      `;

      tr.style.cursor = "pointer";
      tr.title = "Click to run this query in the Search tab";
      tr.addEventListener("click", () => {
        document.getElementById("tabSearchBtn").click();
        searchInput.value = q.query;
        performSearch(q.query);
      });

      benchmarkTableBody.appendChild(tr);
    });
  }

  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      currentBenchFilter = pill.getAttribute("data-filter");
      renderBenchmarkTable();
    });
  });

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
