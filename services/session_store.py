"""
ChromaDB-backed session log store for chat conversations.
"""

import chromadb
from datetime import datetime
from typing import List, Dict
import uuid


class SessionStore:
    def __init__(self, persist_dir: str = "./session_data"):
        if persist_dir:
            self.client = chromadb.PersistentClient(path=persist_dir)
        else:
            self.client = chromadb.Client()

        self.collection = self.client.get_or_create_collection(
            name="session_logs",
            metadata={"hnsw:space": "cosine"}
        )

    # ── Session Management ──────────────────────────────────────

    def create_session(self) -> str:
        session_id = (
            f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f"_{uuid.uuid4().hex[:6]}"
        )
        return session_id
    
    def list_sessions(self) -> List[Dict]:
        results = self.collection.get(include=["documents", "metadatas"])
        session_map = {}
        for doc, meta in zip(results["documents"], results["metadatas"]):
            sid = meta["session_id"]
            if sid not in session_map:
                session_map[sid] = {
                    "session_id": sid,
                    "message_count": 0,
                    "last_active": meta["timestamp"],
                    "filename": None,
                }
            
            # Only count actual chat messages (ignore system_code, system_filename)
            if meta["role"] in ["user", "assistant"]:
                session_map[sid]["message_count"] += 1

            if meta["timestamp"] > session_map[sid]["last_active"]:
                session_map[sid]["last_active"] = meta["timestamp"]

            # Grab the saved filename
            if meta["role"] == "system_filename" and doc:
                session_map[sid]["filename"] = doc

        return sorted(session_map.values(), key=lambda x: x["last_active"], reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        results = self.collection.get(where={"session_id": session_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return True
        return False

    # ── Message Storage ─────────────────────────────────────────

    def save_message(self, session_id: str, role: str, content: str):
        timestamp = datetime.now().isoformat()
        msg_id = f"{session_id}_{role}_{uuid.uuid4().hex[:8]}"
        doc = content[:8000]
        self.collection.upsert(
            documents=[doc],
            metadatas=[{
                "session_id": session_id,
                "role": role,
                "timestamp": timestamp,
            }],
            ids=[msg_id],
        )

    def save_conversation_turn(self, session_id: str, user_msg: str, assistant_msg: str):
        self.save_message(session_id, "user", user_msg)
        self.save_message(session_id, "assistant", assistant_msg)

    # ── Code Content Storage ────────────────────────────────────

    def save_code_content(self, session_id: str, code_content: str):
        results = self.collection.get(
            where={"$and": [
                {"session_id": session_id},
                {"role": "system_code"}
            ]}
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

        timestamp = datetime.now().isoformat()
        msg_id = f"{session_id}_code_{uuid.uuid4().hex[:8]}"
        self.collection.upsert(
            documents=[code_content[:50000]],
            metadatas=[{
                "session_id": session_id,
                "role": "system_code",
                "timestamp": timestamp,
            }],
            ids=[msg_id],
        )

    def get_code_content(self, session_id: str) -> str:
        results = self.collection.get(
            where={"$and": [
                {"session_id": session_id},
                {"role": "system_code"}
            ]},
            include=["documents"]
        )
        if results["documents"]:
            return results["documents"][0]
        return ""

    # ── Generic Metadata Storage (filename, etc.) ───────────────

    def save_metadata(self, session_id: str, key: str, value: str):
        """Save a metadata value (like filename) for a session."""
        results = self.collection.get(
            where={"$and": [
                {"session_id": session_id},
                {"role": key}
            ]}
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

        timestamp = datetime.now().isoformat()
        msg_id = f"{session_id}_{key}_{uuid.uuid4().hex[:8]}"
        self.collection.upsert(
            documents=[value[:1000]],
            metadatas=[{
                "session_id": session_id,
                "role": key,
                "timestamp": timestamp,
            }],
            ids=[msg_id],
        )

    def get_metadata(self, session_id: str, key: str) -> str:
        """Retrieve a metadata value for a session."""
        results = self.collection.get(
            where={"$and": [
                {"session_id": session_id},
                {"role": key}
            ]},
            include=["documents"]
        )
        if results["documents"]:
            return results["documents"][0]
        return ""

    # ── Retrieval ───────────────────────────────────────────────

    def get_session(self, session_id: str) -> List[Dict]:
        results = self.collection.get(
            where={"session_id": session_id},
            include=["documents", "metadatas"],
        )
        messages = []
        if results["documents"]:
            for doc, meta in zip(results["documents"], results["metadatas"]):
                messages.append({
                    "role": meta["role"],
                    "content": doc,
                    "timestamp": meta["timestamp"],
                })
        messages.sort(key=lambda x: x["timestamp"])
        return messages

    def search_sessions(self, query: str, n_results: int = 5) -> List[Dict]:
        count = self.collection.count()
        if count == 0:
            return []
        n_results = min(n_results, count)
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        matches = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                matches.append({
                    "content": doc,
                    "session_id": meta["session_id"],
                    "role": meta["role"],
                    "timestamp": meta["timestamp"],
                    "relevance": round(1 - dist, 4),
                })
        return matches

    def get_recent_context(self, session_id: str, n_messages: int = 6) -> str:
        messages = self.get_session(session_id)
        messages = [m for m in messages if m["role"] not in ["system_code", "system_filename"]]
        recent = messages[-n_messages:] if len(messages) > n_messages else messages
        parts = [f"[{m['role'].upper()}]: {m['content'][:500]}" for m in recent]
        return "\n\n".join(parts)

    # ── Stats ───────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        count = self.collection.count()
        sessions = self.list_sessions()
        return {
            "total_messages": count,
            "total_sessions": len(sessions),
            "collection_name": self.collection.name,
        }
