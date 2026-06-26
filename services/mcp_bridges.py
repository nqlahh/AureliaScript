"""
MCP Bridge for AureliaScript

Maps MCP session-log tools to OpenAI function-calling format.
When the AI decides to search past conversations, it calls these
tools — the same tools exposed by the MCP server.
"""

import json
from typing import Dict, Any
from openai import OpenAI
from services.session_store import SessionStore


# ── MCP Tool Schemas (OpenAI function-calling format) ──────────

MCP_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_past_conversations",
            "description": (
                "Search past chat conversations semantically. "
                "Use when the user refers to previous discussions or "
                "needs context from past conversations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_session_history",
            "description": "Retrieve full history for a specific session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "The session ID to retrieve",
                    }
                },
                "required": ["session_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_sessions",
            "description": "List all past conversation sessions.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# ── Tool Execution (same backend as MCP server) ────────────────

def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute an MCP tool. Uses SessionStore directly (same backend
    the MCP server wraps), ensuring consistency.
    """
    store = SessionStore()

    if tool_name == "search_past_conversations":
        results = store.search_sessions(
            arguments.get("query", ""),
            arguments.get("n_results", 5),
        )
        if not results:
            return "No past conversations found."
        return json.dumps(results, indent=2)

    elif tool_name == "get_session_history":
        messages = store.get_session(arguments.get("session_id", ""))
        if not messages:
            return "No messages found for that session."
        return json.dumps(messages, indent=2)

    elif tool_name == "list_all_sessions":
        sessions = store.list_sessions()
        if not sessions:
            return "No past sessions found."
        return json.dumps(sessions, indent=2)

    return f"Unknown tool: {tool_name}"


# ── Main Chat Function (with MCP context) ──────────────────────

def chat_with_session_context(
    code_content: str,
    question: str,
    session_id: str,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Enhanced chat with session logging + MCP tool access.

    Flow:
    1. Build code context via RAG
    2. Load recent session context
    3. Call OpenAI with MCP tools available
    4. If AI calls a tool → execute & continue
    5. Log the conversation turn
    """
    client = OpenAI(api_key=api_key)
    store = SessionStore()

    # ── RAG context from code ──
    from services.vector_store import VectorStore
    vs = VectorStore(api_key)
    vs.build(code_content)
    code_context = vs.retrieve(question)

    # ── Recent session context ──
    recent_context = store.get_recent_context(session_id, n_messages=4)

    # ── Build messages ──
    messages = [
        {
            "role": "system",
            "content": (
                "You are a code analysis assistant for AureliaScript. "
                "You can search past conversations using the provided tools. "
                "Use them when the user refers to previous discussions."
            ),
        },
    ]

    if recent_context:
        messages.append({
            "role": "system",
            "content": f"Recent conversation context:\n{recent_context}",
        })

    messages.append({
        "role": "user",
        "content": f"CODE CONTEXT:\n{code_context}\n\nQUESTION:\n{question}",
    })

    # ── First OpenAI call (with MCP tools) ──
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=MCP_TOOL_DEFINITIONS,
        tool_choice="auto",
        temperature=0,
    )

    message = response.choices[0].message

    # ── Handle tool calls ──
    if message.tool_calls:
        messages.append(message)

        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            tool_result = execute_mcp_tool(fn_name, fn_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

        # ── Second call with tool results ──
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
        message = response.choices[0].message

    answer = message.content

    # ── Save conversation turn ──
    store.save_conversation_turn(session_id, question, answer)

    return answer