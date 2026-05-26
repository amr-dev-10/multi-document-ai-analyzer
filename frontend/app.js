const state = {
  token: localStorage.getItem("token"),
  sessionId: null,
  pollTimer: null,
};

const authPanel = document.querySelector("#authPanel");
const workspace = document.querySelector("#workspace");
const logoutBtn = document.querySelector("#logoutBtn");
const authMessage = document.querySelector("#authMessage");
const documentsEl = document.querySelector("#documents");
const messagesEl = document.querySelector("#messages");
const fileInput = document.querySelector("#fileInput");
const selectedFilesEl = document.querySelector("#selectedFiles");
const dropzone = document.querySelector("#dropzone");

function headers(json = true) {
  const output = {};
  if (json) output["Content-Type"] = "application/json";
  if (state.token) output.Authorization = `Bearer ${state.token}`;
  return output;
}

function setAuthenticated(isAuthenticated) {
  authPanel.classList.toggle("hidden", isAuthenticated);
  workspace.classList.toggle("hidden", !isAuthenticated);
  logoutBtn.classList.toggle("hidden", !isAuthenticated);
  if (isAuthenticated) {
    loadDocuments();
    startPolling();
  } else if (state.pollTimer) {
    clearInterval(state.pollTimer);
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }
  return data;
}

async function authenticate(mode) {
  authMessage.textContent = "";
  const payload = {
    email: document.querySelector("#email").value,
    password: document.querySelector("#password").value,
  };
  try {
    const data = await api(`/api/v1/auth/${mode}`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(payload),
    });
    state.token = data.access_token;
    localStorage.setItem("token", state.token);
    setAuthenticated(true);
  } catch (error) {
    authMessage.textContent = error.message;
  }
}

function statusClass(status) {
  return `status ${status}`;
}

async function loadDocuments() {
  try {
    const docs = await api("/api/v1/documents", {
      headers: headers(false),
    });
    documentsEl.innerHTML = docs.length
      ? docs
        .map(
          (doc) => `
          <div class="doc">
            <strong>${escapeHtml(doc.file_name)}</strong>
            <span class="${statusClass(doc.status)}">${doc.status}</span>
            ${doc.error ? `<p class="status failed">${escapeHtml(doc.error)}</p>` : ""}
          </div>
        `
        )
        .join("")
      : `<p class="muted">No documents uploaded yet.</p>`;

    // STOP POLLING IF ALL DOCUMENTS FINISHED
    const allFinished = docs.every(
      (doc) => doc.status === "ready" || doc.status === "failed"
    );

    if (allFinished && state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }

  } catch (error) {
    documentsEl.innerHTML = `
      <p class="status failed">${escapeHtml(error.message)}</p>
    `;
  }
}

function startPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(loadDocuments, 2500);
}

async function uploadFiles() {
  if (!fileInput.files.length) return;
  const form = new FormData();
  for (const file of fileInput.files) form.append("files", file);
  await api("/api/v1/upload", {
    method: "POST",
    headers: headers(false),
    body: form,
  });
  fileInput.value = "";
  selectedFilesEl.innerHTML = "";
  await loadDocuments();
}

function addMessage(role, text, sources = []) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text;
  messagesEl.appendChild(message);
  if (sources.length) {
    const sourceBlock = document.createElement("div");
    sourceBlock.className = "sources";
    sourceBlock.innerHTML = sources
      .map(
        (source, idx) => `
        <div class="source">
          <strong>[${idx + 1}] ${escapeHtml(source.document_name)}${source.page ? `, page ${source.page}` : ""}</strong>
          <div>Score: ${source.score}</div>
          <div>${escapeHtml(source.text.slice(0, 320))}${source.text.length > 320 ? "..." : ""}</div>
        </div>
      `,
      )
      .join("");
    messagesEl.appendChild(sourceBlock);
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function askQuestion(event) {
  event.preventDefault();
  const input = document.querySelector("#question");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  addMessage("user", question);
  try {
    const data = await api("/api/v1/chat/query", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ question, session_id: state.sessionId, top_k: 5 }),
    });
    state.sessionId = data.session_id;
    addMessage("assistant", data.answer, data.sources);
  } catch (error) {
    addMessage("assistant", error.message);
  }
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return map[char];
  });
}

document.querySelector("#authForm").addEventListener("submit", (event) => {
  event.preventDefault();
  authenticate("login");
});
document.querySelector("#registerBtn").addEventListener("click", () => authenticate("register"));
document.querySelector("#uploadBtn").addEventListener("click", uploadFiles);
document.querySelector("#chatForm").addEventListener("submit", askQuestion);
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("token");
  state.token = null;
  state.sessionId = null;
  setAuthenticated(false);
});

setAuthenticated(Boolean(state.token));

function renderSelectedFiles(files) {
  if (!files.length) {
    selectedFilesEl.innerHTML = "";
    return;
  }

  selectedFilesEl.innerHTML = Array.from(files)
    .map(
      (file) => `
      <div class="selected-file">
        ${escapeHtml(file.name)}
      </div>
    `
    )
    .join("");
}
fileInput.addEventListener("change", () => { renderSelectedFiles(fileInput.files); });
dropzone.addEventListener("dragover", (event) => { event.preventDefault(); dropzone.classList.add("dragging"); });
dropzone.addEventListener("dragleave", () => { dropzone.classList.remove("dragging"); });
dropzone.addEventListener("drop", (event) => {
  event.preventDefault(); dropzone.classList.remove("dragging");
  fileInput.files = event.dataTransfer.files;
  renderSelectedFiles(fileInput.files);
});