from openai import OpenAI
import os
import streamlit as st
import streamlit.components.v1 as components
import uuid
import zipfile
import io  # Moved to top

from services.session_store import SessionStore
from services.questions import get_answer

# Import modules
import config
import services.diagram_generator
import services.doc_generator
import services.questions

# ==========================
# HELPER: LANGUAGE DETECTION
# ==========================
def get_language_from_filename(filename):
    """Map file extension to Streamlit code block language."""
    if not filename:
        return "text"
    ext = filename.rsplit('.', 1)[-1].lower()
    mapping = {
        "py": "python", "js": "javascript", "ts": "typescript",
        "jsx": "jsx", "tsx": "tsx", "java": "java", "c": "c",
        "cpp": "cpp", "h": "c", "hpp": "cpp", "cs": "csharp",
        "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
        "swift": "swift", "kt": "kotlin", "html": "html", "css": "css",
        "sql": "sql", "sh": "bash", "yaml": "yaml", "yml": "yaml",
        "json": "json", "xml": "xml", "md": "markdown", "r": "r",
        "scala": "scala", "lua": "lua", "dart": "dart", "vue": "html",
    }
    return mapping.get(ext, "text")

# ==========================
# PAGE SETUP
# ==========================
st.set_page_config(
    page_title="AureliaScript",
    layout="wide"
)

# ==========================
# CACHED SESSION STORE
# ==========================
@st.cache_resource
def get_session_store():
    return SessionStore()

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.header("⚙️ Settings")

    col1, col2 = st.columns(2)

    with col1:
        use_own_key = st.checkbox("Use your own OpenAI key")
    with col2:
        use_env_key = st.checkbox("Use default key")

    # Ensure mutual exclusivity
    if use_own_key and use_env_key:
        st.warning("Please select only one option.")
        api_key = ""

    elif use_own_key:
        st.markdown(
            "🔑 **Get your API key:** Go to [OpenAI API Keys](https://platform.openai.com/api-keys) → "
            "Log in → Click **'Create new secret key'** → Copy and paste it below."
        )
        api_key = st.text_input("Enter your OpenAI API Key", type="password")

    elif use_env_key:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            st.success("✅ Default API key loaded successfully.")
        else:
            st.error("❌ No API key found in environment. Please contact the administrator.")

    else:
        api_key = ""

    st.markdown("---")

    # ── Session History Panel ───────────────────────────────
    if api_key:
        store = get_session_store()

        st.subheader("📜 Session History")

        # ── Current session indicator ──
        if "session_id" not in st.session_state:
            st.session_state.session_id = store.create_session()

        current_sid = st.session_state.session_id
        short_id = current_sid.split("_", 2)[-1] if "_" in current_sid else current_sid
        st.caption(f"🟢 Active: `{short_id}`")

        # ── New session button ──
        col_new1, col_new2 = st.columns([3, 1])
        with col_new1:
            if st.button("🆕 New Session", use_container_width=True):
                new_sid = store.create_session()
                st.session_state.session_id = new_sid
                st.session_state.messages = []
                st.session_state.code_content = ""
                st.session_state.uploaded_filename = ""
                st.session_state.doc_content = None
                st.session_state.mermaid_code = None
                st.session_state.mermaid_analysis = None
                st.rerun()
        with col_new2:
            if st.button("🗑️", help="Delete current session"):
                store.delete_session(current_sid)
                st.session_state.session_id = store.create_session()
                st.session_state.messages = []
                st.session_state.code_content = ""
                st.session_state.uploaded_filename = ""
                st.session_state.doc_content = None
                st.session_state.mermaid_code = None
                st.session_state.mermaid_analysis = None
                st.rerun()

        st.markdown("---")

        # ── Past sessions ──
        sessions = store.list_sessions()
        past_sessions = [s for s in sessions if s["session_id"] != current_sid]

        if past_sessions:
            st.markdown("**Past Sessions**")
            for s in past_sessions[:8]:
                ts = s["last_active"][:19].replace("T", " ")
                msg_count = s["message_count"]
                fname = s.get("filename")
                if fname:
                    label = f"📄 {fname} | 📅 {ts} ({msg_count} msgs)"
                else:
                    label = f"📅 {ts} ({msg_count} msgs)"

                with st.expander(label):
                    col_resume, col_delete = st.columns([2, 1])
                    with col_resume:
                        if st.button("▶️ Resume", key=f"resume_{s['session_id']}", use_container_width=True):
                            st.session_state.session_id = s["session_id"]
                            history = store.get_session(s["session_id"])
                            st.session_state.messages = [
                                {"role": m["role"], "content": m["content"]}
                                for m in history if m["role"] not in ["system_code", "system_filename"]
                            ]
                            loaded_code = store.get_code_content(s["session_id"])
                            st.session_state.code_content = loaded_code
                            loaded_fname = store.get_metadata(s["session_id"], "system_filename")
                            st.session_state.uploaded_filename = loaded_fname or "source_code.txt"
                            st.session_state.doc_content = None
                            st.session_state.mermaid_code = None
                            st.session_state.mermaid_analysis = None
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"del_{s['session_id']}"):
                            store.delete_session(s["session_id"])
                            st.rerun()
        else:
            st.caption("No past sessions yet.")

        st.markdown("---")

        # ── Semantic search ──
        st.subheader("🔍 Search History")
        search_query = st.text_input(
            "Search past conversations...",
            key="history_search",
            label_visibility="collapsed",
        )
        if search_query:
            results = store.search_sessions(search_query, n_results=3)
            if results:
                for r in results:
                    if r["role"] in ["system_code", "system_filename"]:
                        continue
                    icon = "🧑" if r["role"] == "user" else "🤖"
                    st.markdown(
                        f"{icon} **{r['role'].title()}** "
                        f"(relevance: {r['relevance']})"
                    )
                    st.markdown(r["content"][:200])
                    st.divider()
            else:
                st.info("No matching conversations found.")

        st.markdown("---")

        stats = store.get_stats()
        st.caption(
            f"📊 {stats['total_messages']} messages "
            f"in {stats['total_sessions']} sessions"
        )

