# diagram_generator.py
from abc import ABC, abstractmethod
import re
from openai import OpenAI
from config import OPENAI_MODEL, DIAGRAM_RULES
from services.vector_store import VectorStore


# ==========================================================
# STRATEGY INTERFACE
# ==========================================================

class DiagramStrategy(ABC):

    @abstractmethod
    def diagram_header(self):
        pass

    @abstractmethod
    def get_prompt(self, context):
        pass



# ==========================================================
# DIAGRAM STRATEGIES
# ==========================================================

class ClassDiagramStrategy(DiagramStrategy):

    def diagram_header(self):
        return "classDiagram"

    def get_prompt(self, context):
        return f"""
{DIAGRAM_RULES['CLASS_DIAGRAM']}

RETRIEVED CONTEXT:
{context}

Generate the diagram now.
"""


class ERDDiagramStrategy(DiagramStrategy):

    def diagram_header(self):
        return "erDiagram"

    def get_prompt(self, context):
        return f"""
{DIAGRAM_RULES['ERD_DIAGRAM']}

RETRIEVED CONTEXT:
{context}

Generate the diagram now.
"""


class UseCaseDiagramStrategy(DiagramStrategy):

    def diagram_header(self):
        return "flowchart LR"

    def get_prompt(self, context):
        return f"""
{DIAGRAM_RULES['USE_CASE_DIAGRAM']}

RETRIEVED CONTEXT:
{context}

Generate the diagram now.
"""


class SequenceDiagramStrategy(DiagramStrategy):

    def diagram_header(self):
        return "sequenceDiagram"

    def get_prompt(self, context):
        return f"""
{DIAGRAM_RULES['SEQUENCE_DIAGRAM']}

RETRIEVED CONTEXT:
{context}

Generate the diagram now.
"""


class ActivityDiagramStrategy(DiagramStrategy):

    def diagram_header(self):
        return "flowchart TD"

    def get_prompt(self, context):
        return f"""
{DIAGRAM_RULES['ACTIVITY_DIAGRAM']}

RETRIEVED CONTEXT:
{context}

Generate the diagram now.
"""



# ==========================================================
# FACTORY
# ==========================================================

class DiagramFactory:
    @staticmethod
    def create(selection: str) -> DiagramStrategy:

        selection = selection.lower()

        if "class" in selection:
            return ClassDiagramStrategy()

        if "erd" in selection:
            return ERDDiagramStrategy()

        if "use case" in selection:
            return UseCaseDiagramStrategy()

        if "sequence" in selection:
            return SequenceDiagramStrategy()

        if "activity" in selection:
            return ActivityDiagramStrategy()

        return ClassDiagramStrategy()


# ===============================
# SAFE CLEANERS (FORTIFIED)
# ===============================

def extract_mermaid(text: str) -> str:
    blocks = re.findall(r"```(?:mermaid)?\s*(.*?)```", text, re.DOTALL)
    return blocks[0].strip() if blocks else text.strip()

def clean_mermaid_output(text: str) -> str:
    # 1. Remove markdown code fences
    text = re.sub(r"```(?:mermaid)?", "", text)
    text = re.sub(r"```", "", text)

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        
        # 2. Skip conversational filler
        if not stripped:
            continue
        if stripped.lower().startswith(("note:", "explanation:", "here is", "sure,", "below")):
            continue

        # 3. Fix common LLM hallucinations in Mermaid syntax
        # Replace smart quotes with standard double quotes
        line = line.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
        
        # Remove markdown bold/italic inside node labels (e.g., **text** -> text)
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        line = re.sub(r'__(.*?)__', r'\1', line)
        
        # Remove trailing commas inside node definitions (e.g., class User { +name, +age } -> +name +age)
        # This is tricky, so we just remove commas before closing brackets/braces
        line = re.sub(r',\s*([}\]\)])', r'\1', line)
        
        # Fix parentheses in node IDs (LLMs sometimes do "User(Login)" instead of "User([Login])")
        # We only apply this if it's clearly a node definition, to avoid breaking method calls in class diagrams
        
        lines.append(line.rstrip())

    return "\n".join(lines).strip()


def ensure_header(code: str, header: str) -> str:
    # Remove any existing instance of the header to avoid duplication
    lines = code.splitlines()
    cleaned = [line for line in lines if line.strip() != header]
    
    # Ensure the header is the very first line
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
        temperature=0  # Keep temperature at 0 for maximum determinism
    )

    raw = response.choices[0].message.content
    mermaid = extract_mermaid(raw)
    mermaid = clean_mermaid_output(mermaid)
    mermaid = ensure_header(mermaid, strategy.diagram_header())

    return raw, mermaid