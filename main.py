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

    if "messages" not in st.session_state:
        st.session_state.messages = []

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

            st.markdown("### 📘 Preview")
            st.markdown(markdown_output)

            st.download_button(
                "📥 Download Markdown",
                markdown_output,
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
        st.stop()

    col_sel, col_btn = st.columns([2, 1])

    with col_sel:
        diagram_selection = st.selectbox(
            "Choose Diagram Type",
            ["Class Diagram", "ERD Diagram", "Use Case Diagram"]
        )

    with col_btn:
        st.write("")
        st.write("")
        generate = st.button("🎨 Generate", type="primary", use_container_width=True)

    if not generate:
        st.stop()

    col_mermaid, col_preview = st.columns([1, 1.6])

    # --------------------------
    # COLUMN 1 — MERMAID SOURCE
    # --------------------------
    with col_mermaid:
        st.subheader("💻 Mermaid Code")

        with st.spinner("Generating diagram..."):
            analysis, clean_mermaid = services.diagram_generator.generate_diagram(
                code_content, diagram_selection,api_key)
            

        if not clean_mermaid:
            st.error("Diagram generation failed.")
            st.stop()

        with st.expander("🧠 AI Analysis"):
            st.markdown(analysis)

        st.code(clean_mermaid, language="markdown", height=720)

    # --------------------------
    # COLUMN 2 — LIVE PREVIEW
    # --------------------------
    with col_preview:
        st.subheader("👁️ Live Preview")

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

.mermaid {{
    flex: 1;
    width: 100%;
    overflow: hidden;
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
        <button onclick="zoomIn()">➕</button>
        <button onclick="zoomOut()">➖</button>
        <button onclick="resetZoom()">🔄</button>
        <div style="flex:1"></div>
        <button onclick="exportSVG()">💾 SVG</button>
        <button onclick="exportPNG()">🖼️ PNG</button>
    </div>

    <div class="mermaid" id="diagram-{unique_id}">
{clean_mermaid}
    </div>
</div>

<script>
let panZoom = null;

function initPanZoom() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (!svg) return;

    panZoom = svgPanZoom(svg, {{
        zoomEnabled: true,
        fit: true,
        center: true,
        minZoom: 0.2,
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
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svg);
    const blob = new Blob([source], {{type: 'image/svg+xml'}});
    download(URL.createObjectURL(blob), 'diagram.svg');
}}

function exportPNG() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    const bbox = svg.getBBox();
    const scale = 3;

    canvas.width = bbox.width * scale;
    canvas.height = bbox.height * scale;

    img.onload = function () {{
        ctx.scale(scale, scale);
        ctx.drawImage(img, 0, 0);
        download(canvas.toDataURL('image/png'), 'diagram.png');
    }};

    img.src = URL.createObjectURL(new Blob([svgStr], {{type: 'image/svg+xml'}}));
}}

function download(url, filename) {{
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}}

const observer = new MutationObserver(() => {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (svg && !panZoom) {{
        initPanZoom();
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

        components.html(html, height=760, scrolling=False)
