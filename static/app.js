id="clean1"
function cleanSQL(text) {
    return text
        .replace(/```sql/g, "")
        .replace(/```/g, "")
        .trim();
}
async function askAI() {

    const questionInput = document.getElementById("question");
    const chatBox = document.getElementById("chatBox");

    const question = questionInput.value.trim();

    if (!question) return;

    chatBox.innerHTML += `
        <div class="message user">
            <strong>You:</strong>
            <p>${question}</p>
        </div>
    `;

    chatBox.innerHTML += `
        <div class="message loading" id="loading">
            ⏳ Generating SQL...
        </div>
    `;

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

			chatBox.innerHTML += `
				<div class="message ai">
					<strong>DataNex AI:</strong>
					<pre>${cleanResponse}</pre>
				</div>
			`;
			/*
			chatBox.innerHTML += `
				<div class="message ai">
					<strong>DataNex AI:</strong>
					<pre>${data.response}</pre>
				</div>
			`;
		    */
		} else {
		
			chatBox.innerHTML += `
				<div class="message error">
					❌ ${data.error || data.detail || "Unknown Error"}
				</div>
			`;
		}

    } catch (error) {

        const loading = document.getElementById("loading");

		if (loading) {
		loading.remove();
		}

        chatBox.innerHTML += `
            <div class="message error">
                ❌ Error generating SQL
            </div>
        `;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}