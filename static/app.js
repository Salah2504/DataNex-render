const chatBox = document.getElementById("chatBox");
id="clean1"
function cleanSQL(text) {
    return text
        .replace(/```sql/g, "")
        .replace(/```/g, "")
        .trim();
}

function addMessage(type, content) {
    const div = document.createElement("div");
    div.className = `message ${type}`;

    if (type === "loading") {
        div.id = "loading";
    }

    div.innerHTML = content;
    chatBox.appendChild(div);

    chatBox.scrollTop = chatBox.scrollHeight;
}

async function askAI() {

    const questionInput = document.getElementById("question");
    
    const question = questionInput.value.trim();

    if (!question) return;
	addMessage("user", `<strong>You:</strong><p>${question}</p>`);

	addMessage("loading", `⏳ Generating SQL...`);

    questionInput.value = "";

    try {

        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                session_id: "web-user"
            })
        });

        const data = await response.json();

		console.log(data);
		
		const loading = document.getElementById("loading");

		if (loading) {
		loading.remove();
		}
		
		if (data.response) {
			let cleanResponse = cleanSQL(data.response);
			addMessage("ai", `<strong>DataNex AI:</strong><pre>${cleanResponse}</pre>`);

		} else {
			addMessage("error", `❌ ${data.error || data.detail || "Unknown Error"}`);

		}

    } catch (error) {

        const loading = document.getElementById("loading");

		if (loading) {
		loading.remove();
		}
		addMessage("error", `❌ Error generating SQL`);

    }

 }