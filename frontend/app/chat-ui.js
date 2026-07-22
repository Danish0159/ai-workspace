"use client";

import { useState } from "react";

export default function ChatUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [indexed, setIndexed] = useState(false);

  async function handleUpload(e) {
    const fileList = e.target.files;
    if (!fileList?.length) return;

    setUploading(true);
    setIndexed(false);
    const formData = new FormData();
    for (const file of fileList) {
      formData.append("files", file);
    }

    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();
    setUploading(false);
    if (res.ok && data.status === "indexed") {
      setIndexed(true);
    }
    e.target.value = "";
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });
    const data = await res.json();
    const answer = res.ok ? data.answer : data.detail || "Something went wrong";
    setMessages((prev) => [...prev, { role: "ai", content: answer }]);
  }

  return (
    <main style={{ maxWidth: 600, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>RAG Chat</h1>
      <div>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={handleUpload}
          disabled={uploading}
        />
        {uploading && <span> Indexing...</span>}
        {!uploading && indexed && <span> Documents indexed — you can chat now.</span>}
      </div>
      <div style={{ margin: "1rem 0", minHeight: 200 }}>
        {messages.map((msg, i) => (
          <p key={i}>
            <strong>{msg.role === "user" ? "You" : "AI"}:</strong> {msg.content}
          </p>
        ))}
      </div>
      <form onSubmit={handleSend}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your documents..."
          style={{ width: "70%", marginRight: 8 }}
        />
        <button type="submit">Send</button>
      </form>
    </main>
  );
}
