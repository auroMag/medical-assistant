import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# Connessione a ChromaDB
client = chromadb.HttpClient(host="localhost", port=8000)

# Crea o recupera la collection
collection = client.get_or_create_collection(
    name="medquad",
    metadata={"hnsw:space": "cosine"}
)

# Carica il JSON processato
json_path = os.path.join(os.path.dirname(__file__), "medquad_processed.json")
with open(json_path, "r", encoding="utf-8") as f:
    qa_pairs = json.load(f)

print(f"Caricate {len(qa_pairs)} coppie Q&A")

# Modello per gli embeddings (leggero e gratuito)
print("Caricamento modello embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Carica in batch per non sovraccaricare la memoria
BATCH_SIZE = 100
total = len(qa_pairs)

print("Inizio caricamento in ChromaDB...")
for i in range(0, total, BATCH_SIZE):
    batch = qa_pairs[i:i+BATCH_SIZE]
    
    # Testo da embeddare: domanda + focus
    texts = [f"{item['focus']}: {item['question']}" for item in batch]
    
    # Genera embeddings
    embeddings = model.encode(texts).tolist()
    
    # Prepara i dati
    ids = [f"medquad_{i+j}" for j in range(len(batch))]
    documents = [item["answer"] for item in batch]
    metadatas = [{"question": item["question"], "focus": item["focus"], "source": item["source"]} for item in batch]
    
    # Inserisci in ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"Caricati {min(i+BATCH_SIZE, total)}/{total}...")

print("Caricamento completato!")
print(f"Totale documenti in ChromaDB: {collection.count()}")