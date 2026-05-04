// app.js
let messages = JSON.parse(localStorage.getItem("chat")) || [];
// app.js


function saveMessages() {
    localStorage.setItem("chat", JSON.stringify(messages));
}

function renderMessages() {
    let chat = document.getElementById("chat");
    chat.innerHTML = "";

    messages.forEach(msg => {
        let div = createMessageElement(msg.text, msg.type, msg.isSQL);
        chat.appendChild(div);
    });

    chat.scrollTop = chat.scrollHeight;
}

async function send() {
	let button = document.querySelector("button");
	button.disabled = true;
    let input = document.getElementById("prompt");
    let userText = input.value;

    if (!userText) return;

    addMessage(userText, "user");
    input.value = "";

    let loading = addMessage("⚡ Generating SQL...", "ai");

    try {
        let res = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: userText,
                session_id: "default"
            })
        });

        console.log("STATUS:", res.status);

        let text = await res.text();
        console.log("RAW:", text);

        let data = JSON.parse(text);

        loading.remove();

        if (data.response) {
			let clean = data.response
				.replace(/```sql/gi, "")
				.replace(/```/g, "")
				.replace(/^\s+|\s+$/g, "")
				.trim();
		
			addMessage(clean, "ai", true);
		} else if (data.detail) {
            addMessage("❌ " + data.detail, "ai");
        } else {
            addMessage("⚠️ Unknown error", "ai");
        }

    } catch (err) {
        console.error("🔥 ERROR:", err);
        loading.remove();
        addMessage("⚠️ Check console", "ai");
    }
	button.disabled = false;
}

function addMessage(text, type, isSQL=false) {
    let chat = document.getElementById("chat");

    let msg = { text, type, isSQL };
    messages.push(msg);
    saveMessages();

    let div = createMessageElement(text, type, isSQL);
    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;

    return div;
}

function createMessageElement(text, type, isSQL=false) {
    let div = document.createElement("div");
    div.className = "message " + type;

    let content = document.createElement("div");

    if (isSQL) {
        let pre = document.createElement("pre");
        let code = document.createElement("code");

        code.className = "language-sql";
        code.innerText = text;

        pre.appendChild(code);
        content.appendChild(pre);

        setTimeout(() => Prism.highlightElement(code), 0);
    } else {
        content.innerText = text;
    }

    div.appendChild(content);

    return div;
}

function clearChat() {
    messages = [];
    saveMessages();
    renderMessages();
}

document.getElementById("prompt").addEventListener("keypress", function(e) {
    if (e.key === "Enter") send();
});

renderMessages();

