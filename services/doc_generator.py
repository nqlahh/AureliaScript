from openai import OpenAI
from config import OPENAI_MODEL, DOC_STRUCTURE_RULES

def generate_documentation(code_content: str, api_key: str):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": DOC_STRUCTURE_RULES},
            {
                "role": "user",
                "content": f"Document this Python code:\n{code_content}"
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content
