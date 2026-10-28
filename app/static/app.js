document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const statusBadge = document.getElementById("api-status-badge");
  const statusText = document.getElementById("api-status-text");

  const indexForm = document.getElementById("index-form");
  const videoUrlInput = document.getElementById("video-url");
  const indexBtn = document.getElementById("index-btn");
  const indexSpinner = document.getElementById("index-spinner");
  const indexStatus = document.getElementById("index-status");

  const videoFilter = document.getElementById("video-filter");
  const indexedVideosList = document.getElementById("indexed-videos-list");

  const youtubeFrame = document.getElementById("youtube-frame");
  const playerBadge = document.getElementById("player-badge");

  const askForm = document.getElementById("ask-form");
  const questionInput = document.getElementById("question-input");
  const askBtn = document.getElementById("ask-btn");
  const askSpinner = document.getElementById("ask-spinner");

  const qaResult = document.getElementById("qa-result");
  const answerContent = document.getElementById("answer-content");
  const citationsContainer = document.getElementById("citations-container");
  const citationsCount = document.getElementById("citations-count");
  const copyBtn = document.getElementById("copy-btn");
  const copyLabel = document.getElementById("copy-label");

  const sampleChips = document.getElementById("sample-chips");

  // Initial Health & Library Fetch
  checkApiHealth();
  refreshVideoCatalog();

  // 1. Health Status
  async function checkApiHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        const llmStatus = data.groq_configured && data.gemini_configured
          ? "System Online"
          : "Keys Missing";
        statusText.textContent = `v${data.version} • ${llmStatus}`;
        if (!data.groq_configured || !data.gemini_configured) {
          statusBadge.style.borderColor = "rgba(245, 158, 11, 0.4)";
          statusBadge.style.color = "#fbbf24";
        }
      } else {
        statusText.textContent = "API Error";
      }
    } catch {
      statusText.textContent = "Offline";
    }
  }

  // 2. Video Indexing Handler
  indexForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = videoUrlInput.value.trim();
    if (!url) return;

    setLoading(indexBtn, indexSpinner, true, "Indexing Transcript...");
    indexStatus.className = "alert-box hidden";

    try {
      const response = await fetch("/api/index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to index video.");
      }

      indexStatus.textContent = `Success: Video '${data.video_id}' indexed (${data.total_chunks_indexed} searchable chunks ready).`;
      indexStatus.className = "alert-box success";
      videoUrlInput.value = "";

      await refreshVideoCatalog();
      loadVideoInPlayer(data.video_id, 0);
    } catch (err) {
      indexStatus.textContent = `Error: ${err.message}`;
      indexStatus.className = "alert-box error";
    } finally {
      setLoading(indexBtn, indexSpinner, false, "Index Video Transcript");
    }
  });

  // 3. Ask Question Handler
  askForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    const selectedVideo = videoFilter.value || null;

    setLoading(askBtn, askSpinner, true, "Synthesizing...");
    qaResult.classList.add("hidden");

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          video_id: selectedVideo,
          top_k: 4,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to synthesize answer.");
      }

      displayAnswer(data);
    } catch (err) {
      alert(`Query error: ${err.message}`);
    } finally {
      setLoading(askBtn, askSpinner, false, "Ask AI");
    }
  });

  // 4. Suggested Questions Click
  sampleChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip && chip.dataset.q) {
      questionInput.value = chip.dataset.q;
      questionInput.focus();
    }
  });

  // 5. Copy Answer Button
  copyBtn.addEventListener("click", () => {
    const text = answerContent.textContent;
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      copyLabel.textContent = "Copied!";
      setTimeout(() => {
        copyLabel.textContent = "Copy";
      }, 2000);
    });
  });

  // 6. Refresh Video Catalog
  async function refreshVideoCatalog() {
    try {
      const res = await fetch("/api/videos");
      if (!res.ok) return;
      const data = await res.json();

      const currentSelected = videoFilter.value;
      videoFilter.innerHTML = '<option value="">🌐 All Indexed Videos (Global Corpus)</option>';
      indexedVideosList.innerHTML = "";

      if (data.videos && data.videos.length > 0) {
        data.videos.forEach((vid) => {
          // Add to Select Option
          const opt = document.createElement("option");
          opt.value = vid.video_id;
          opt.textContent = `Video ${vid.video_id} (${vid.chunk_count} chunks)`;
          if (vid.video_id === currentSelected) {
            opt.selected = true;
          }
          videoFilter.appendChild(opt);

          // Add to Sidebar List Row
          const row = document.createElement("div");
          row.className = "video-row";
          row.innerHTML = `
            <span class="video-row-id" title="Load into player">${vid.video_id}</span>
            <div class="video-row-actions">
              <span class="video-badge">${vid.chunk_count} chunks</span>
              <button class="delete-btn" title="Remove video" data-id="${vid.video_id}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          `;

          row.querySelector(".video-row-id").addEventListener("click", () => {
            loadVideoInPlayer(vid.video_id, 0);
            videoFilter.value = vid.video_id;
          });

          row.querySelector(".delete-btn").addEventListener("click", async (e) => {
            e.stopPropagation();
            if (confirm(`Remove video "${vid.video_id}" from index?`)) {
              await deleteVideo(vid.video_id);
            }
          });

          indexedVideosList.appendChild(row);
        });

        // Set default player if not loaded yet
        if (!youtubeFrame.src || youtubeFrame.src === "about:blank") {
          loadVideoInPlayer(data.videos[0].video_id, 0);
        }
      } else {
        indexedVideosList.innerHTML = '<div class="empty-state">No videos indexed yet. Enter a YouTube URL above.</div>';
      }
    } catch (e) {
      console.error("Error refreshing videos:", e);
    }
  }

  // 7. Delete Video
  async function deleteVideo(videoId) {
    try {
      const res = await fetch(`/api/videos/${videoId}`, { method: "DELETE" });
      if (res.ok) {
        await refreshVideoCatalog();
      }
    } catch (err) {
      console.error("Failed to delete video:", err);
    }
  }

  // 8. Render Answer and Citations
  function displayAnswer(data) {
    answerContent.textContent = data.answer;
    citationsContainer.innerHTML = "";

    const sources = data.sources || [];
    citationsCount.textContent = `${sources.length} citation${sources.length === 1 ? "" : "s"}`;

    if (sources.length > 0) {
      sources.forEach((src) => {
        const card = document.createElement("div");
        card.className = "citation-card";

        const startSeconds = Math.floor(src.start);
        card.innerHTML = `
          <div class="citation-meta">
            <span class="citation-video">ID: ${src.video_id}</span>
            <button class="timestamp-seek-btn" data-video="${src.video_id}" data-time="${startSeconds}">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
              ${src.timestamp_label}
            </button>
          </div>
          <p class="citation-snippet">"${src.text_snippet}"</p>
        `;

        card.querySelector(".timestamp-seek-btn").addEventListener("click", () => {
          loadVideoInPlayer(src.video_id, startSeconds);
        });

        citationsContainer.appendChild(card);
      });
    }

    qaResult.classList.remove("hidden");
  }

  // 9. Load Player
  function loadVideoInPlayer(videoId, startSeconds) {
    if (!videoId) return;
    youtubeFrame.src = `https://www.youtube-nocookie.com/embed/${videoId}?start=${startSeconds}&autoplay=1`;
    playerBadge.textContent = `Playing ${videoId} @ ${startSeconds}s`;
    playerBadge.style.background = "rgba(99, 102, 241, 0.2)";
    playerBadge.style.color = "#818cf8";
  }

  // 10. Utility Helper
  function setLoading(button, spinner, isLoading, label) {
    const textSpan = button.querySelector(".btn-text");
    if (isLoading) {
      button.disabled = true;
      textSpan.textContent = label;
      spinner.classList.remove("hidden");
    } else {
      button.disabled = false;
      textSpan.textContent = label;
      spinner.classList.add("hidden");
    }
  }
});
