import shutil
import os
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.models.database import get_db, Chat, Patient
from app.models.schemas import ChatRequest, ChatResponse
from app.services.gemini_service import generate_medical_response, analyze_triage, generate_medical_response_with_image

router = APIRouter()

@router.post("/")
def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Genera risposta RAG
    result = generate_medical_response(
        user_message=request.message,
        patient_name=patient.name
    )

    # Analisi triage
    triage = analyze_triage(request.message)

    # Salva nel DB
    chat = Chat(
        patient_id=request.patient_id,
        message=request.message,
        response=result["response"]
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)

    # Risposta con triage incluso
    response_data = {
        "id": chat.id,
        "patient_id": chat.patient_id,
        "message": chat.message,
        "response": chat.response,
        "created_at": chat.created_at.isoformat(),
        "triage": triage
    }
    return JSONResponse(content=jsonable_encoder(response_data))

@router.get("/history/{patient_id}", response_model=list[ChatResponse])
def get_chat_history(patient_id: int, db: Session = Depends(get_db)):
    return db.query(Chat).filter(Chat.patient_id == patient_id).all()

@router.post("/with-image")
async def send_message_with_image(
    patient_id: int = Form(...),
    message: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    # Salva l'immagine
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    image_path = f"{upload_dir}/{patient_id}_{image.filename}"
    with open(image_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # Analizza con Groq Vision
    result = generate_medical_response_with_image(message, image_path, patient.name)

    # Analisi triage anche per immagini
    triage_message = message if message.strip() else "dolore o sintomo non specificato"
    triage = analyze_triage(triage_message)

    # Salva nel DB
    chat = Chat(
        patient_id=patient_id,
        message=f"{message} [immagine: {image.filename}]",
        response=result["response"]
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)

    response_data = {
        "id": chat.id,
        "patient_id": chat.patient_id,
        "message": chat.message,
        "response": chat.response,
        "created_at": chat.created_at.isoformat(),
        "triage": triage
    }
    return JSONResponse(content=jsonable_encoder(response_data))

