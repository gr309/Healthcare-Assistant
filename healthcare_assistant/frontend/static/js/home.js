const base = window.location.origin;
const token = "f9f77226996fd674c67ad2b8ef401f9abdca6879";

let currentConversationId = null;

document.addEventListener("DOMContentLoaded", function () {
    loadConversationInSidebar();
    setupNewConversationButton();
    setupConversationClickListener();
    setupMessageInput();
    toggleEmptyState();
});

function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Token ${token}`
    };
}

function getReplyBox() {
    return document.getElementById("replyBox") || document.querySelector(".reply");
}

function toggleEmptyState() {
    const replyBox = getReplyBox();
    const emptyState = document.getElementById("emptyState");
    if (!replyBox || !emptyState) return;

    const hasMessages = Array.from(replyBox.children).some(
        (child) => child.id !== "emptyState"
    );

    emptyState.style.display = hasMessages ? "none" : "block";
}

function safeJsonParse(text) {
    try {
        return JSON.parse(text);
    } catch (error) {
        return null;
    }
}

function safePythonDictParse(text) {
    if (typeof text !== "string") return null;

    const trimmed = text.trim();
    if (!trimmed.startsWith("{") || !trimmed.endsWith("}")) {
        return null;
    }

    try {
        const normalized = trimmed
            .replace(/\bTrue\b/g, "true")
            .replace(/\bFalse\b/g, "false")
            .replace(/\bNone\b/g, "null")
            .replace(/'([^'\\]*(?:\\.[^'\\]*)*)'/g, function (_, content) {
                return `"${content
                    .replace(/\\/g, "\\\\")
                    .replace(/"/g, '\\"')}"`;
            });

        return JSON.parse(normalized);
    } catch (error) {
        return null;
    }
}

function unwrapQuotedString(text) {
    if (typeof text !== "string") return null;

    const trimmed = text.trim();
    const hasDoubleQuotes = trimmed.startsWith('"') && trimmed.endsWith('"');
    const hasSingleQuotes = trimmed.startsWith("'") && trimmed.endsWith("'");

    if (!hasDoubleQuotes && !hasSingleQuotes) {
        return null;
    }

    try {
        return JSON.parse(trimmed);
    } catch (error) {
        const inner = trimmed.slice(1, -1);
        return inner
            .replace(/\\n/g, "\n")
            .replace(/\\"/g, '"')
            .replace(/\\'/g, "'")
            .replace(/\\\\/g, "\\");
    }
}

function parseStructuredPayloadString(text) {
    if (typeof text !== "string") return null;

    const queue = [text.trim()];
    const seen = new Set();

    while (queue.length > 0) {
        const current = queue.shift();
        if (!current || seen.has(current)) {
            continue;
        }
        seen.add(current);

        const jsonParsed = safeJsonParse(current);
        if (jsonParsed && typeof jsonParsed === "object") {
            return jsonParsed;
        }
        if (typeof jsonParsed === "string") {
            queue.push(jsonParsed.trim());
        }

        const pythonParsed = safePythonDictParse(current);
        if (pythonParsed && typeof pythonParsed === "object") {
            return pythonParsed;
        }

        const unwrapped = unwrapQuotedString(current);
        if (typeof unwrapped === "string") {
            queue.push(unwrapped.trim());
        } else if (unwrapped && typeof unwrapped === "object") {
            return unwrapped;
        }
    }

    return null;
}

function normalizeConfidence(confidence) {
    if (confidence === null || confidence === undefined || confidence === "") {
        return "";
    }

    if (typeof confidence === "number") {
        return `${Math.round(confidence * 100)}%`;
    }

    return String(confidence);
}

function normalizeBotPayload(payload) {
    if (payload === null || payload === undefined || payload === "") {
        return {
            answer: "No reply",
            confidence: "",
            suggestion: "",
            emergency: false
        };
    }

    let resolvedPayload = payload;

    if (typeof resolvedPayload === "string") {
        const parsed = parseStructuredPayloadString(resolvedPayload);
        if (parsed && typeof parsed === "object") {
            resolvedPayload = parsed;
        } else {
            return {
                answer: resolvedPayload,
                confidence: "",
                suggestion: "",
                emergency: false
            };
        }
    }

    if (resolvedPayload.ai_reply) {
        return normalizeBotPayload(resolvedPayload.ai_reply);
    }

    if (typeof resolvedPayload !== "object" || Array.isArray(resolvedPayload)) {
        return {
            answer: String(resolvedPayload),
            confidence: "",
            suggestion: "",
            emergency: false
        };
    }

    return {
        answer: resolvedPayload.answer || resolvedPayload.message || resolvedPayload.detail || "No reply",
        confidence: normalizeConfidence(resolvedPayload.confidence),
        suggestion: resolvedPayload.suggestion || "",
        emergency: resolvedPayload.emergency === true || String(resolvedPayload.emergency).toLowerCase() === "true"
    };
}

async function readApiResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        return await response.json();
    }

    const text = await response.text();
    return { message: text };
}

