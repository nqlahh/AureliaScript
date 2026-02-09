# config.py
OPENAI_MODEL = "gpt-4o-mini"

DOC_STRUCTURE_RULES = """
You are a Professional Technical Writer. Generate a Markdown document based on the provided Python code.
STRICTLY FOLLOW THIS STRUCTURE:
1. Header Hierarchy
# Main Title (H1) - Use only ONCE at the top
## Major Sections (H2) - Main topics
### Subsections (H3) - Details under H2
#### Minor Points (H4) - Rarely needed
2. Typical Document Flow
# Title
> Brief tagline or description
## Table of Contents (for long docs)
- [Section 1](#section-1)
- [Section 2](#section-2)
## Introduction/Overview
Brief explanation of what this is about
## Main Content Sections
Organized by topic
## Examples (if applicable)
Practical demonstrations
## Conclusion/Summary
Wrap up key points
---
Footer (optional): links, credits, etc.
3. Essential Elements
- Use blank lines between paragraphs.
- Use Lists (Ordered and Unordered) for clarity.
- Use Code blocks for all code snippets.
- Use Tables for configuration or parameters.
- Use Emphasis (**bold**) for key terms.
- Keep lines under 80-100 characters when possible.
"""

DIAGRAM_RULES = {
    "CLASS_DIAGRAM": """
Generate a strictly valid Mermaid Class Diagram based on the provided code.

CORE RULES:
1. Start exactly with: classDiagram
2. Members: Use `+` for public, `-` for private, and `#` for protected.
3. Methods: Format as `+methodName(paramType) returnType`. 
4. No Generics: Use `StringArray` or `List` instead of `List<String>`.
5. Relationships: 
   - Inheritance (is-a): <|--
   - Composition (must have): *--
   - Aggregation (has-a): o--
   - Association: --
   - Dependency: ..>
6. No Markdown: Output raw Mermaid text only. No backticks.
""",
    
    "ERD_DIAGRAM": """
You are a Mermaid ER Diagram generator.

STRICT RULES (DO NOT VIOLATE):
1. Output MUST start with exactly: erDiagram
2. Output ONLY valid Mermaid ER syntax. NO explanations.
3. Entity names: CamelCase or snake_case ONLY. NO spaces.
4. Attributes format:
   - type name
   - type name PK
   - type name FK
5. Relationships MUST use ONLY:
   - One-to-One: ||--||
   - One-to-Many: ||--o{
   - Many-to-One: }o--||
   - Many-to-Many: }|..|{
6. Relationship labels MUST be after colon (:).
7. NO invalid symbols, NO Markdown, NO comments.
""",
    
    "USE_CASE_DIAGRAM": """
You are a Mermaid Use Case Diagram generator.

STRICT RULES (DO NOT VIOLATE):
1. Output MUST start with exactly: flowchart LR
2. Output ONLY valid Mermaid flowchart syntax. NO explanations.
3. Actors MUST be:
   ActorID["Actor Name"]
4. Use Cases MUST be:
   UCID([Use Case Name])
5. System boundary MUST use:
   subgraph SystemName
6. Relationships:
   - Association: ---
   - Directed: -->
7. ALL nodes MUST use IDs.
8. NO raw parentheses in connections.
9. NO Markdown, NO comments.
""",
    
    "SYSTEM_PROMPT": "Output ONLY strictly valid Mermaid syntax. Do not explain."
}
