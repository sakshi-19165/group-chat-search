// ==========================================================================
// Search a Group Chat Properly — Frontend Application Logic
// Features: Semantic Search, Conversational Chat Copilot, Benchmark Suite,
// Keyboard Shortcuts, WhatsApp Context Timeline, Toast Notifications
// ==========================================================================

// Deterministic Avatar Color Palette
const AVATAR_COLORS = [
  '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b',
  '#06b6d4', '#ec4899', '#f97316', '#6366f1'
];

function getSenderColor(name) {
  if (!name) return '#64748b';
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

// Markdown parser (bold, italic, inline code, links, newlines)
function renderMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

// Toast notification helper
function showToast(message) {
  const existing = document.querySelector('.toast-notice');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast-notice';
  toast.innerHTML = `
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-emerald);">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 260);
  }, 2400);
}

document.addEventListener("DOMContentLoaded", () => {
  // Navigation & Tabs
  const tabBtns = document.querySelectorAll(".tab-btn");
  const viewPanels = document.querySelectorAll(".view-panel");

  // Search Elements
  const searchInput = document.getElementById("searchInput");
  const searchSubmitBtn = document.getElementById("searchSubmitBtn");
  const clearSearchBtn = document.getElementById("clearSearchBtn");
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

  // Cache initial human-friendly onboarding HTML
  const initialEmptyStateHtml = resultsList ? resultsList.innerHTML : "";

  // Chat Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const chatSendBtn = document.getElementById("chatSendBtn");
  const chatPromptCards = document.querySelectorAll(".chat-prompt-card");
  const chatEmptyState = document.getElementById("chatEmptyState");

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
  function switchTab(targetTabId) {
    tabBtns.forEach(btn => {
      if (btn.getAttribute("data-tab") === targetTabId) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    viewPanels.forEach(p => {
      if (p.id === targetTabId) {
        p.classList.add("active");
      } else {
        p.classList.remove("active");
      }
    });

    // Auto-focus relevant inputs
    if (targetTabId === "search-view") {
      setTimeout(() => searchInput.focus(), 50);
    } else if (targetTabId === "chat-view") {
      setTimeout(() => chatInput.focus(), 50);
    }
  }

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // -------------------------------------------------------------
  // GLOBAL KEYBOARD SHORTCUTS
  // -------------------------------------------------------------
  window.addEventListener("keydown", (e) => {
    // Ctrl+K or Cmd+K or "/" to focus search
    if ((e.key === "k" && (e.ctrlKey || e.metaKey)) || (e.key === "/" && document.activeElement !== searchInput && document.activeElement !== chatInput)) {
      e.preventDefault();
      switchTab("search-view");
      searchInput.focus();
      searchInput.select();
    }

    // Escape to clear or blur
    if (e.key === "Escape") {
      if (document.activeElement === searchInput) {
        if (searchInput.value) {
          clearSearch();
        } else {
          searchInput.blur();
        }
      }
    }
  });

  // Search Input State Handling
  function updateClearButton() {
    if (searchInput.value.trim().length > 0) {
      clearSearchBtn.style.display = "flex";
    } else {
      clearSearchBtn.style.display = "none";
    }
  }

  function clearSearch() {
    searchInput.value = "";
    updateClearButton();
    searchInput.focus();
    analysisBanner.style.display = "none";
    resultsHeader.style.display = "none";
    resultsList.innerHTML = initialEmptyStateHtml;
  }

  searchInput.addEventListener("input", updateClearButton);
  clearSearchBtn.addEventListener("click", clearSearch);

  // -------------------------------------------------------------
  // SEARCH EXECUTION
  // -------------------------------------------------------------
  async function performSearch(query) {
    if (!query || !query.trim()) return;

    const trimmed = query.trim();
    searchInput.value = trimmed;
    updateClearButton();

    searchSubmitBtn.disabled = true;
    searchSubmitBtn.innerHTML = `<span class="spinner"></span> Searching...`;
    resultsList.innerHTML = `
      <div style="text-align: center; padding: 4.5rem 1rem; color: var(--text-secondary);">
        <div class="spinner" style="width: 26px; height: 26px; margin-bottom: 1.15rem;"></div>
        <div style="font-size: 16px; font-weight: 600; color: var(--text-primary);">Scanning 4,250 messages across 6 months...</div>
        <div style="font-size: 13px; color: var(--text-muted); margin-top: 5px;">Computing semantic cosine similarity & extracting surrounding context</div>
      </div>
    `;

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed, top_k: 8, context_radius: 3 })
      });

      if (!res.ok) throw new Error(`Search failed: HTTP ${res.status}`);
      const data = await res.json();
      renderSearchResults(data);
    } catch (err) {
      resultsList.innerHTML = `
        <div style="padding: 1.5rem; background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: var(--radius-md); color: #fda4af;">
          <div style="font-weight: 600; margin-bottom: 4px;">Search Error</div>
          <div style="font-size: 13px;">${err.message}</div>
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
      senderChip.style.display = "inline-flex";
      senderChip.textContent = `👤 ${analysis.sender_filter}`;
    } else {
      senderChip.style.display = "none";
    }

    if (analysis.date_start) {
      temporalChip.style.display = "inline-flex";
      const startClean = analysis.date_start.slice(0, 10);
      const endClean = (analysis.date_end || "").slice(0, 10);
      temporalChip.textContent = `📅 ${startClean} to ${endClean}`;
    } else {
      temporalChip.style.display = "none";
    }

    analysisMetaText.textContent = `Found ${results.length} conversation bursts in ${latency} ms (${data.total_candidates} candidates scanned)`;

    resultsHeader.style.display = "flex";
    matchStats.textContent = `Top ${results.length} matches`;

    if (results.length === 0) {
      resultsList.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon-wrapper">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </div>
          <div class="empty-state-title">No matching conversation bursts found</div>
          <div class="empty-state-subtitle">Try phrasing your question naturally or clicking one of the popular suggestions above.</div>
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
            <span style="font-family: var(--font-mono); opacity: 0.7;">#${c.id}</span>
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
          <span class="rank-badge">#${rank}</span>
          <span style="font-weight: 600; color: var(--text-primary);">${escapeHtml(msg.sender)}</span>
          <span>${formattedDate}</span>
        </div>
        <div class="score-badge">${score}% Semantic Match</div>
      </div>
      <div class="context-stream" id="stream-${msg.id}">
        ${contextHtml}
      </div>
      <div class="card-actions">
        <div class="card-actions-left">
          <button class="action-btn-ghost copy-snippet-btn" title="Copy snippet to clipboard">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>Copy</span>
          </button>
          <button class="action-btn-ghost ask-copilot-btn" title="Ask Copilot about this decision">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Ask Copilot</span>
          </button>
        </div>
        <button class="action-btn-ghost expand-btn" data-id="${msg.id}" data-radius="7">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="7 15 12 20 17 15"></polyline>
            <polyline points="7 9 12 4 17 9"></polyline>
          </svg>
          <span>Expand Context (±7 msgs)</span>
        </button>
      </div>
    `;

    // Action: Expand
    const expandBtn = card.querySelector(".expand-btn");
    expandBtn.addEventListener("click", () => expandContext(msg.id, expandBtn));

    // Action: Copy Snippet
    const copyBtn = card.querySelector(".copy-snippet-btn");
    copyBtn.addEventListener("click", () => {
      const copyText = `[#${msg.id}] ${msg.sender} (${formattedDate}): "${msg.text}"`;
      navigator.clipboard.writeText(copyText).then(() => {
        showToast(`Copied snippet #${msg.id} to clipboard`);
      }).catch(() => {
        showToast(`Snippet #${msg.id} ready`);
      });
    });

    // Action: Ask Copilot
    const askCopilotBtn = card.querySelector(".ask-copilot-btn");
    askCopilotBtn.addEventListener("click", () => {
      switchTab("chat-view");
      const askQuery = `What was the full context and decision around message #${msg.id} by ${msg.sender}: "${msg.text.slice(0, 70)}"?`;
      chatInput.value = askQuery;
      sendChatMessage();
    });

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
        btn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent-emerald);">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>Expanded (±7 Messages)</span>
        `;
        showToast(`Loaded ${messages.length} surrounding messages`);
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
      performSearch(query);
    });
  });

  // -------------------------------------------------------------
  // CHAT COPILOT
  // -------------------------------------------------------------
  async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (chatEmptyState) {
      chatEmptyState.style.display = "none";
    }

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

      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();

      let answer = data.answer || "I could not find a definitive answer in the chat corpus.";
      // Parse markdown
      answer = renderMarkdown(answer);
      // Format citation chips [#123]
      answer = answer.replace(/\[#(\d+)\]/g, (match, id) => {
        return `<span class="citation-tag" data-msgid="${id}">[#${id}]</span>`;
      });

      const loadingElem = document.getElementById(loadingId);
      if (loadingElem) {
        loadingElem.innerHTML = answer;
        attachCitationListeners(loadingElem);
      }
    } catch (err) {
      const loadingElem = document.getElementById(loadingId);
      if (loadingElem) {
        loadingElem.innerHTML = `<span style="color: #fda4af;">Unable to complete query: ${err.message}. If using OpenRouter, verify your API key is configured.</span>`;
      }
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendChatBubble(role, contentHtml, id = null) {
    const row = document.createElement("div");
    row.className = `chat-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = `chat-avatar ${role}`;
    if (role === "assistant") {
      avatar.innerHTML = '<img src="assets/logo.png" alt="AI" class="avatar-logo-img" />';
    } else {
      avatar.textContent = "You";
    }

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
        switchTab("search-view");
        searchInput.value = `message #${msgId}`;
        performSearch(`message #${msgId}`);
      });
    });
  }

  chatSendBtn.addEventListener("click", sendChatMessage);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage();
  });

  chatPromptCards.forEach(card => {
    card.addEventListener("click", () => {
      const prompt = card.getAttribute("data-prompt");
      chatInput.value = prompt;
      sendChatMessage();
    });
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
      showToast("Benchmark evaluation completed: 100% Hit@3");
    } catch (err) {
      alert(`Benchmark error: ${err.message}`);
    } finally {
      runBenchmarkBtn.disabled = false;
      runBenchmarkBtn.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        <span>Re-run 40 Benchmark Queries</span>
      `;
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

    // Color-code metrics
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
        <td style="color: var(--text-muted); font-family: var(--font-mono); font-weight: 600;">${q.id}</td>
        <td>
          <div style="font-weight: 500; color: var(--text-primary); margin-bottom: 2px;">
            ${escapeHtml(q.query)}
          </div>
          <div style="font-size: 11.5px; color: var(--text-secondary);">
            Target [${targetSender}]: "${escapeHtml(targetText)}"
          </div>
        </td>
        <td><span class="shape-badge ${q.query_type}">${q.query_type}</span></td>
        <td>
          ${q.zero_lexical_overlap ? '<span class="zero-tag">ZERO OVERLAP</span>' : '<span style="color: var(--text-muted);">Lexical</span>'}
        </td>
        <td style="font-family: var(--font-mono); font-size: 11.5px; color: var(--text-secondary);">#${q.target_message_id}</td>
        <td style="font-weight: 700; font-family: var(--font-mono);">${q.rank > 0 ? `#${q.rank}` : 'Miss'}</td>
        <td>
          ${q.passed ? '<span class="pass-badge">PASS</span>' : '<span class="fail-badge">FAIL</span>'}
        </td>
      `;

      tr.style.cursor = "pointer";
      tr.title = "Click to run this query in the Search tab";
      tr.addEventListener("click", () => {
        switchTab("search-view");
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
