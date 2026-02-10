from openai import OpenAI
import os
import streamlit as st
import streamlit.components.v1 as components
import uuid

# Import modules
import config
import services.diagram_generator
import services.doc_generator
import services.questions

# ==========================
# PAGE SETUP
# ==========================
st.set_page_config(
    page_title="AureliaScript",
    layout="wide"
)

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Enter your API Key", type="password")
    st.markdown("---")
    st.info("Architecture: Factory + Strategy + Client-side rendering")

if not api_key:
    st.warning("Please enter your API Key.")
    st.stop()

client = OpenAI(api_key=api_key)

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_content" not in st.session_state:
    st.session_state.doc_content = None
if "mermaid_code" not in st.session_state:
    st.session_state.mermaid_code = None
if "mermaid_analysis" not in st.session_state:
    st.session_state.mermaid_analysis = None
if "current_diagram_type" not in st.session_state:
    st.session_state.current_diagram_type = "Class Diagram"

# ==========================
# FILE UPLOAD
# ==========================
st.header("📄 Upload Python Code")
uploaded_file = st.file_uploader("Choose a .py file", type=["py"])

code_content = ""
if uploaded_file:
    code_content = uploaded_file.read().decode("utf-8")
    with st.expander("📂 View Uploaded Code"):
        st.code(code_content, language="python")

# ==========================
# TABS
# ==========================
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📝 Documentation", "📊 Diagrams"])

# ==========================
# TAB 1 — CHAT
# ==========================
with tab1:
    st.header("Chat with Code")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask something about the code..."):
        if not code_content:
            st.warning("Upload a file first.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Thinking..."):
                answer = services.questions.get_answer(
                    code_content,
                    prompt,
                    api_key
                )

            with st.chat_message("assistant"):
                st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})

# ==========================
# TAB 2 — DOCUMENTATION
# ==========================
with tab2:
    st.header("Documentation Generator")

    if st.button("🚀 Generate Documentation", type="primary"):
        if not code_content:
            st.error("Please upload a Python file.")
        else:
            with st.spinner("Generating documentation..."):
                markdown_output = services.doc_generator.generate_documentation(code_content, api_key)
                st.session_state.doc_content = markdown_output

    if st.session_state.doc_content:
        st.markdown("### 📘 Preview")
        st.markdown(st.session_state.doc_content)

        st.download_button(
            "📥 Download Markdown",
            st.session_state.doc_content,
            "Documentation.md",
            "text/markdown"
        )

# ==========================
# TAB 3 — DIAGRAMS
# ==========================
with tab3:
    st.header("Generate Diagrams")

    if not code_content:
        st.info("Upload a Python file to generate diagrams.")
    else:
        # Controls
        col_sel, col_btn = st.columns([2, 1])

        with col_sel:
            diagram_selection = st.selectbox(
                "Choose Diagram Type",
                ["Class Diagram", "ERD Diagram", "Use Case Diagram"],
                index=["Class Diagram", "ERD Diagram", "Use Case Diagram"].index(st.session_state.current_diagram_type)
            )

        with col_btn:
            st.write("")
            st.write("")
            generate = st.button("🎨 Generate", type="primary", use_container_width=True)

        # Generation Logic
        if generate:
            st.session_state.current_diagram_type = diagram_selection
            with st.spinner("Generating diagram..."):
                analysis, clean_mermaid = services.diagram_generator.generate_diagram(
                    code_content, diagram_selection, api_key
                )
                st.session_state.mermaid_analysis = analysis
                st.session_state.mermaid_code = clean_mermaid

        # Display Layout
        if st.session_state.mermaid_code:
            with st.container():
                # Equal width columns (1:1) to ensure they appear side-by-side
                col_code, col_preview = st.columns([1, 1], gap="small")

                # --------------------------
                # LEFT COLUMN — MERMAID CODE
                # --------------------------
                with col_code:
                    st.write("💻 **Mermaid Source**")
                    # Display code first to align tops with the preview
                    st.code(st.session_state.mermaid_code, language="markdown", height=750)
                    
                    # Move analysis to bottom so it doesn't push code down
                    if st.session_state.mermaid_analysis:
                        with st.expander("🧠 AI Analysis"):
                            st.markdown(st.session_state.mermaid_analysis)

                # --------------------------
                # RIGHT COLUMN — LIVE PREVIEW
                # --------------------------
                with col_preview:
                    st.write("👁️ **Live Preview**")

                    unique_id = uuid.uuid4().hex[:8]

                    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    window.mermaid = mermaid;
    mermaid.initialize({{
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose'
    }});
