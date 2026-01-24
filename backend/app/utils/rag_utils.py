import os
import glob
import ast
from dotenv import load_dotenv
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Tuple, Dict

# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Load Embedding Model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Helper Functions (For FYP Requirements) ---

def extract_imports(tree):
    """Helper to extract imports from AST tree"""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return list(set(imports))

def parse_python_file(filepath: str) -> Dict:
    """Parses a Python file using AST to extract structure."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        # Extract Classes
        classes = [node.name for node in ast.walk(tree) 
                   if isinstance(node, ast.ClassDef)]
        
        # Extract Functions
        functions = [node.name for node in ast.walk(tree) 
                     if isinstance(node, ast.FunctionDef)]
        
        # Extract Imports
        imports = extract_imports(tree)
        
        return {
            'file': filepath,
            'classes': classes,
            'functions': functions,
            'imports': imports
        }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

# --- RAG System Class ---

class RAGSystem:
    def __init__(self, model_name='gemini-2.5-flash'):
        self.model = genai.GenerativeModel(model_name)
        self.index = None
        self.documents = []
        self.metadata = [] 

    def load_codebase(self, folder_path: str):
        """
        Reads all .py files from a folder.
        Uses SIMPLE LOGIC for stability, but calls AST parser just to log stats.
        """
        print(f"Loading codebase from: {folder_path}")
        documents = []
        metadata = []
        
        files = glob.glob(os.path.join(folder_path, "**/*.py"), recursive=True)
        
        for file_path in files:
            try:
                # 1. Use AST Parsing (Optional, just for display/context header)
                parsed_data = parse_python_file(file_path)
                
                # 2. Read full file content (This is what is searched/used for diagrams)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 3. Combine Context (This makes search easier for AI)
                # We add the AST summary at the top
                context_text = f"File: {file_path}\n"
                if parsed_data:
                    context_text += f"Classes: {', '.join(parsed_data['classes'])}\n"
                    context_text += f"Functions: {', '.join(parsed_data['functions'])}\n"
                context_text += "--- CODE START ---\n"
                context_text += content
                context_text += "\n--- CODE END ---"
                
                documents.append(context_text)
                metadata.append(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        print(f"Loaded {len(documents)} files.")
        self.documents = documents
        self.metadata = metadata
        return documents

    def create_vector_index(self):
        """Converts code to vectors and saves to FAISS index."""
        print("Creating embeddings... this might take a minute.")
        embeddings = embedding_model.encode(self.documents)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        print(f"Index created with {self.index.ntotal} vectors.")

    def search_code(self, query: str, top_k=3) -> Tuple[str, List[str]]:
        """Searches vector index for relevant code snippets."""
        if self.index is None:
            return "", []
        query_vector = embedding_model.encode([query])
        distances, indices = self.index.search(query_vector.astype('float32'), top_k)
        retrieved_docs = []
        retrieved_sources = []
        for i in indices[0]:
            if i < len(self.documents):
                retrieved_docs.append(self.documents[i])
                retrieved_sources.append(self.metadata[i])
        context_text = "\n\n### NEW FILE ###\n\n".join(retrieved_docs)
        return context_text, retrieved_sources

    def ask_question(self, question: str):
        """RAG Pipeline: Retrieve -> Augment -> Generate"""
        context, sources = self.search_code(question)
        prompt = f"""
        You are a helpful Software Engineering Assistant.
        Analyze the following Python source code and answer the user's question.
        
        CONTEXT (Source Code):
        {context}
        
        QUESTION: {question}
        
        Provide a detailed answer based ONLY on the code provided.
        If the answer is not in the code, say "I cannot find that information."
        """
        response = self.model.generate_content(prompt)
        return {
            "answer": response.text,
            "sources": sources
        }

# Global instance
rag_instance = RAGSystem()