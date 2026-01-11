import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // New State for Documentation Feature
  const [docs, setDocs] = useState("");
  const [showDocs, setShowDocs] = useState(false);

  // --- Handlers ---
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadStatus(""); // Clear old status
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus("Please select a .zip file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadStatus("Codebase indexed successfully!");
      setChatHistory([]); // Clear chat history on new upload
    } catch (error) {
      setUploadStatus("Error uploading file.");
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;

    const newHistory = [...chatHistory, { role: "user", content: question }];
    setChatHistory(newHistory);
    setQuestion("");
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/ask`, { question: question });
      setChatHistory([
        ...newHistory,
        { role: "ai", content: response.data.answer },
      ]);
    } catch (error) {
      setChatHistory([
        ...newHistory,
        { role: "ai", content: "Error: Could not connect to server or no codebase uploaded." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDocs = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/generate-docs`, { file_name: "" });
      setDocs(response.data.markdown_docs);
      setShowDocs(true);
    } catch (error) {
      setDocs("Error generating documentation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      
      {/* Header */}
      <header className="app-header">
        <div>
          <h1>AI-Driven Documentation Assistant</h1>
          <p>FYP Backend Demo</p>
        </div>
      </header>

      <div className="main-container">
        
        {/* Sidebar: Upload Section */}
        <aside className="sidebar">
          <h3>1. Codebase</h3>
          
          <input 
            type="file" 
            id="zipInput" 
            accept=".zip" 
            style={{ display: 'none' }} 
            onChange={handleFileChange} 
          />
          
          <label htmlFor="zipInput" className="upload-area">
            <div style={{fontSize: '2rem'}}>📂</div>
            <p>Click to Upload .zip</p>
            {file && <p style={{color: '#bb86fc', fontWeight: 'bold'}}>{file.name}</p>}
          </label>

          <button 
            className="button" 
            onClick={handleUpload} 
            disabled={loading}
          >
            {loading ? "Processing..." : "Upload & Index"}
          </button>

          {/* New Feature: Generate Docs Button */}
          <button 
            className="button" 
            onClick={handleGenerateDocs} 
            disabled={loading}
            style={{marginTop: "20px"}}
          >
            {loading ? "Generating..." : "Generate Documentation"}
          </button>

          <div className={`status-msg ${uploadStatus.includes("Error") ? "status-error" : "status-success"}`}>
            {uploadStatus}
          </div>
        </aside>

        {/* Chat Section */}
        <main className="chat-area">
          
          {/* Toggle between Chat and Docs View */}
          <div style={{display: "flex", justifyContent: "flex-end", marginBottom: "20px"}}>
            <button 
              onClick={() => setShowDocs(!showDocs)}
              style={{padding: "5px 10px", cursor: "pointer", background: "#bb86fc", border: "none", color: "white", borderRadius: "4px"}}
            >
              {showDocs ? "Show Chat" : "Show Documentation"}
            </button>
          </div>

          {showDocs ? (
            <div style={{flex: 1, overflowY: "auto", background: "#1e1e1e", padding: "20px", borderRadius: "8px", whiteSpace: "pre-wrap", fontFamily: "monospace"}}>
               <div dangerouslySetInnerHTML={{__html: docs.replace(/\n/g, "<br>")}} />
            </div>
          ) : (
            // Existing Chat History Code
            <div className="chat-history">
              {chatHistory.length === 0 && (
                <div style={{textAlign:'center', color:'#555', marginTop:'50px'}}>
                  <h3>No questions yet.</h3>
                  <p>Upload a codebase to start chatting!</p>
                </div>
              )}
              
              {chatHistory.map((msg, index) => (
                <div key={index} className={`message ${msg.role}`}>
                  <div className="sender">{msg.role === "user" ? "You" : "AI Assistant"}</div>
                  <div className="bubble">{msg.content}</div>
                </div>
              ))}
              
              {loading && (
                <div className="message ai">
                  <div className="sender">AI Assistant</div>
                  <div className="bubble" style={{color: '#888'}}>Thinking...</div>
                </div>
              )}
            </div>
          )}

          <div className="input-area">
            <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your code..."
                onKeyPress={(e) => { if(e.key === 'Enter' && !loading) handleAsk() }}
              />
            <button onClick={handleAsk} disabled={loading}>Send</button>
          </div>
        </main>

      </div>
    </div>
  );
}

export default App;