</script>

<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>

<style>
html, body {{
    margin: 0;
    padding: 0;
    height: 100%;
    width: 100%;
    overflow: hidden;
    background: #f5f5f5;
    font-family: sans-serif;
}}

.container {{
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
}}

.toolbar {{
    height: 40px;
    padding: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
    background: #fafafa;
    border-bottom: 1px solid #ddd;
}}

.toolbar button {{
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 14px;
}}
.toolbar button:hover {{
    background: #e6e6e6;
}}

.mermaid {{
    flex: 1;
    width: 100%;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px;
}}

.mermaid svg {{
    width: 100% !important;
    height: 100% !important;
}}
</style>
</head>

<body>
<div class="container">
    <div class="toolbar">
        <button onclick="zoomIn()" title="Zoom In">➕</button>
        <button onclick="zoomOut()" title="Zoom Out">➖</button>
        <button onclick="resetZoom()" title="Reset Zoom">🔄</button>
        <div style="flex:1"></div>
        <button onclick="exportSVG()" title="Download as SVG">💾 SVG</button>
        <button onclick="exportPNG()" title="Download as PNG">🖼️ PNG</button>
    </div>

    <div class="mermaid" id="diagram-{unique_id}">
{st.session_state.mermaid_code}
    </div>
</div>

<script>
let panZoom = null;

function initPanZoom() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (!svg) return;
    
    svg.addEventListener("wheel", function(e) {{
        if (e.ctrlKey) {{
            e.preventDefault();
        }}
    }}, {{ passive: false }});

    panZoom = svgPanZoom(svg, {{
        zoomEnabled: true,
        fit: true,
        center: true,
        minZoom: 0.1,
        maxZoom: 10
    }});
}}

function zoomIn() {{ panZoom?.zoomIn(); }}
function zoomOut() {{ panZoom?.zoomOut(); }}
function resetZoom() {{
    panZoom?.resetZoom();
    panZoom?.center();
}}

function exportSVG() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (!svg) return;
    
    const clone = svg.cloneNode(true);
    if (!clone.getAttribute('xmlns')) {{
        clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    }}
    
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(clone);
    const blob = new Blob([source], {{type: 'image/svg+xml;charset=utf-8'}});
    download(URL.createObjectURL(blob), 'diagram.svg');
}}

function exportPNG() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (!svg) return;

    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);
    
    const img = new Image();
    const svgBlob = new Blob([svgStr], {{type: 'image/svg+xml;charset=utf-8'}});
    const url = URL.createObjectURL(svgBlob);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    img.onload = function() {{
        const bbox = svg.getBBox();
        const padding = 20;
        const scale = 2;
        
        let width = bbox.width + padding * 2;
        let height = bbox.height + padding * 2;
        
        if (svg.viewBox.baseVal) {{
             width = svg.viewBox.baseVal.width;
             height = svg.viewBox.baseVal.height;
        }}
        
        canvas.width = width * scale;
        canvas.height = height * scale;
        
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.scale(scale, scale);
        ctx.drawImage(img, 0, 0, width, height);
        
        download(canvas.toDataURL('image/png'), 'diagram.png');
        URL.revokeObjectURL(url);
    }};

    img.onerror = function() {{
        console.error("Error loading SVG into image");
        URL.revokeObjectURL(url);
    }}

    img.src = url;
}}

function download(url, filename) {{
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}}

const observer = new MutationObserver(() => {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (svg && !panZoom) {{
        setTimeout(initPanZoom, 100);
        observer.disconnect();
    }}
}});

observer.observe(document.getElementById('diagram-{unique_id}'), {{
    childList: true,
    subtree: true
}});
</script>
</body>
</html>
"""
            # Height set to match the code box (750) + header space
            components.html(html, height=790, scrolling=False)
