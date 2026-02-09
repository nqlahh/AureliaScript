from abc import ABC, abstractmethod
import re
from openai import OpenAI
from config import OPENAI_MODEL, DIAGRAM_RULES
from services.vector_store import VectorStore

# ===============================
# STRATEGY BASE
# ===============================

class DiagramStrategy(ABC):
    @abstractmethod
    def diagram_header(self) -> str:
        pass

    @abstractmethod
    def get_prompt(self, code_context: str) -> str:
        pass


# ===============================
# CLASS DIAGRAM
# ===============================

class ClassDiagramStrategy(DiagramStrategy):
    def diagram_header(self):
        return "classDiagram"

    def get_prompt(self, code_content):
        return f"{DIAGRAM_RULES['CLASS_DIAGRAM']}\n\nINPUT CODE:\n{code_content}"


# ===============================
# ER DIAGRAM
# ===============================

class ERDDiagramStrategy(DiagramStrategy):
    def diagram_header(self):
        return "erDiagram"

    def get_prompt(self, code_context):
        return f"{DIAGRAM_RULES['ERD_DIAGRAM']}\n\nCODE CONTEXT:\n{code_context}"


# ===============================
# USE CASE DIAGRAM
# ===============================

class UseCaseDiagramStrategy(DiagramStrategy):
    def diagram_header(self):
        return "flowchart LR"

    def get_prompt(self, code_context):
        return f"{DIAGRAM_RULES['USE_CASE_DIAGRAM']}\n\nCODE CONTEXT:\n{code_context}"


# ===============================
# FACTORY
# ===============================

class DiagramFactory:
    @staticmethod
    def create(selection: str) -> DiagramStrategy:
        if "Class" in selection:
            return ClassDiagramStrategy()
        if "ERD" in selection:
            return ERDDiagramStrategy()
        if "Use Case" in selection:
            return UseCaseDiagramStrategy()
        return ClassDiagramStrategy()


# ===============================
# SAFE CLEANERS (NON-DESTRUCTIVE)
# ===============================

def extract_mermaid(text: str) -> str:
    """
    Extract Mermaid code if wrapped in ``` blocks,
    otherwise return raw text.
    """
    blocks = re.findall(r"```(?:mermaid)?\s*(.*?)```", text, re.DOTALL)
    return blocks[0].strip() if blocks else text.strip()


def clean_mermaid_output(text: str) -> str:
    """
    Removes markdown fences and explanations
    WITHOUT breaking Mermaid grammar.
    """
    text = re.sub(r"```(?:mermaid)?", "", text)
    text = re.sub(r"```", "", text)

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith(("note:", "explanation:", "here is")):
            continue
        lines.append(line.rstrip())

    return "\n".join(lines).strip()


def ensure_header(code: str, header: str) -> str:
    """
    Ensures Mermaid header appears exactly once at the top.
    """
    lines = code.splitlines()
    cleaned = [line for line in lines if line.strip() != header]
    return header + "\n" + "\n".join(cleaned)


# ===============================
# MAIN GENERATOR (RAG ENABLED)
# ===============================

def generate_diagram(code_content: str, selection: str, api_key: str):
    client = OpenAI(api_key=api_key)
    strategy = DiagramFactory.create(selection)

    # ---- RAG VECTOR STORE ----
    vs = VectorStore(api_key)
    vs.build(code_content)
    context = vs.retrieve(f"{selection} diagram entities, relationships, structure")

    # ---- GPT CALL ----
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": DIAGRAM_RULES["SYSTEM_PROMPT"]
            },
            {
                "role": "user",
                "content": strategy.get_prompt(context)
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content
    mermaid = extract_mermaid(raw)
    mermaid = clean_mermaid_output(mermaid)
    mermaid = ensure_header(mermaid, strategy.diagram_header())

    return raw, mermaid