if not api_key:
    if use_own_key and use_env_key:
        pass  # Warning already shown in sidebar
    elif use_env_key:
        pass  # Error already shown in sidebar
    else:
        st.info("👈 Select an API key option in the sidebar to get started.")
    st.stop()

# ==========================
# INITIALIZE SESSION STATES
# ==========================
if "session_id" not in st.session_state:
    store = get_session_store()
    st.session_state.session_id = store.create_session()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "code_content" not in st.session_state:
    st.session_state.code_content = ""

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = ""

if "doc_content" not in st.session_state:
    st.session_state.doc_content = None
if "mermaid_code" not in st.session_state:
    st.session_state.mermaid_code = None
if "mermaid_analysis" not in st.session_state:
    st.session_state.mermaid_analysis = None
if "current_diagram_type" not in st.session_state:
    st.session_state.current_diagram_type = "Class Diagram"

# ==========================
# FILE UPLOAD (MULTI-LANGUAGE + ZIP SUPPORT)
# ==========================
st.header("📄 Upload Source Code")

SUPPORTED_EXTENSIONS = {
    "py", "js", "ts", "jsx", "tsx", "java", "c", "cpp", "h", "hpp",
    "cs", "go", "rs", "rb", "php", "swift", "kt", "html", "css",
    "sql", "sh", "yaml", "yml", "json", "xml", "md", "r", "scala",
    "lua", "dart", "vue", "svelte", "toml", "ini", "cfg", "env",
    "txt", "bat", "ps1", "makefile", "dockerfile", "gitignore", "zip",
}

uploaded_file = st.file_uploader("Choose a source code file")

if uploaded_file:
    ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else ""
            
    # ── HANDLE SINGLE FILES ──
    if ext not in SUPPORTED_EXTENSIONS:
        st.warning(f"⚠️ `.{ext}` is not a common source code file. Attempting to read anyway...")

    try:
        code_content = uploaded_file.read().decode("utf-8")
        st.session_state.code_content = code_content
        st.session_state.uploaded_filename = uploaded_file.name
        if "session_id" in st.session_state:
            store = get_session_store()
            store.save_code_content(st.session_state.session_id, code_content)
            store.save_metadata(st.session_state.session_id, "system_filename", uploaded_file.name)
    except UnicodeDecodeError:
        st.error("❌ Cannot read this file. It appears to be a binary file. Please upload a text-based source code file.")
        code_content = ""

