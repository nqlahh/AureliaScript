import os
import glob
from dotenv import load_dotenv  # <--- ADD THIS
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np
from typing import List, Tuple

# Load API Key from .env file
load_dotenv() # <--- ADD THIS
api_key = os.getenv("GEMINI_API_KEY") # <--- ADD THIS
genai.configure(api_key=api_key) # <--- ADD THIS

# Load Embedding Model (This converts text to numbers/vectors)
# We use 'all-MiniLM-L6-v2' which is fast and accurate for code
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class RAGSystem:
    def __init__(self, model_name='gemini-2.5-flash'):
        # Initialize AI Model
        self.model = genai.GenerativeModel(model_name)
        self.index = None
        self.documents = []
        self.metadata = [] # Stores file paths

    def load_codebase(self, folder_path: str):
        """
        Reads all .py files from a folder.
        """
        print(f"Loading codebase from: {folder_path}")
        documents = []
        metadata = []
        
        # Find all .py files recursively
        files = glob.glob(os.path.join(folder_path, "**/*.py"), recursive=True)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        documents.append(content)
                        metadata.append(file_path)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        print(f"Loaded {len(documents)} files.")
        self.documents = documents
        self.metadata = metadata
        return documents

    def create_vector_index(self):
        """
        Converts code to vectors and saves to FAISS index.
        """
        print("Creating embeddings... this might take a minute.")
        
        # 1. Convert text to vectors (embeddings)
        embeddings = embedding_model.encode(self.documents)
        
        # 2. Create FAISS Index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension) # L2 is a distance metric
        
        # 3. Add vectors to index
        self.index.add(embeddings.astype('float32'))
        
        print(f"Index created with {self.index.ntotal} vectors.")

    def search_code(self, query: str, top_k=3) -> Tuple[str, List[str]]:
        """
        1. Convert question to vector
        2. Search FAISS for top matches
        3. Return the relevant code snippets
        """
        if self.index is None:
            return "Please load a codebase first.", []

        # 1. Convert query to vector
        query_vector = embedding_model.encode([query])
        
        # 2. Search FAISS
        distances, indices = self.index.search(query_vector.astype('float32'), top_k)
        
        # 3. Retrieve documents
        retrieved_docs = []
        retrieved_sources = []
        
        for i in indices[0]:
            if i < len(self.documents):
                retrieved_docs.append(self.documents[i])
                retrieved_sources.append(self.metadata[i])
        
        context_text = "\n\n### NEW FILE ###\n\n".join(retrieved_docs)
        return context_text, retrieved_sources

    def ask_question(self, question: str):
        """
        RAG Pipeline: Retrieve -> Augment -> Generate
        """
        # 1. Retrieve
        context, sources = self.search_code(question)
        
        # 2. Augment (Build Prompt)
        prompt = f"""
        You are a helpful Software Engineering Assistant.
        Analyze the following Python source code and answer the user's question.
        
        CONTEXT (Source Code):
        {context}
        
        QUESTION: {question}
        
        Provide a detailed answer based ONLY on the code provided.
        If the answer is not in the code, say "I cannot find that information."
        """
        
        # 3. Generate
        response = self.model.generate_content(prompt)
        return {
            "answer": response.text,
            "sources": sources
        }

# Global instance to be used by the app
rag_instance = RAGSystem()