async function loadConversationInSidebar(activeConversationId = currentConversationId) {
    const conversationList = document.querySelector(".conversation-list");
    if (!conversationList) return;

    try {
        const response = await fetch(`${base}/api/chat-list/`, {
            method: "GET",
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            console.log("error in status in chat-list", response.status);
            return;
        }

        const data = await response.json();
        conversationList.innerHTML = "";

        data.forEach((chat) => {
            const item = document.createElement("li");
            item.className = "conversation-item";
            item.dataset.convoId = chat.id;

            if (String(chat.id) === String(activeConversationId)) {
                item.classList.add("active");
            }

            const title = document.createElement("h3");
            title.textContent = chat.title;
            item.appendChild(title);

            conversationList.appendChild(item);
        });

        if (!activeConversationId && data.length > 0) {
            const firstConversationId = data[0].id;
            setActiveConversation(firstConversationId);
            await openConversation(firstConversationId);
        }
    } catch (error) {
        console.error(error);
    }
}

async function createConversation() {
    const response = await fetch(`${base}/api/chat/create/`, {
        method: "POST",
        headers: getAuthHeaders()
    });

    if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
    }

    const data = await response.json();
    currentConversationId = data.id;
    await loadConversationInSidebar(data.id);
    return data.id;
}

function setActiveConversation(conversationId) {
    currentConversationId = conversationId;

    document.querySelectorAll(".conversation-item").forEach((item) => {
        item.classList.toggle(
            "active",
            String(item.dataset.convoId) === String(conversationId)
        );
    });
}

function setupNewConversationButton() {
    const newConvoBtn = document.getElementById("new-convo-btn");
    if (!newConvoBtn) {
        console.error("Button with ID 'new-convo-btn' not found.");
        return;
    }

    newConvoBtn.addEventListener("click", async () => {
        const originalText = newConvoBtn.textContent;
        newConvoBtn.disabled = true;
        newConvoBtn.textContent = "Creating...";

        try {
            const conversationId = await createConversation();
            await openConversation(conversationId);
        } catch (error) {
            console.error(error);
        } finally {
            newConvoBtn.disabled = false;
            newConvoBtn.textContent = originalText;
        }
    });
}

function setupConversationClickListener() {
    const list = document.querySelector(".conversation-list");
    if (!list) return;

    list.addEventListener("click", async function (event) {
        const clickedItem = event.target.closest(".conversation-item");
        if (!clickedItem) return;

        const convoId = clickedItem.dataset.convoId;
        if (String(convoId) === String(currentConversationId)) return;

        setActiveConversation(convoId);
        await openConversation(convoId);
    });
}

