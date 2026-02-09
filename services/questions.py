from openai import OpenAI
from config import OPENAI_MODEL
from services.vector_store import VectorStore

def get_answer(code_content: str, question: str, api_key: str):
    client = OpenAI(api_key=api_key)

    # Build vector store
    vs = VectorStore(api_key)
    vs.build(code_content)

    # Retrieve relevant context
    context = vs.retrieve(question)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a code analysis assistant."},
            {
                "role": "user",
                "content": f"""
CONTEXT:
{context}

QUESTION:
{question}
"""
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content
