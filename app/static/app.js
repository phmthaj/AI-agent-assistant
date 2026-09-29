const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const messagesEl = document.querySelector("#messages");
const toolCallsEl = document.querySelector("#toolCalls");
const conversationIdEl = document.querySelector("#conversationId");
const agentRunIdEl = document.querySelector("#agentRunId");
const healthText = document.querySelector("#healthText");
const newConversationButton = document.querySelector("#newConversationButton");
const clearToolsButton = document.querySelector("#clearToolsButton");

const state = {
  conversationId: Number(localStorage.getItem("conversationId")) || null,
  toolCalls: [],
};

conversationIdEl.textContent = state.conversationId ?? "New";

function addMessage(role, content, options = {}) {
  const item = document.createElement("article");
  item.className = `message ${role}${options.error ? " error" : ""}`;

  const label = document.createElement("span");
  label.className = "role";
  label.textContent = role;
  item.appendChild(label);

  if (role === "assistant") {
    const parsed = splitReasoning(content);
    if (parsed.reasoning) {
      const details = document.createElement("details");
      details.className = "reasoning";

      const summary = document.createElement("summary");
      summary.textContent = "Reasoning";
      details.appendChild(summary);

      const reasoning = document.createElement("p");
      reasoning.textContent = parsed.reasoning;
      details.appendChild(reasoning);
      item.appendChild(details);
    }

    const body = document.createElement("div");
    body.textContent = parsed.answer || content;
    item.appendChild(body);
  } else {
    const body = document.createElement("div");
    body.textContent = content;
    item.appendChild(body);
  }

  messagesEl.appendChild(item);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function splitReasoning(content) {
  const match = content.match(/^\s*<think>\s*([\s\S]*?)\s*<\/think>\s*([\s\S]*)$/);
  if (!match) {
    return { reasoning: "", answer: content };
  }
  return {
    reasoning: match[1].trim(),
    answer: match[2].trim(),
  };
}

function renderToolCalls(toolCalls) {
  state.toolCalls = [...toolCalls, ...state.toolCalls];
  toolCallsEl.innerHTML = "";

  if (state.toolCalls.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No tool calls yet.";
    toolCallsEl.appendChild(empty);
    return;
  }

  for (const call of state.toolCalls) {
    const card = document.createElement("article");
    card.className = "tool-card";

    const title = document.createElement("strong");
    title.textContent = call.tool_name;
    card.appendChild(title);

    const meta = document.createElement("p");
    meta.className = "tool-meta";
    meta.textContent = call.result?.ok === false ? "failed" : "completed";
    card.appendChild(meta);

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(
      {
        arguments: call.arguments,
        result: call.result,
      },
      null,
      2,
    );
    card.appendChild(pre);
    toolCallsEl.appendChild(card);
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    healthText.textContent = "Backend online";
  } catch (error) {
    healthText.textContent = "Backend unavailable";
  }
}

async function sendMessage(message) {
  const payload = { message };
  if (state.conversationId) {
    payload.conversation_id = state.conversationId;
  }

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }

  state.conversationId = data.conversation_id;
  localStorage.setItem("conversationId", String(state.conversationId));
  conversationIdEl.textContent = data.conversation_id;
  agentRunIdEl.textContent = data.agent_run_id;
  addMessage("assistant", data.answer);
  renderToolCalls(data.tool_calls || []);
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  addMessage("user", message);
  messageInput.value = "";
  sendButton.disabled = true;
  sendButton.textContent = "Sending";

  try {
    await sendMessage(message);
  } catch (error) {
    addMessage("system", error.message, { error: true });
  } finally {
    sendButton.disabled = false;
    sendButton.textContent = "Send";
    messageInput.focus();
  }
});

newConversationButton.addEventListener("click", () => {
  state.conversationId = null;
  state.toolCalls = [];
  localStorage.removeItem("conversationId");
  conversationIdEl.textContent = "New";
  agentRunIdEl.textContent = "-";
  messagesEl.innerHTML = "";
  renderToolCalls([]);
  messageInput.focus();
});

clearToolsButton.addEventListener("click", () => {
  state.toolCalls = [];
  renderToolCalls([]);
});

addMessage("assistant", "Xin chào. Tôi đã sẵn sàng nhận câu hỏi và gọi tool khi cần.");
renderToolCalls([]);
checkHealth();
