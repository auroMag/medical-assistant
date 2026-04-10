import chromadb
from sentence_transformers import SentenceTransformer

# Connessione a ChromaDB
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma_client.get_or_create_collection(
    name="medquad",
    metadata={"hnsw:space": "cosine"}
)

# Stesso modello usato per il caricamento
model = SentenceTransformer("all-MiniLM-L6-v2")

def search_medical_context(query: str, n_results: int = 3) -> list:
    query_embedding = model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    contexts = []
    for i in range(len(results["documents"][0])):
        contexts.append({
            "answer": results["documents"][0][i],
            "question": results["metadatas"][0][i]["question"],
            "focus": results["metadatas"][0][i]["focus"],
            "relevance": 1 - results["distances"][0][i]
        })
    
    return contexts