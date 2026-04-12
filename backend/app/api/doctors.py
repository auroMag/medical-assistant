from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, Doctor, Appointment, Patient, Chat
from app.services.auth_service import hash_password, verify_password
from app.models.schemas import DoctorCreate, DoctorResponse, DoctorUpdate, DoctorRecommendationRequest, DoctorLogin

router = APIRouter()

@router.post("/", response_model=DoctorResponse)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    existing = db.query(Doctor).filter(Doctor.email == doctor.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    data = doctor.model_dump()
    password = data.pop("password", None)
    
    db_doctor = Doctor(**data)
    if password:
        db_doctor.password_hash = hash_password(password)
    
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

@router.post("/login", response_model=DoctorResponse)
def login_doctor(credentials: DoctorLogin, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.email == credentials.email).first()
    if not doctor:
        raise HTTPException(status_code=401, detail="Email o password errati")
    if not doctor.password_hash:
        raise HTTPException(status_code=401, detail="Account senza password")
    if not verify_password(credentials.password, doctor.password_hash):
        raise HTTPException(status_code=401, detail="Email o password errati")
    return doctor

@router.get("/", response_model=list[DoctorResponse])
def get_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()

@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    return doctor

@router.get("/specialization/{spec}", response_model=list[DoctorResponse])
def get_by_specialization(spec: str, db: Session = Depends(get_db)):
    doctors = db.query(Doctor).filter(
        Doctor.specialization.ilike(f"%{spec}%")
    ).all()
    return doctors

@router.delete("/{doctor_id}")
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    db.delete(doctor)
    db.commit()
    return {"message": "Medico eliminato"}


@router.patch("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(doctor_id: int, update: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor


from app.services.gemini_service import recommend_doctor_specialization

@router.post("/recommend")
def recommend_doctor(request: DoctorRecommendationRequest, db: Session = Depends(get_db)):
    """
    Analizza i sintomi del paziente e raccomanda i medici più adatti.
    """

    #non request.get("message", "") perchè è dict
    message = request.message
    if not message:
        raise HTTPException(status_code=400, detail="Messaggio mancante")
    
    # Step 1: Chiedi all'AI la specializzazione
    recommendation = recommend_doctor_specialization(message)
    
    # Step 2: Cerca medici con quella specializzazione nel DB
    doctors = db.query(Doctor).filter(
        Doctor.specialization.ilike(f"%{recommendation['specialization']}%")
    ).all()
    
    # Step 3: Se non trova medici esatti, cerca medici di base
    if not doctors:
        doctors = db.query(Doctor).filter(
            Doctor.specialization.ilike("%medico di base%")
        ).all()
    
    return {
        "recommended_specialization": recommendation["specialization"],
        "reason": recommendation["reason"],
        "urgency": recommendation["urgency"],
        "doctors": [
            {
                "id": d.id,
                "name": d.name,
                "specialization": d.specialization,
                "email": d.email,
                "phone": d.phone
            }
            for d in doctors
        ]
    }

@router.get("/{doctor_id}/appointments-with-patients")
def get_doctor_appointments_with_patients(doctor_id: int, db: Session = Depends(get_db)):
    """Restituisce gli appuntamenti del medico con i dati dei pazienti"""
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).all()
    
    result = []
    for appt in appointments:
        patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        chats = db.query(Chat).filter(Chat.patient_id == appt.patient_id).all()
        
        result.append({
            "appointment_id": appt.id,
            "datetime": appt.datetime.isoformat(),
            "status": appt.status,
            "notes": appt.notes,
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "email": patient.email,
                "phone": patient.phone
            },
            "chat_history": [
                {
                    "message": c.message,
                    "response": c.response,
                    "created_at": c.created_at.isoformat()
                } for c in chats
            ]
        })
    
    return result