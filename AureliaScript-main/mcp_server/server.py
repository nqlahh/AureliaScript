"""
AureliaScript MCP Server — Session Logs

Exposes session log tools via the Model Context Protocol.
The AI (or any MCP client) can search/retrieve conversation history
through this standardized interface.

Run standalone:
    python -m mcp_server.server
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from services.session_store import SessionStore

mcp = FastMCP("AureliaScript-SessionLogs", version="1.0.0")
store = SessionStore()


@mcp.tool()
def search_past_conversations(query: str, n_results: int = 5) -> str:
    """
    Search past chat conversations semantically.
    Use when the user refers to previous discussions or past conversations.
    """
    results = store.search_sessions(query, min(n_results, 10))
    if not results:
        return "No past conversations found."
    output = []
    for r in results:
        output.append(
            f"[Session: {r['session_id']} | {r['role']} | "
            f"{r['timestamp']} | Relevance: {r['relevance']}]\n"
            f"{r['content'][:500]}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
def get_session_history(session_id: str) -> str:
    """Retrieve full conversation history for a specific session."""
    messages = store.get_session(session_id)
    if not messages:
        return f"No messages found for session: {session_id}"
    output = []
    for msg in messages:
        output.append(f"[{msg['role'].upper()} | {msg['timestamp']}]\n{msg['content'][:500]}")
    return "\n\n".join(output)


@mcp.tool()
def list_all_sessions() -> str:
    """List all past conversation sessions."""
    sessions = store.list_sessions()
    if not sessions:
        return "No past sessions found."
    output = []
    for s in sessions:
        output.append(
            f"- Session: {s['session_id']} | "
            f"Messages: {s['message_count']} | "
            f"Last Active: {s['last_active']}"
        )
    return "\n".join(output)


@mcp.tool()
def delete_session_log(session_id: str) -> str:
    """Delete a session and all its messages."""
    deleted = store.delete_session(session_id)
    return f"Session '{session_id}' deleted." if deleted else f"Session '{session_id}' not found."


@mcp.tool()
def get_session_stats() -> str:
    """Get statistics about stored session logs."""
    stats = store.get_stats()
    return (
        f"Session Log Statistics:\n"
        f"- Total Messages: {stats['total_messages']}\n"
        f"- Total Sessions: {stats['total_sessions']}\n"
        f"- Storage: ChromaDB (Persistent)"
    )


if __name__ == "__main__":
    mcp.run()