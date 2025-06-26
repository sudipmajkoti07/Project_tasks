import uuid
import io
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from database.db import insert_document_metadata, insert_chunk_metadata

# Initialize Qdrant client (make sure Qdrant is running on this host/port)
qdrant_client = QdrantClient(host="localhost", port=6333)

# Collection & embedding model config
collection_name = "documents"
embedding_model_name = "all-MiniLM-L6-v2"
embedding_model = SentenceTransformer(embedding_model_name)

# Recreate collection (dev only)
def create_qdrant_collection():
    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config={"size": 384, "distance": "Cosine"}
    )

create_qdrant_collection()

def extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    elif content_type == "text/plain":
        return file_bytes.decode("utf-8")
    return ""

def chunk_text(text: str, max_tokens: int = 150) -> list:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk.split()) + len(paragraph.split()) <= max_tokens:
            current_chunk += " " + paragraph
        else:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def process_uploaded_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    text = extract_text(file_bytes, content_type)
    if not text.strip():
        return "❌ No readable content found."

    file_type = "pdf" if content_type == "application/pdf" else "txt"
    chunking_method = "recursive"
    chunks = chunk_text(text)
    embeddings = embedding_model.encode(chunks).tolist()

    document_id = insert_document_metadata(
        filename=filename,
        file_type=file_type,
        chunking_method=chunking_method,
        embedding_model=embedding_model_name,
        chunk_count=len(chunks)
    )

    insert_chunk_metadata(document_id, chunks)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk,
                "source": filename,
                "document_id": document_id
            }
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    qdrant_client.upsert(collection_name=collection_name, points=points)

    return f"✅ Stored {len(chunks)} chunks from '{filename}' into Qdrant & metadata into SQLite."
