import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# Connessione a ChromaDB
client = chromadb.HttpClient(host="localhost", port=8000)

# Collection SEPARATA da MedQuAD
collection = client.get_or_create_collection(
    name="mtsamples",
    metadata={"hnsw:space": "cosine"}
)

# Carica il JSON processato
json_path = os.path.join(os.path.dirname(__file__), "mtsamples_processed.json")
with open(json_path, "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Caricate {len(records)} trascrizioni")

# Stesso modello di MedQuAD — fondamentale!
print("Caricamento modello embeddings...")
model = SentenceTransformer("all-MiniLM-L6-v2")

BATCH_SIZE = 100
total = len(records)

print("Inizio caricamento in ChromaDB...")
for i in range(0, total, BATCH_SIZE):
    batch = records[i:i+BATCH_SIZE]
    
    # Testo da embeddare: specializzazione + descrizione
    texts = [f"{item['specialty']}: {item['description']}" for item in batch]
    
    embeddings = model.encode(texts).tolist()
    
    ids = [f"mtsamples_{i+j}" for j in range(len(batch))]
    documents = [item["transcription"] for item in batch]
    metadatas = [{
        "specialty": item["specialty"],
        "description": item["description"],
        "sample_name": item["sample_name"],
        "keywords": item["keywords"],
        "source": "mtsamples"
    } for item in batch]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"Caricati {min(i+BATCH_SIZE, total)}/{total}...")

print("Caricamento completato!")
print(f"Totale documenti MTSamples in ChromaDB: {collection.count()}")