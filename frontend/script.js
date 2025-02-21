async function createNote() {
    let noteContent = document.getElementById("noteContent").value;
    let response = await fetch("/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: noteContent, expire_time: 300 })
    });
    let data = await response.json();
    document.getElementById("link").innerHTML = `<a href="${data.note_url}">${data.note_url}</a>`;
}
