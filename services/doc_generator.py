from openai import OpenAI
from config import OPENAI_MODEL, DOC_STRUCTURE_RULES
from services.vector_store import VectorStore

def generate_documentation(code_content: str, api_key: str):
    client = OpenAI(api_key=api_key)

    vs = VectorStore(api_key)
    vs.build(code_content)

    context = vs.retrieve("overall structure, functions, classes")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": DOC_STRUCTURE_RULES},
            {
                "role": "user",
                "content": f"""
DOCUMENT THIS CODE BASED ON THE CONTEXT BELOW:

{context}
"""
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content
