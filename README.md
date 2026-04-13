# MediAssist — Assistente Virtuale Sanitario

Assistente medico basato su RAG che combina LLaMA 3.3, ChromaDB e dataset medici (MedQuAD + MTSamples) per rispondere a domande cliniche, suggerire specialisti e gestire prenotazioni.

---

## Stack

**Backend:** FastAPI, PostgreSQL, ChromaDB, SQLAlchemy, Groq (LLaMA 3.3 + LLaMA 4 Vision)  
**Frontend:** HTML, CSS, JavaScript  
**Dataset:** MedQuAD (16.374 Q&A mediche), MTSamples (4.921 trascrizioni cliniche)  
**Infrastruttura:** Docker (PostgreSQL + ChromaDB containerizzati)

---

## Funzionalità

- Chat medica con RAG — recupera contesto dai dataset e genera risposte contestuali
- Triage automatico — classifica i messaggi in verde/giallo/rosso e mostra avvisi di emergenza
- Raccomandazione medico — analizza i sintomi e suggerisce la specializzazione più adatta
- Upload immagini diagnostiche — analisi con LLaMA 4 Vision
- Prenotazione appuntamenti — slot disponibili, conferma e cancellazione
- Storico chat — accessibile dal paziente e dal medico
- Dashboard medico — visualizzazione appuntamenti e chat precedenti dei pazienti
- Autenticazione — login/registrazione con password hashata (bcrypt)

---

## Come funziona il RAG

```
Messaggio paziente
      ↓
Embedding con all-MiniLM-L6-v2
      ↓
Ricerca per similarità coseno su ChromaDB (MedQuAD + MTSamples)
      ↓
Top 4 documenti più rilevanti → prompt contestuale
      ↓
LLaMA 3.3 70B genera la risposta in italiano
```

---

## Installazione

### Requisiti
- Python 3.10+
- Docker Desktop

### Setup

```bash
git clone https://github.com/auroMag/medical-assistant.git
cd medical-assistant

python -m venv venv
.\venv\Scripts\activate

cd backend
pip install -r requirements.txt
```

### Variabili d'ambiente

Crea `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_db_name
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

API key gratuita su [console.groq.com](https://console.groq.com)

### Avvio

```bash
# Avvia i container
docker-compose up -d

# Carica i dataset in ChromaDB (solo la prima volta)
python data/datasets/preprocess_datasets.py
python data/datasets/load_to_chromadb.py
python data/datasets/load_mtsamples_to_chromadb.py

# Avvia il backend
cd backend
uvicorn app.main:app --reload --port 8080
```

Apri `frontend/index.html` nel browser.  
API docs: `http://localhost:8080/docs`  
Area medici: `frontend/doctor.html`

---

## Dataset

**MedQuAD** — 47k Q&A mediche dell'NIH, usato per domande su malattie, sintomi e trattamenti  
**MTSamples** — trascrizioni cliniche reali, aggiunge contesto su come i medici descrivono i casi  

L'architettura ChromaDB supporta collection multiple, quindi aggiungere MIMIC-III richiede solo un nuovo script di preprocessing senza modificare il resto del sistema.

---

## Struttura

```
medical-assistant/
├── backend/
│   ├── app/
│   │   ├── api/          # routes FastAPI
│   │   ├── models/       # SQLAlchemy + Pydantic
│   │   ├── services/     # RAG, LLaMA, auth
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html        # login paziente
│   ├── chat.html         # chat medica
│   ├── appointments.html # prenotazioni
│   ├── doctor.html       # dashboard medico
│   └── style.css
├── data/datasets/        # script preprocessing
└── docker-compose.yml
```
