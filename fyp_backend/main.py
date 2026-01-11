from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import zipfile
import uvicorn

# Import the RAG system we just created
from app.utils.rag_utils import rag_instance

app = FastAPI(title="AI Code Assistant Backend")

# --- CORS Settings ---
# This allows the React frontend (on port 5173) to talk to this backend (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React runs on this port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class QuestionRequest(BaseModel):
    question: str

class DocsRequest(BaseModel):
    file_name: str  # Optional: specific file to document, or leave empty for all

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "Server is running! Use /upload and /ask endpoints."}

@app.post("/upload")
async def upload_codebase(file: UploadFile = File(...)):
    """
    Uploads a .zip file of Python code, extracts it, and indexes it.
    """
    # 1. Save zip file
    upload_dir = "data"
    os.makedirs(upload_dir, exist_ok=True)
    
    zip_path = os.path.join(upload_dir, file.filename)
    
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Extract zip
    extract_path = os.path.join(upload_dir, "extracted")
    
    # FIX: Use ignore_errors=True to handle OneDrive/VirusScanner locks
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path, ignore_errors=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        
    # 3. Process with RAG
    try:
        rag_instance.load_codebase(extract_path)
        rag_instance.create_vector_index()
        
        # Clean up zip file (keep extracted folder for debug if needed)
        os.remove(zip_path)
        
        return {"message": "Codebase indexed successfully!", "files_indexed": len(rag_instance.documents)}
    except Exception as e:
        # Log the error to console for debugging
        print(f"Error during processing: {e}")
        return {"error": str(e)}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Ask a natural language question about the uploaded code.
    """
    if rag_instance.index is None:
        raise HTTPException(status_code=400, detail="No codebase uploaded yet.")
        
    result = rag_instance.ask_question(request.question)
    return result

@app.post("/generate-docs")
def generate_docs(request: DocsRequest):
    """
    Generates formatted documentation (Markdown) for the uploaded codebase.
    """
    if rag_instance.index is None:
        raise HTTPException(status_code=400, detail="No codebase uploaded yet.")

    # 1. Retrieve relevant code (Search for "architecture" or "main" or "functions")
    # If file_name is provided, we try to find it
    query = request.file_name if request.file_name else "software architecture and main classes"
    
    # We will create a custom prompt for documentation
    context, sources = rag_instance.search_code(query, top_k=5)
    
    if not context:
         return {"markdown_docs": "# Error\n\nNo code found to document."}

    # 2. Create a specialized Prompt for Documentation
    prompt = f"""
    You are a Technical Writer. Generate comprehensive Software Documentation based on the provided code.
    
    REQUIREMENTS:
    1. Use Markdown format.
    2. Include sections: Overview, Classes, Functions, and Usage.
    3. Do NOT include the raw source code, just descriptions.
    
    SOURCE CODE:
    {context}
    
    Generate the documentation now.
    """

    # 3. Ask AI (Synchronous for now, same as /ask)
    response = rag_instance.model.generate_content(prompt)
    
    return {
        "markdown_docs": response.text,
        "sources": sources
    }


# --- Main Entry Point ---
if __name__ == "__main__":
    # IMPORTANT: We run directly without '--reload' to prevent memory loss
    uvicorn.run(app, host="127.0.0.1", port=8000)