async function openConversation(id) {
    const replyBox = getReplyBox();
    if (!replyBox) return;

    try {
        const response = await fetch(`${base}/api/chat/${id}/`, {
            method: "GET",
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            console.log("error in status in chat/id", response.status);
            return;
        }

        const data = await response.json();
        const messages = data.messages || [];

        currentConversationId = id;
        setActiveConversation(id);
        replyBox.querySelectorAll(".message").forEach((message) => message.remove());

        messages.forEach((chat) => {
            appendMessage(chat.query, "user");
            appendBotResponse(chat.response || "No reply");
        });

        toggleEmptyState();
        scrollReplyToBottom();
        requestAnimationFrame(scrollReplyToBottom);
    } catch (error) {
        console.error(error);
    }
}

function appendMessage(text, type) {
    const replyBox = getReplyBox();
    if (!replyBox) return;

    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.innerText = text;
    replyBox.appendChild(message);
    toggleEmptyState();
}

function appendBotResponse(payload) {
    const replyBox = getReplyBox();
    if (!replyBox) return;

    const normalized = normalizeBotPayload(payload);

    const message = document.createElement("div");
    message.className = "message bot bot-card";
    if (normalized.emergency) {
        message.classList.add("emergency-card");
    }

    const label = document.createElement("p");
    label.className = "bot-label";
    label.innerText = normalized.emergency ? "Urgent guidance" : "Assistant response";
    message.appendChild(label);

    const answer = document.createElement("p");
    answer.className = "bot-answer";
    answer.innerText = normalized.answer;
    message.appendChild(answer);

    const meta = document.createElement("div");
    meta.className = "bot-meta";

    if (normalized.confidence) {
        const confidence = document.createElement("span");
        confidence.className = "bot-chip";
        confidence.innerText = `Confidence: ${normalized.confidence}`;
        meta.appendChild(confidence);
    }

    const statusChip = document.createElement("span");
    statusChip.className = normalized.emergency ? "bot-chip emergency" : "bot-chip warning";
    statusChip.innerText = normalized.emergency ? "Emergency" : "Non-emergency";
    meta.appendChild(statusChip);

    message.appendChild(meta);

    if (normalized.suggestion) {
        const suggestion = document.createElement("div");
        suggestion.className = "bot-suggestion";
        const suggestionTitle = document.createElement("strong");
        suggestionTitle.innerText = "Suggested next step";
        suggestion.appendChild(suggestionTitle);

        const suggestionText = document.createElement("span");
        suggestionText.innerText = normalized.suggestion;
        suggestion.appendChild(suggestionText);
        message.appendChild(suggestion);
    }

    replyBox.appendChild(message);
    toggleEmptyState();
}

function scrollReplyToBottom() {
    const replyBox = getReplyBox();
    if (!replyBox) return;

    replyBox.scrollTop = replyBox.scrollHeight;
}

function scrollReplyToBottomSmooth() {
    const replyBox = getReplyBox();
    if (!replyBox) return;

    replyBox.scrollTo({
        top: replyBox.scrollHeight,
        behavior: "smooth"
    });
}

function setupMessageInput() {
    const input = document.getElementById("messageInput");
    if (!input) return;

    input.addEventListener("keydown", function (event) {
        if (event.key !== "Enter" || event.shiftKey) return;

        event.preventDefault();
        sendMessage();
    });
}

async function sendMessage() {
    const input = document.getElementById("messageInput");
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    input.disabled = true;

    try {
        if (!currentConversationId) {
            await createConversation();
        }

        appendMessage(message, "user");
        input.value = "";
        scrollReplyToBottomSmooth();

        const response = await fetch(`${base}/api/chat/${currentConversationId}/`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
                content: message
            })
        });

        const data = await readApiResponse(response);

        if (!response.ok) {
            throw new Error(
                data.ai_reply ||
                data.message ||
                data.detail ||
                `HTTP Error: ${response.status}`
            );
        }

        appendBotResponse(
            data.ai_reply ||
            data.message ||
            data.detail ||
            "No reply"
        );
        await loadConversationInSidebar(currentConversationId);
        scrollReplyToBottomSmooth();
    } catch (error) {
        console.error(error);
        appendBotResponse(error.message || "Something went wrong while sending the message.");
    } finally {
        input.disabled = false;
        input.focus();
    }
}

window.sendMessage = sendMessage;
