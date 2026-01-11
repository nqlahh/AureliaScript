import warnings
# This hides the "FutureWarning" message at the top
warnings.filterwarnings("ignore", category=FutureWarning)

import os
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
from chromadb.config import Settings

# 1. SETUP
# -------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Use the 2.5 model found in your debug list
model = genai.GenerativeModel('gemini-2.5-flash')

documents = [
    "Python is a high-level, interpreted programming language known for its readability.",
    "The capital of France is Paris, which is known for the Eiffel Tower.",
    "Photosynthesis is the process used by plants to convert light into energy.",
    "The Gemini API is a generative AI model provided by Google DeepMind.",
    "ChromaDB is an open-source vector database used for AI embeddings."
]

# 2. SETUP VECTOR DB
# -----------------------------------
try:
    chroma_client = chromadb.Client(Settings())
    collection = chroma_client.get_collection(name="my_knowledge_base")
except:
    chroma_client = chromadb.Client(Settings())
    collection = chroma_client.create_collection(name="my_knowledge_base")

if collection.count() == 0:
    collection.add(
        documents=documents,
        ids=[f"id_{i}" for i in range(len(documents))]
    )

# 3. RAG FUNCTION
# ----------------------------
def ask_question(question):
    # Step A: Retrieve
    results = collection.query(
        query_texts=[question],
        n_results=2
    )
    retrieved_contexts = results['documents'][0]
    context_text = "\n".join(retrieved_contexts)
    
    # Step B: Augment
    prompt = f"""
    Context: {context_text}
    Question: {question}
    Answer:
    """

    # Step C: Generate
    response = model.generate_content(prompt)
    
    # Step D: Clean Output (Print just the text)
    print(response.text)

# 4. RUN TESTS
# -------------------
if __name__ == "__main__":
    print("--- Test 1 ---")
    ask_question("What is the capital of France?")
    
    print("\n--- Test 2 ---")
    ask_question("What is Photosynthesis?")