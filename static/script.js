const chatArea = document.getElementById("chatArea");
const chatForm = document.getElementById("chatForm");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");
const docxBtn = document.getElementById("docxBtn");
const imgBtn = document.getElementById("imgBtn");

function addMessage(sender, text, extraHtml) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (sender === "You" ? "user" : "bot");
  wrap.innerHTML = `<div class="msg-label">${sender}</div><div class="msg-text"></div>`;
  wrap.querySelector(".msg-text").textContent = text;
  if (extraHtml) {
    wrap.querySelector(".msg-text").insertAdjacentHTML("beforeend", extraHtml);
  }
  chatArea.appendChild(wrap);
  chatArea.scrollTop = chatArea.scrollHeight;
  return wrap;
}

function addTyping() {
  const el = document.createElement("div");
  el.className = "msg bot";
  el.id = "typingIndicator";
  el.innerHTML = `<div class="msg-label">Dhrubo</div><div class="typing">typing...</div>`;
  chatArea.appendChild(el);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  msgInput.disabled = busy;
  docxBtn.disabled = busy;
  imgBtn.disabled = busy;
}

async function initWelcome() {
  try {
    const res = await fetch("/api/welcome");
    const data = await res.json();
    addMessage("Dhrubo", data.welcome_message || "Hey! I'm Dhrubo.");
    if (!data.site_enabled) {
      setBusy(true);
      msgInput.placeholder = "Guest chat is paused right now...";
    }
  } catch (err) {
    addMessage("Dhrubo", "Hey! I'm Dhrubo. What's on your mind?");
  }
}
initWelcome();

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = msgInput.value.trim();
  if (!text) return;
  msgInput.value = "";
  addMessage("You", text);
  setBusy(true);
  addTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    removeTyping();
    addMessage("Dhrubo", data.reply || "(no reply)");
  } catch (err) {
    removeTyping();
    addMessage("Dhrubo", "Sorry, couldn't reach the server. Try again in a bit.");
  }
  setBusy(false);
  msgInput.focus();
});

docxBtn.addEventListener("click", async () => {
  const title = prompt("What should the Word document be about?");
  if (!title) return;
  addMessage("You", `Make a Word doc: ${title}`);
  setBusy(true);
  addTyping();
  try {
    const res = await fetch("/api/generate_docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content: `# ${title}\n\n(Draft content - ask Dhrubo to expand this in chat.)` }),
    });
    const data = await res.json();
    removeTyping();
    if (data.error) {
      addMessage("Dhrubo", data.error);
    } else {
      addMessage("Dhrubo", "Here's your document:", `<br><a class="file-link" href="${data.download_url}" target="_blank">⬇ ${data.filename}</a>`);
    }
  } catch (err) {
    removeTyping();
    addMessage("Dhrubo", "Sorry, couldn't create the document right now.");
  }
  setBusy(false);
});

imgBtn.addEventListener("click", async () => {
  const prompt_text = prompt("Describe the image you want:");
  if (!prompt_text) return;
  addMessage("You", `Make an image: ${prompt_text}`);
  setBusy(true);
  addTyping();
  try {
    const res = await fetch("/api/generate_image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt_text }),
    });
    const data = await res.json();
    removeTyping();
    if (data.error) {
      addMessage("Dhrubo", data.error);
    } else {
      addMessage("Dhrubo", "Here you go:", `<br><img class="generated" src="${data.image_url}" alt="generated image">`);
    }
  } catch (err) {
    removeTyping();
    addMessage("Dhrubo", "Sorry, couldn't generate the image right now.");
  }
  setBusy(false);
});
