import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import mermaid from 'mermaid';
import './App.css';

const API_URL = "http://127.0.0.1:8000";

// Initialize Mermaid once
mermaid.initialize({ startOnLoad: true, theme: 'default' });

function App() {
  // --- State ---
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Documentation State
  const [docs, setDocs] = useState("");
  const [showDocs, setShowDocs] = useState(false);

  // Diagram State
  const [diagram, setDiagram] = useState("");
  const [diagramType, setDiagramType] = useState("class"); // 'class', 'usecase', 'erd'
  const [showDiagram, setShowDiagram] = useState(false);
  const [showRawCode, setShowRawCode] = useState(false); // Toggle for code preview
  const diagramRef = useRef(null); // For rendering logic

  // --- Handlers ---
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadStatus(""); 
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
      setChatHistory([]); 
      setShowDocs(false);
      setShowDiagram(false);
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
    setShowDocs(true);
    setShowDiagram(false); 
    try {
      const response = await axios.post(`${API_URL}/generate-docs`, { file_name: "" });
      setDocs(response.data.markdown_docs);
    } catch (error) {
      setDocs("Error generating documentation.");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDiagram = async () => {
    setLoading(true);
    setShowDiagram(true);
    setShowDocs(false); 
    setShowRawCode(false);
    try {
      // Send the selected diagram type in 'file_name' field
      const response = await axios.post(`${API_URL}/generate-diagram`, { file_name: diagramType });
      setDiagram(response.data.diagram_syntax);
    } catch (error) {
      setDiagram("Error generating diagram.");
    } finally {
      setLoading(false);
    }
  };

  // Function to Export Diagram as SVG
  const handleExportSVG = async () => {
    if (!diagram) return;
    
    const id = 'diagram-' + Date.now();
    try {
      const { svg } = await mermaid.render(id, diagram);
      const blob = new Blob([svg], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${diagramType}-diagram.svg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      alert("Failed to export SVG: " + error.message);
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

          {/* Action Buttons */}
          <button 
            className="button" 
            onClick={handleGenerateDocs} 
            disabled={loading}
            style={{marginTop: "20px", background: "#03dac6"}}
          >
            {loading ? "Generating..." : "Generate Documentation"}
          </button>

          <button 
            className="button" 
            onClick={handleGenerateDiagram} 
            disabled={loading}
            style={{marginTop: "10px", background: "#cf6679"}}
          >
            {loading ? "Generating..." : "Generate Diagram"}
          </button>

          <div className={`status-msg ${uploadStatus.includes("Error") ? "status-error" : "status-success"}`}>
            {uploadStatus}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="chat-area">
          
          {/* Navigation Tabs */}
          <div style={{display: "flex", gap: "10px", marginBottom: "20px", paddingBottom: "20px", borderBottom: "1px solid #333"}}>
            <button 
              onClick={() => { setShowDocs(false); setShowDiagram(false); }} 
              style={{
                padding: "5px 15px", 
                cursor: "pointer", 
                background: !showDocs && !showDiagram ? "#bb86fc" : "#2a2a2a", 
                border: "none", 
                color: "white", 
                borderRadius: "4px",
                fontWeight: "bold"
              }}
            >
              💬 Chat
            </button>
            <button 
              onClick={() => { setShowDocs(true); setShowDiagram(false); }} 
              style={{
                padding: "5px 15px", 
                cursor: "pointer", 
                background: showDocs && !showDiagram ? "#03dac6" : "#2a2a2a", 
                border: "none", 
                color: "white", 
                borderRadius: "4px",
                fontWeight: "bold"
              }}
            >
              📄 Documentation
            </button>
            <button 
              onClick={() => { setShowDocs(false); setShowDiagram(true); }} 
              style={{
                padding: "5px 15px", 
                cursor: "pointer", 
                background: showDiagram ? "#cf6679" : "#2a2a2a", 
                border: "none", 
                color: "white", 
                borderRadius: "4px",
                fontWeight: "bold"
              }}
            >
              🔷 Diagram
            </button>
          </div>

          {/* View Logic */}
          {showDiagram ? (
            <div style={{flex: 1, overflowY: "auto", background: "#1e1e1e", padding: "20px", borderRadius: "8px", display: "flex", flexDirection: "column", alignItems: "center"}}>
              <h3 style={{color: "#cf6679", marginBottom: "15px"}}>Visual Diagram Generator</h3>
              
              {/* Diagram Controls */}
              <div style={{display: "flex", gap: "10px", marginBottom: "15px", width: "100%", justifyContent: "center"}}>
                <select 
                    value={diagramType} 
                    onChange={(e) => setDiagramType(e.target.value)}
                    style={{padding: "5px", borderRadius: "4px", background: "#2a2a2a", color: "white", border: "none"}}
                  >
                    <option value="class">Class Diagram</option>
                    <option value="usecase">Use Case Diagram</option>
                    <option value="erd">ERD Diagram</option>
                  </select>
                
                <button 
                  onClick={handleGenerateDiagram}
                  style={{padding: "5px 10px", background: "#bb86fc", border: "none", color: "white", borderRadius: "4px"}}
                >
                  Generate
                </button>

                {diagram && (
                  <>
                    <button 
                      onClick={() => setShowRawCode(!showRawCode)}
                      style={{padding: "5px 10px", background: "#333", border: "1px solid #555", color: "white", borderRadius: "4px"}}
                    >
                      {showRawCode ? "Show Visual" : "Show Code"}
                    </button>
                    
                    <button 
                      onClick={handleExportSVG}
                      style={{padding: "5px 10px", background: "#03dac6", border: "none", color: "white", borderRadius: "4px"}}
                    >
                      📥 Export SVG
                    </button>
                  </>
                )}
              </div>

              {/* View Mode */}
              {showRawCode ? (
                 <div style={{width: "100%", background: "#121212", padding: "15px", borderRadius: "8px", color: "#e0e0e0", fontSize: "0.8rem"}}>
                    <h4 style={{marginTop: 0, marginBottom: "10px"}}>Mermaid Code:</h4>
                    <pre style={{whiteSpace: "pre-wrap", fontFamily: "monospace", margin: 0}}>{diagram}</pre>
                 </div>
              ) : (
                 <div style={{width: "100%", background: "#fff", borderRadius: "8px", padding: "20px", overflow: "auto"}}>
                   {/* Mermaid Text Block - This will auto-render */}
                   <div className="mermaid">
                     {diagram}
                   </div>
                 </div>
              )}
            </div>
          ) : showDocs ? (
            <div style={{flex: 1, overflowY: "auto", background: "#1e1e1e", padding: "20px", borderRadius: "8px", whiteSpace: "pre-wrap", fontFamily: "monospace"}}>
               <div dangerouslySetInnerHTML={{__html: docs.replace(/\n/g, "<br>")}} />
            </div>
          ) : (
            // Chat View
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

          {/* Input Area (Only show in Chat mode) */}
          {!showDocs && !showDiagram && (
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
          )}
        </main>

      </div>
    </div>
  );
}

export default App;