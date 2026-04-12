
const API_URL    = "http://127.0.0.1:8001/analyze";
const analyzeBtn = document.getElementById("analyzeBtn");
const inputText  = document.getElementById("inputText");
const resultBox  = document.getElementById("result");

// ── Dynamically inject model selector after the textarea ──────────────────────
const modelWrapper = document.createElement("div");
modelWrapper.style.cssText = "margin-bottom: 16px; display: flex; align-items: center; gap: 12px;";
modelWrapper.innerHTML = `
  <label for="modelSelect" style="font-size:0.9rem; font-weight:500; color:#fafafa; white-space:nowrap;">Model:</label>
  <select id="modelSelect" style="
    background-color: #262730;
    color: #fafafa;
    border: 1px solid #41444e;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 0.95rem;
    cursor: pointer;
    transition: border-color 0.2s;
  ">
    <option value="svm">SVM (faster)</option>
    <option value="distilbert">DistilBERT (more accurate)</option>
  </select>
`;

// Insert model selector before the Check button
analyzeBtn.parentNode.insertBefore(modelWrapper, analyzeBtn);

// Add hover effect on select
const modelSelect = document.getElementById("modelSelect");
modelSelect.addEventListener("mouseover", () => modelSelect.style.borderColor = "#ff4b4b");
modelSelect.addEventListener("mouseout",  () => modelSelect.style.borderColor = "#41444e");

// ── Helpers ────────────────────────────────────────────────────────────────────
function setLoading(on) {
  analyzeBtn.disabled = on;
  analyzeBtn.textContent = on ? "Checking..." : "Check";
}

function showResult(label, confidence, modelName) {
  const isSmishing = label === "Smishing";
  const pct        = (confidence * 100).toFixed(1);
  const cls        = isSmishing ? "phishing" : "safe";
  const verdict    = isSmishing ? "⚠️ Smishing / Phishing Detected" : "✅ No Threat Found";

  resultBox.className = `result-box ${cls}`;
  resultBox.style.display = "block";
  resultBox.innerHTML = `
    <div><strong>${verdict}</strong></div>
    <div style="margin-top:8px; font-size:0.9rem; opacity:0.85;">
      Classification: <strong>${label}</strong> &nbsp;|&nbsp;
      Confidence: <strong>${pct}%</strong> &nbsp;|&nbsp;
      Model: <strong>${modelName}</strong>
    </div>
  `;
}

function showError(msg) {
  resultBox.className = "result-box error";
  resultBox.style.display = "block";
  resultBox.innerHTML = `<strong>⚠️ Error:</strong> ${msg}`;
}

// ── Main handler ───────────────────────────────────────────────────────────────
analyzeBtn.addEventListener("click", async () => {
  const text  = inputText.value.trim();
  const model = modelSelect.value;

  if (!text) {
    showError("Please enter a message before running analysis.");
    return;
  }

  setLoading(true);
  resultBox.style.display = "none";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, model }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || `Server error ${response.status}`);
    }

    const data = await response.json();
    showResult(data.label, data.confidence, data.model);

  } catch (err) {
    if (err.message.includes("Failed to fetch")) {
      showError("Cannot reach the backend. Make sure the server is running on port 8000.");
    } else {
      showError(err.message);
    }
  } finally {
    setLoading(false);
  }
});