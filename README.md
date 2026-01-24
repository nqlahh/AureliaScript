
## 🚀 Getting Started

### Prerequisites
- Python 3.14+
- Node.js 18+

### 1. Backend Setup

1.  **Clone/Download** the project.
2.  Navigate to the backend directory:
    ```bash
    cd FYP_MAIN/FYP_BACKEND
    ```
3.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    # venv/bin/activate  # Mac/Linux
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Configure API Key:**
    *   Create a `.env` file in `FYP_BACKEND`.
    *   Add your Google API Key:
        ```text
        GEMINI_API_KEY=your_api_key_here
        ```
6.  **Run the Server:**
    ```bash
    uvicorn main:app --reload
    ```
    *   The API will run at `http://127.0.0.1:8000`

### 2. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd FYP_MAIN/FYP_FRONTEND
    ```
2.  **Install Dependencies:**
    ```bash
    npm install
    ```
3.  **Run the Application:**
    ```bash
    npm run dev
    ```
    *   The app will run at `http://localhost:5173`

## 💻 Usage Guide

1.  **Start Both Servers:** Ensure Backend (Port 8000) and Frontend (Port 5173) are running.
2.  **Upload Codebase:**
    *   Zip your Python project files (e.g., `my_project.zip`).
    *   Click "Upload & Index" in the sidebar.
    *   The system will parse the code, create vector embeddings, and index it.
3.  **Chat with Code:**
    *   Go to the "Chat" tab.
    *   Ask questions like: *"Explain the User class"* or *"What does the create_order function do?"*
4.  **Generate Documentation:**
    *   Click the "Generate Documentation" button to get a full Markdown report.
5.  **Visualize Architecture:**
    *   Go to the "Diagram" tab.
    *   Select **Class Diagram**, **Use Case**, or **ERD** from the dropdown.
    *   Click "Generate" to view the visual architecture.
    *   Click "Export SVG" to download the diagram.

