import React, { useState } from "react";

const API_URL = "http://localhost:8000/ask";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setLoading(true);

    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: input,
        history: newMessages,
      }),
    });

    const data = await res.json();
    if (data.response) {
      setMessages([...newMessages, { role: "agent", content: data.response }]);
    } else {
      setMessages([...newMessages, { role: "agent", content: data.error || "Error" }]);
    }

    setInput("");
    setLoading(false);
  };

  return (
    <div className="app-container">
      <h2 style={{ textAlign: "center" }}>PartSelect Chat Agent</h2>
      <div className="message" style={{ marginBottom: "1rem", width: "60%", margin: "0 auto"  }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ 
            textAlign: msg.role === "user" ? "right" : "left", 
            padding: "5px 0"
          }}>
            <div style={{
              display: "inline-block",
              backgroundColor: "white",
              padding: "8px 12px",
              borderRadius: "12px",
              maxWidth: "70%",
              boxShadow: "0 1px 2px rgba(0,0,0,0.1)"
            }}>
              <strong>{msg.role === "user" ? "You" : "Agent"}:</strong> {msg.content}
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', width: '75%', margin: "0 auto", padding: '10px' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask something..."
          style={{ flexGrow: 1, marginRight: '10px' }}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