elif st.session_state.code_content:
    code_content = st.session_state.code_content
else:
    code_content = ""

if code_content:
    lang = get_language_from_filename(st.session_state.get("uploaded_filename", ""))
    display_lang = "text" if lang == "zip" else lang
    with st.expander(f"📂 View Uploaded Code ({len(code_content)} characters)"):
        st.code(code_content, language=display_lang, height=400)

# ==========================
# TABS
# ==========================
st.markdown("""
<style>
    /* Center the tabs container */
    div[data-baseweb="tab-list"] {
        justify-content: center;
    }
    /* Increase the font size of the tab buttons */
    button[data-baseweb="tab"] {
        font-size: 1.3rem; /* Makes the text bigger */
        font-weight: 600;  /* Makes it slightly bolder */
    }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📝 Documentation", "📊 Diagrams"])

# ==========================
# TAB 1 — CHAT
# ==========================
with tab1:
    st.header("Chat with Code")

    # Render chat history (User is right-aligned, Assistant is left-aligned natively)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── AUTO-SCROLL TO BOTTOM (The "WhatsApp" feel) ──
    # This script runs every time the chat updates, scrolling the user's view to the latest message.
    components.html(
        """
        <script>
            function scrollToBottom() {
                var main = window.parent.document.querySelector('section.main');
                if (main) {
                    main.scrollTo({ top: main.scrollHeight, behavior: 'smooth' });
                }
            }
            setTimeout(scrollToBottom, 100); // Small delay ensures DOM is fully loaded
        </script>
        """,
        height=0  # Set to 0 so it takes up no visual space on the screen
    )

    # Chat input (pinned to bottom natively by Streamlit)
    if prompt := st.chat_input("Ask something about the code..."):
        if not code_content:
            st.warning("Upload a file first.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.spinner("Thinking..."):
                answer = services.questions.get_answer(
                    code_content=code_content,
                    question=prompt,
                    api_key=api_key,
                    session_id=st.session_state.session_id,
                )

            with st.chat_message("assistant"):
                st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # Rerun to trigger the scroll script above with the new message
            st.rerun()

# ==========================
# TAB 2 — DOCUMENTATION
# ==========================
with tab2:
    st.header("Documentation Generator")

    if st.button("🚀 Generate Documentation", type="primary"):
        if not code_content:
            st.error("Please upload a source code file.")
        else:
            with st.spinner("Generating documentation..."):
                markdown_output = services.doc_generator.generate_documentation(
                    code_content, api_key
                )
                st.session_state.doc_content = markdown_output

    if st.session_state.doc_content:
        st.markdown("### 📘 Preview")
        st.markdown(st.session_state.doc_content)

        st.download_button(
            "📥 Download Markdown",
            st.session_state.doc_content,
            "Documentation.md",
            "text/markdown",
        )

# ==========================
# TAB 3 — DIAGRAMS
# ==========================
with tab3:
    st.header("Generate Diagrams")

    DIAGRAM_OPTIONS = [
        "Class Diagram",
        "ERD Diagram",
        "Use Case Diagram",
        "Sequence Diagram",
        "Activity Diagram",
    ]

    if not code_content:
        st.info("Upload a source code file to generate diagrams.")
    else:
        col_sel, col_btn = st.columns([2, 1])

        with col_sel:
            diagram_selection = st.selectbox(
                "Choose Diagram Type",
                DIAGRAM_OPTIONS,
                index=DIAGRAM_OPTIONS.index(st.session_state.current_diagram_type) if st.session_state.current_diagram_type in DIAGRAM_OPTIONS else 0,
            )

        with col_btn:
            st.write("")
            st.write("")
            generate = st.button("🎨 Generate", type="primary", use_container_width=True)

        if generate:
            st.session_state.current_diagram_type = diagram_selection
            with st.spinner("Generating diagram..."):
                analysis, clean_mermaid = services.diagram_generator.generate_diagram(
                    code_content, diagram_selection, api_key
                )
                st.session_state.mermaid_analysis = analysis
                st.session_state.mermaid_code = clean_mermaid

        # FIX: This entire block is now safely indented INSIDE `with tab3:`
        if st.session_state.mermaid_code:
            with st.container():
                col_code, col_preview = st.columns([1, 1], gap="small")

                with col_code:
                    st.write("💻 **Mermaid Source (Editable)**")
                    st.caption("⚠️ If the diagram fails to render, fix syntax errors here and press `Ctrl+Enter` to update the preview.")
                    
                    edited_code = st.text_area(
                        "Mermaid Code Editor",
                        value=st.session_state.mermaid_code,
                        height=750,
                        label_visibility="collapsed"
                    )
                    
                    if edited_code != st.session_state.mermaid_code:
                        st.session_state.mermaid_code = edited_code
                        st.rerun()

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
html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; background: #f5f5f5; font-family: sans-serif; }}
.container {{ height: 100%; width: 100%; display: flex; flex-direction: column; background: white; border: 1px solid #ddd; border-radius: 8px; }}
.toolbar {{ height: 40px; padding: 6px; display: flex; align-items: center; gap: 6px; background: #fafafa; border-bottom: 1px solid #ddd; }}
.toolbar button {{ background: white; border: 1px solid #ccc; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 14px; }}
.toolbar button:hover {{ background: #e6e6e6; }}
.mermaid {{ flex: 1; width: 100%; overflow: hidden; display: flex; justify-content: center; align-items: center; padding: 10px; }}
.mermaid svg {{ width: 100% !important; height: 100% !important; }}
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
    svg.addEventListener("wheel", function(e) {{ if (e.ctrlKey) {{ e.preventDefault(); }} }}, {{ passive: false }});
    panZoom = svgPanZoom(svg, {{ zoomEnabled: true, fit: true, center: true, minZoom: 0.1, maxZoom: 10 }});
}}
function zoomIn() {{ panZoom?.zoomIn(); }}
function zoomOut() {{ panZoom?.zoomOut(); }}
function resetZoom() {{ panZoom?.resetZoom(); panZoom?.center(); }}
function exportSVG() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (!svg) return;
    const clone = svg.cloneNode(true);
    if (!clone.getAttribute('xmlns')) {{ clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); }}
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(clone);
    const blob = new Blob([source], {{type: 'image/svg+xml;charset=utf-8'}});
    download(URL.createObjectURL(blob), 'diagram.svg');
}}

function exportPNG() {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (!svg) return alert("Error: SVG structure not found yet.");
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
        const scale = 2; // High DPI Scale fallback
        let width = bbox.width + padding * 2;
        let height = bbox.height + padding * 2;
        
        if (svg.viewBox && svg.viewBox.baseVal) {{ 
            width = svg.viewBox.baseVal.width || width; 
            height = svg.viewBox.baseVal.height || height; 
        }}
        
        canvas.width = width * scale;
        canvas.height = height * scale;
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.scale(scale, scale);
        ctx.drawImage(img, padding, padding, width - padding*2, height - padding*2);
        download(canvas.toDataURL('image/png'), 'diagram.png');
        URL.revokeObjectURL(url);
    }};
    img.onerror = function() {{ alert("Failed to convert image layout."); URL.revokeObjectURL(url); }}
    img.src = url;
}}

function download(url, filename) {{
    const a = document.createElement('a');
    a.href = url; 
    a.download = filename;
    a.target = '_blank'; // Prevents some sandbox environment blocks
    document.body.appendChild(a); 
    a.click(); 
    document.body.removeChild(a);
}}

// Initialize observer
const observer = new MutationObserver(() => {{
    const svg = document.querySelector('#diagram-{unique_id} svg');
    if (svg && !panZoom) {{
        setTimeout(initPanZoom, 100);
        observer.disconnect();
    }}
}});
observer.observe(document.getElementById('diagram-{unique_id}'), {{ childList: true, subtree: true }});

</script>
</body>
</html>
"""
                    components.html(html, height=790, scrolling=False)

                    st.write("---")
                    st.caption("📥 Browser blocking the buttons inside the preview pane? Download raw script below:")
                    st.download_button(
                        label="💾 Download Raw Mermaid Text Script (.mmd)",
                        data=st.session_state.mermaid_code,
                        file_name="diagram.mmd",
                        mime="text/plain",
                        use_container_width=True
                    )
