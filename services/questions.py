from openai import OpenAI
from config import OPENAI_MODEL
from services.vector_store import VectorStore
from services.session_store import SessionStore
from services.mcp_bridges import chat_with_session_context


def get_answer(code_content: str, question: str, api_key: str, session_id: str = None):
    """
    Get answer with session logging + MCP context.
    Falls back to original simple mode if no session_id.
    """
    if session_id:
        return chat_with_session_context(
            code_content=code_content,
            question=question,
            session_id=session_id,
            api_key=api_key,
            model=OPENAI_MODEL,
        )
    else:
        # Original mode (backward compatible)
        client = OpenAI(api_key=api_key)
        vs = VectorStore(api_key)
        vs.build(code_content)
        context = vs.retrieve(question)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a code analysis assistant."},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"},
            ],
            temperature=0,
        )
        return response.choices[0].message.content