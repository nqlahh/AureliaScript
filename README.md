# AureliaScript: AI-Powered Code Intelligence

> A Streamlit-based workspace that transforms Python source code into structured documentation, interactive diagrams, and insightful chat conversations.

---

## Table of Contents

* [Overview](https://www.google.com/search?q=%23overview)
* [Key Features](https://www.google.com/search?q=%23key-features)
* [Architecture](https://www.google.com/search?q=%23architecture)
* [Installation](https://www.google.com/search?q=%23installation)
* [Configuration](https://www.google.com/search?q=%23configuration)
* [Usage](https://www.google.com/search?q=%23usage)

---

## Overview

**AureliaScript** is a developer tool designed to bridge the gap between raw code and human understanding. By leveraging OpenAI's models, it provides an automated way to generate technical debt-reducing assets like UML diagrams and comprehensive Markdown documentation directly from uploaded Python files.

## Key Features

* **💬 Chat with Code**: Context-aware AI assistant that answers specific questions about your uploaded logic.
* **📝 Documentation Generator**: Produces professional Markdown documentation following strict technical writing standards.
* **📊 Interactive Diagrams**: Generates Mermaid.js visualizations including:
* **Class Diagrams**: For structural analysis.
* **ERD Diagrams**: For data relationship mapping.
* **Use Case Diagrams**: For functional flow overview.


* **👁️ Live Preview**: A custom-built SVG viewer with pan, zoom, and export (PNG/SVG) capabilities.

## Architecture

The application is built with a focus on maintainability and clean code principles:

| Component | Description |
| --- | --- |
| **Frontend** | Streamlit (Multi-tab interface) |
| **Patterns** | **Factory & Strategy Patterns** for flexible diagram generation. |
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
pip install -r requirement.txt

```


3. **Run the application**:
```bash
streamlit run main.py

```



## Configuration

The application relies on a `config.py` file to manage its behavior. You can adjust the following parameters:

* `OPENAI_MODEL`: Set your preferred model (default: `gpt-4o-mini`).
* `DOC_STRUCTURE_RULES`: Defines the "Professional Technical Writer" persona and formatting constraints for the documentation engine.

## Usage

1. **API Key**: Launch the app and enter your OpenAI API key in the sidebar.
2. **Upload**: Provide a `.py` file for analysis.
3. **Interact**:
* Use the **Chat** tab to ask "What does this function do?"
* Use the **Documentation** tab to generate a full README-style guide.
* Use the **Diagrams** tab to visualize your class structures.



---

### Footer

*Developed with Streamlit and OpenAI* | [Report Bug](https://www.google.com/search?q=https://github.com/your-repo/aureliascript/issues)
