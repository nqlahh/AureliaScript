from abc import ABC, abstractmethod
import re
from openai import OpenAI
from config import OPENAI_MODEL

client = OpenAI()

# ===============================
# STRATEGY
# ===============================

class DiagramStrategy(ABC):
    @abstractmethod
    def diagram_header(self) -> str:
        pass

    @abstractmethod
    def get_prompt(self, code_content: str) -> str:
        pass


class ClassDiagramStrategy(DiagramStrategy):
    def diagram_header(self):
        return "classDiagram"

    def get_prompt(self, code_content):
        return f"""
Generate a VALID Mermaid Class Diagram ONLY.

RULES:
- Output Mermaid code only
- Start with: classDiagram
- No explanations
- No markdown
- No generics
- Simple methods: + method()

CODE:
{code_content}
"""


class ERDDiagramStrategy(DiagramStrategy):
    def diagram_header(self):
        return "erDiagram"

    def get_prompt(self, code_content):
        return f"""
Generate a VALID Mermaid ER Diagram ONLY.

RULES:
- Output Mermaid code only
- Start with: erDiagram
- Correct cardinalities

CODE:
{code_content}
"""


class UseCaseDiagramStrategy(DiagramStrategy):
    def diagram_header(self):
        return "flowchart TD"

    def get_prompt(self, code_content):
        return f"""
Generate a Mermaid Use Case Diagram using flowchart TD ONLY.

RULES:
- Output Mermaid only
- Actors external
- Use --> arrows

CODE:
{code_content}
"""


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
# HELPERS
# ===============================

def extract_mermaid(text: str) -> str:
    blocks = re.findall(r"```(?:mermaid)?\s*(.*?)```", text, re.DOTALL)
    return blocks[0].strip() if blocks else text.strip()


def ensure_header(code: str, header: str) -> str:
    return code if code.startswith(header) else f"{header}\n{code}"


def repair_mermaid(code: str) -> str:
    code = re.sub(r"<.*?>", "", code)
    code = re.sub(r":\s*\w+", "", code)
    code = code.replace("[", "").replace("]", "")
    return code.strip()

# ===============================
# MAIN
# ===============================

def generate_diagram(code_content: str, selection: str, api_key: str):
    client = OpenAI(api_key=api_key)
    strategy = DiagramFactory.create(selection)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a UML generation engine."},
            {"role": "user", "content": strategy.get_prompt(code_content)}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content
    mermaid = extract_mermaid(raw)
    mermaid = ensure_header(mermaid, strategy.diagram_header())
    mermaid = repair_mermaid(mermaid)

    return raw, mermaid
