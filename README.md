Your README is already very good, but it needs a few minor updates to perfectly match the latest changes we made to the code (specifically the ZIP upload feature, the editable diagram text area, the `pydantic-settings` requirement, and the new "WhatsApp-style" auto-scroll chat).

Here is the updated and fully aligned version:

---

# AureliaScript: AI-Powered Code Intelligence

> An AI-powered code intelligence platform that transforms source code into structured documentation, interactive diagrams, and insightful chat conversations.

---

## Table of Contents

* [Overview](#overview)
* [Key Features](#key-features)
* [Architecture](#architecture)
* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Project Structure](#project-structure)
* [API Reference](#api-reference)
* [Storage](#storage)
* [Supported Languages](#supported-languages)
* [Troubleshooting](#troubleshooting)
* [License](#license)

---

## Overview

**AureliaScript** is a developer tool designed to bridge the gap between raw code and human understanding. Built for developers, by developers, it leverages OpenAI's language models and a Retrieval-Augmented Generation (RAG) architecture to provide real-time code analysis, automated technical documentation, and multi-format diagram generation.

Whether you're onboarding onto a legacy codebase, auditing architecture, or generating compliance documentation, AureliaScript provides the intelligence layer to make source code accessible and actionable across 30+ programming languages.

## Key Features

* **💬 Chat with Code**: Context-aware AI assistant that answers specific questions about your uploaded logic. Powered by RAG (Retrieval-Augmented Generation) to ensure responses are grounded in your actual source code. Features a "WhatsApp-style" chat interface with right-aligned user messages and auto-scrolling.
* **📝 Documentation Generator**: Produces professional Markdown documentation following strict technical writing standards. The AI adopts a "Professional Technical Writer" persona, enforcing header hierarchies, table structures, and code block conventions.
* **📊 Interactive Diagrams**: Generates Mermaid.js visualizations including:
  * **Class Diagrams**: For structural analysis and object-oriented design mapping.
  * **ERD Diagrams**: For data relationship mapping and schema visualization.
  * **Use Case Diagrams**: For functional flow overview and actor interaction mapping.
  * **Sequence Diagrams**: For message flow tracing between components and API interactions.
  * **Activity Diagrams**: For control flow visualization, decision logic, and process steps.
* **👁️ Live Preview & Editable Source**: A custom-built SVG viewer with pan, zoom, and export (PNG/SVG) capabilities. The Mermaid source code is fully editable in the UI, allowing users to manually fix minor AI syntax errors and instantly re-render the preview.
* **🕐 Session Management**: Persistent chat history with semantic search. Resume past sessions with full code and conversation context restored without needing to re-upload files.
* **🔌 MCP Integration**: The AI assistant autonomously retrieves past conversation context through standardized Model Context Protocol (MCP) tool calls.
* **🌐 Multi-Language & ZIP Support**: Accepts single source code files in 30+ programming languages, or entire project repositories packaged as `.zip` archives.

## Architecture

The application is built with a focus on maintainability and clean code principles:

| Component | Description |
| --- | --- |
| **Frontend** | Streamlit (Multi-tab interface) |
| **Patterns** | **Factory & Strategy Patterns** for flexible diagram generation. |
| **RAG Engine** | **OpenAI Embeddings + VectorStore** for context-aware code retrieval. |
| **Persistence** | **ChromaDB** for session logs, code storage, and semantic search. |
| **AI Integration** | **MCP (Model Context Protocol)** for autonomous session context retrieval. |
| **Rendering** | Client-side Mermaid.js with `svg-pan-zoom` via Streamlit Components. |
| **AI Engine** | OpenAI API (GPT-4o-mini by default). |

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/your-repo/aureliascript.git
cd aureliascript
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```
*(Note: `requirements.txt` includes `openai`, `streamlit`, `chromadb`, `mcp`, and `pydantic-settings`)*

3. **Configure API key (optional — for "Use default key" feature)**:

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Windows (PowerShell — current session):**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Windows (PowerShell — permanent, user-level):**
```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-your-key-here", "User")
```

4. **Run the application**:
```bash
streamlit run main.py
```

## Configuration

The application relies on a `config.py` file to manage its behavior. You can adjust the following parameters:

* `OPENAI_MODEL`: Set your preferred model (default: `gpt-4o-mini`).
* `DOC_STRUCTURE_RULES`: Defines the "Professional Technical Writer" persona and formatting constraints for the documentation engine.
* `DIAGRAM_RULES`: Contains prompt templates and few-shot examples for each diagram type (`CLASS_DIAGRAM`, `ERD_DIAGRAM`, `USE_CASE_DIAGRAM`, `SEQUENCE_DIAGRAM`, `ACTIVITY_DIAGRAM`).
* `SESSION_DATA_DIR`: ChromaDB persistence directory for session logs and code storage (default: `./session_data`).

## Usage

1. **API Key**: Launch the app and select an API key option in the sidebar:
   * **Use your own OpenAI key** — Paste your key directly.
   * **Use default key** — Loads from the `OPENAI_API_KEY` environment variable.

2. **Upload**: Provide a source code file (`.py`, `.js`, `.java`, etc.) or a `.zip` archive containing multiple project files. Extracted ZIP files are automatically concatenated with file-path headers for AI context.

3. **Interact**:
   * Use the **Chat** tab to ask *"What does this function do?"* or *"What did we discuss about authentication last time?"*
   * Use the **Documentation** tab to generate a full README-style guide.
   * Use the **Diagrams** tab to visualize class structures, data relationships, message flows, and control logic. Edit the Mermaid source directly in the left panel if needed.

4. **Session Management**:
   * **Resume** past sessions from the sidebar to restore chat history and uploaded code.
   * **Search** across all past conversations using natural language.
   * **Delete** individual sessions to manage storage.

## Project Structure

```
aureliascript/
├── main.py                     # Streamlit application entry point
├── config.py                   # AI model & prompt configuration
├── requirements.txt            # Python dependencies
│
├── services/
│   ├── vector_store.py         # RAG engine (OpenAI embeddings + cosine similarity)
│   ├── session_store.py        # ChromaDB-backed session persistence & semantic search
│   ├── mcp_bridge.py           # OpenAI ↔ MCP tool bridge (function calling)
│   ├── diagram_generator.py    # Factory + Strategy pattern for diagram generation
│   ├── doc_generator.py        # Documentation generation service
│   └── questions.py            # Chat Q&A service (RAG + session context)
│
├── mcp_server/
│   ├── __init__.py
│   └── server.py               # Standalone MCP server (FastMCP)
│
└── session_data/               # ChromaDB persistence directory (auto-created)
```

## API Reference

### VectorStore
Manages code chunking, embedding generation, and similarity-based retrieval for RAG.

| Method | Parameters | Returns | Description |
| --- | --- | --- | --- |
| `build(code_content)` | `str` | — | Splits code into chunks and generates embeddings |
| `retrieve(query, top_k)` | `str, int` | `str` | Returns concatenated context from top-k relevant chunks |

### SessionStore
ChromaDB-backed persistent storage for session logs, uploaded code, and metadata.

| Method | Parameters | Returns | Description |
| --- | --- | --- | --- |
| `create_session()` | — | `str` | Creates a new session ID |
| `list_sessions()` | — | `List[Dict]` | Lists all sessions with metadata (including filenames) |
| `delete_session(session_id)` | `str` | `bool` | Deletes a session and all associated data |
| `save_conversation_turn(session_id, user_msg, assistant_msg)` | `str, str, str` | — | Saves a complete chat turn |
| `save_code_content(session_id, code_content)` | `str, str` | — | Persists uploaded source code (up to 200k chars) |
| `get_code_content(session_id)` | `str` | `str` | Retrieves the uploaded code for a session |
| `save_metadata(session_id, key, value)` | `str, str, str` | — | Saves metadata (e.g., `system_filename`) |
| `search_sessions(query, n_results)` | `str, int` | `List[Dict]` | Semantic search across all sessions |

### DiagramFactory
Factory class that instantiates the appropriate `DiagramStrategy` based on user selection.

| Method | Parameters | Returns | Description |
| --- | --- | --- | --- |
| `create(selection)` | `str` | `DiagramStrategy` | Returns the correct strategy instance |

### MCP Bridge
Maps MCP session tools to OpenAI function-calling format for autonomous session context retrieval.

| Tool | Description |
| --- | --- |
| `search_past_conversations` | Semantic search across all past chat sessions |
| `get_session_history` | Retrieve full history for a specific session |
| `list_all_sessions` | List all past conversation sessions |

## Storage

### Disk Usage Estimates

| Component | Size per 1,000 Messages |
| --- | --- |
| ChromaDB (vectors + documents + index) | ~5–10 MB |
| MCP server process | 0 MB on disk (protocol only) |

ChromaDB uses a single persistent store (DuckDB + Parquet internally). There is no duplicate storage—vectors, documents, and metadata coexist in the same collection.

### Data Isolation

Each session is isolated via the `session_id` metadata filter (using `$and` operators). Uploaded code is stored with the `system_code` role, and filenames with `system_filename`, ensuring they are excluded from chat context and semantic search results.

## Supported Languages

AureliaScript accepts source code in the following languages:

| Category | Languages |
| --- | --- |
| **Web & Frontend** | JavaScript, TypeScript, JSX, TSX, HTML, CSS, Vue, Svelte |
| **Backend & Systems** | Python, Java, C, C++, C#, Go, Rust, PHP, Ruby |
| **Mobile** | Swift, Kotlin, Dart |
| **Data & Config** | SQL, YAML, TOML, JSON, XML, Markdown |
| **Scripting** | Shell/Bash, PowerShell, Lua, R, Scala |
| **Other** | Protocol Buffers, Dockerfile, .env, .gitignore, ZIP Archives |

Custom or unrecognized file extensions are read as plain text with a warning.

## Troubleshooting

| Issue | Solution |
| --- | --- |
| `pip is not recognized` | Use `python -m pip install ...` or `py -3.12 -m pip install ...` |
| `PydanticImportError: BaseSettings` | Run `pip install pydantic-settings` (already in requirements.txt) |
| Python 3.14 compatibility errors | Install Python 3.12 and run with `py -3.12 -m streamlit run main.py` |
| `OPENAI_API_KEY` not found | Ensure the environment variable is set and PowerShell has been restarted |
| Diagrams fail to render | Edit the Mermaid source in the left panel to fix syntax errors, then press `Ctrl+Enter`. |
| Session history shows "No file" | Sessions created before the filename feature was added will not display filenames. Delete old sessions and create new ones. |
| ZIP file fails to upload | Ensure the archive is not corrupted and contains text-based source files, not binary files. |

## License

This project is developed for academic purposes (FYP 2). All rights reserved.

---

### Footer

*Developed with Streamlit, OpenAI, and ChromaDB* | [Report Bug](https://github.com/your-repo/aureliascript/issues)
