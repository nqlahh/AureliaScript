from openai import OpenAI


class VectorStore:
    """
    Simple vector store for RAG (Retrieval-Augmented Generation).
    Uses OpenAI embeddings to store and retrieve relevant code chunks.
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.chunks = []
        self.embeddings = []

    def build(self, code_content: str):
        """
        Splits code into chunks and generates embeddings for each chunk.
        """
        # Split code into logical chunks (functions, classes, etc.)
        self.chunks = self._split_code(code_content)

        # Generate embeddings for each chunk
        for chunk in self.chunks:
            embedding = self._get_embedding(chunk)
            self.embeddings.append(embedding)

    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves the most relevant chunks based on the query.
        Returns concatenated context from top-k chunks.
        """
        if not self.chunks:
            return ""

        # Get query embedding
        query_embedding = self._get_embedding(query)

        # Calculate similarity scores
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((similarity, i))

        # Sort by similarity and get top-k
        similarities.sort(reverse=True)
        top_indices = [idx for _, idx in similarities[:top_k]]

        # Concatenate relevant chunks
        context = "\n\n".join([self.chunks[idx] for idx in top_indices])
        return context

    def _split_code(self, code_content: str) -> list:
        """
        Splits code into chunks based on function/class definitions.
        Falls back to paragraph-based splitting if no definitions found.
        """
        # Try to split by class/function definitions
        chunks = []
        lines = code_content.split("\n")
        current_chunk = []

        for line in lines:
            if (line.strip().startswith("class ") or line.strip().startswith("def ")) and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        # Fallback: if no chunks found, split by paragraphs
        if not chunks:
            chunks = [paragraph.strip() for paragraph in code_content.split("\n\n") if paragraph.strip()]

        return chunks if chunks else [code_content]

    def _get_embedding(self, text: str) -> list:
        """
        Gets embeddings from OpenAI API.
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception:
            # Fallback: return a zero vector if API call fails
            return [0.0] * 1536

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """
        Calculates cosine similarity between two vectors.
        """
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = (sum(a ** 2 for a in vec1)) ** 0.5
        magnitude2 = (sum(b ** 2 for b in vec2)) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
