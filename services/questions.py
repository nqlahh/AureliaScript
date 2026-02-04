from openai import OpenAI
from config import OPENAI_MODEL

def get_answer(code_content: str, question: str, api_key: str):
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a code analysis assistant."},
            {
                "role": "user",
                "content": f"CODE:\n{code_content}\n\nQUESTION:\n{question}"
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content
