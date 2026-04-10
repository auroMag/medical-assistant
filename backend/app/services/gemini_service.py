from groq import Groq
from app.config import GROQ_API_KEY
from app.services.rag_service import search_medical_context

client = Groq(api_key=GROQ_API_KEY)

def generate_medical_response(user_message: str, patient_name: str = "paziente") -> dict:
    # Step 1: Cerca contesto rilevante
    contexts = search_medical_context(user_message, n_results=3)
    
    # Step 2: Costruisci il contesto
    context_text = ""
    for i, ctx in enumerate(contexts):
        if ctx["relevance"] > 0.3:
            context_text += f"\n--- Informazione medica {i+1} ---\n"
            context_text += f"Argomento: {ctx['focus']}\n"
            context_text += f"Domanda simile: {ctx['question']}\n"
            context_text += f"Risposta medica: {ctx['answer']}\n"
    
    # Step 3: Costruisci il prompt
    if context_text:
        system_prompt = """Sei un assistente medico virtuale professionale e empatico. 
Rispondi in italiano in modo chiaro e comprensibile.
Usa le informazioni mediche fornite come contesto per rispondere.
Ricorda sempre di consigliare di consultare un medico per diagnosi e trattamenti specifici."""

        user_prompt = f"""CONTESTO MEDICO:
{context_text}

DOMANDA DEL PAZIENTE ({patient_name}):
{user_message}

Fornisci una risposta utile, accurata e empatica basandoti sul contesto medico fornito."""
    else:
        system_prompt = """Sei un assistente medico virtuale professionale e empatico.
Rispondi in italiano in modo chiaro e comprensibile.
Ricorda sempre di consigliare di consultare un medico per diagnosi e trattamenti specifici."""

        user_prompt = f"DOMANDA DEL PAZIENTE ({patient_name}): {user_message}"
    
    # Step 4: Chiedi a Groq
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1024,
        temperature=0.7
    )
    
    return {
        "response": response.choices[0].message.content,
        "contexts_used": len([c for c in contexts if c["relevance"] > 0.3]),
        "top_topics": [c["focus"] for c in contexts[:2]]
    }


def recommend_doctor_specialization(user_message: str) -> dict:
    """
    Analizza il messaggio del paziente e raccomanda la specializzazione
    medica più adatta.
    """
    system_prompt = """Sei un assistente medico che analizza i sintomi dei pazienti.
Il tuo compito è identificare la specializzazione medica più adatta in base ai sintomi descritti.
Rispondi SOLO con un JSON valido, nessun testo aggiuntivo, nel seguente formato:
{
    "specialization": "nome della specializzazione in italiano",
    "reason": "breve spiegazione del perché questa specializzazione",
    "urgency": "bassa/media/alta"
}

Specializzazioni disponibili: Cardiologo, Pediatra, Dermatologo, Neurologo, Ortopedico, 
Gastroenterologo, Pneumologo, Endocrinologo, Psichiatra, Oftalmologo, 
Otorinolaringoiatra, Urologo, Ginecologo, Medico di base"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Sintomi del paziente: {user_message}"}
        ],
        max_tokens=256,
        temperature=0.3
    )
    
    import json
    try:
        result = json.loads(response.choices[0].message.content)
    except:
        result = {
            "specialization": "Medico di base",
            "reason": "Per una valutazione generale dei sintomi",
            "urgency": "media"
        }
    
    return result


import base64

def generate_medical_response_with_image(user_message: str, image_path: str, patient_name: str = "paziente") -> dict:
    """Analizza un'immagine diagnostica con Groq Vision"""
    
    # Leggi e codifica l'immagine in base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Determina il tipo di immagine
    ext = image_path.split(".")[-1].lower()
    media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
    
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",  # modello con vision
        messages=[
            {
                "role": "system",
                "content": """Sei un assistente medico che analizza immagini diagnostiche.
Rispondi in italiano in modo chiaro e professionale.
Descrivi quello che vedi nell'immagine e fornisci osservazioni generali.
Ricorda sempre di consigliare una valutazione medica professionale."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Paziente {patient_name}: {user_message}"
                    }
                ]
            }
        ],
        max_tokens=1024
    )
    
    return {
        "response": response.choices[0].message.content,
        "contexts_used": 0,
        "top_topics": ["Analisi immagine diagnostica"]
    }


def analyze_triage(message: str) -> dict:
    """
    Analizza il messaggio del paziente e determina il livello di triage.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Sei un sistema di triage medico. Analizza il messaggio del paziente e restituisci SOLO un JSON valido senza testo aggiuntivo:
{
    "level": "verde/giallo/rosso",
    "reason": "breve motivazione",
    "action": "azione consigliata"
}

Livelli:
- verde: sintomi lievi, nessuna urgenza
- giallo: sintomi moderati, valutazione medica consigliata entro 24-48h
- rosso: emergenza, chiamare il 118 o andare al pronto soccorso immediatamente

Esempi rosso: dolore al petto, difficoltà respiratorie gravi, perdita di coscienza, emorragia, ictus
Esempi giallo: febbre alta persistente, dolore moderato, sintomi che peggiorano
Esempi verde: raffreddore, leggero mal di testa, domande generali"""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        max_tokens=150,
        temperature=0.1
    )

    import json
    try:
        text = response.choices[0].message.content.strip()
        # rimuovi eventuali backticks
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        return {"level": "verde", "reason": "Analisi non disponibile", "action": "Continua normalmente"}