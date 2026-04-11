import chromadb
from sentence_transformers import SentenceTransformer

# Connessione a ChromaDB
chroma_client = chromadb.HttpClient(host="localhost", port=8000)

# Due collection
medquad_collection = chroma_client.get_or_create_collection(
    name="medquad",
    metadata={"hnsw:space": "cosine"}
)

mtsamples_collection = chroma_client.get_or_create_collection(
    name="mtsamples",
    metadata={"hnsw:space": "cosine"}
)

# Stesso modello per entrambe
model = SentenceTransformer("all-MiniLM-L6-v2")

def search_medical_context(query: str, n_results: int = 3) -> list:
    """
    Cerca i documenti più rilevanti in entrambe le collection.
    Restituisce una lista combinata di contesti medici.
    """
    query_embedding = model.encode([query]).tolist()
    
    contexts = []

    # Cerca in MedQuAD
    try:
        medquad_results = medquad_collection.query(
            query_embeddings=query_embedding,
            n_results=2,
            include=["documents", "metadatas", "distances"]
        )
        for i in range(len(medquad_results["documents"][0])):
            contexts.append({
                "answer": medquad_results["documents"][0][i],
                "question": medquad_results["metadatas"][0][i].get("question", ""),
                "focus": medquad_results["metadatas"][0][i].get("focus", ""),
                "relevance": 1 - medquad_results["distances"][0][i],
                "source": "MedQuAD"
            })
    except Exception as e:
        print(f"Errore ricerca MedQuAD: {e}")

    # Cerca in MTSamples
    try:
        mtsamples_results = mtsamples_collection.query(
            query_embeddings=query_embedding,
            n_results=2,
            include=["documents", "metadatas", "distances"]
        )
        for i in range(len(mtsamples_results["documents"][0])):
            contexts.append({
                "answer": mtsamples_results["documents"][0][i],
                "question": mtsamples_results["metadatas"][0][i].get("description", ""),
                "focus": mtsamples_results["metadatas"][0][i].get("specialty", ""),
                "relevance": 1 - mtsamples_results["distances"][0][i],
                "source": "MTSamples"
            })
    except Exception as e:
        print(f"Errore ricerca MTSamples: {e}")

    # Ordina per rilevanza
    contexts.sort(key=lambda x: x["relevance"], reverse=True)
    
    return contexts