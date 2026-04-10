from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.auth_service import hash_password, verify_password
from app.models.database import get_db
from app.models.database import Patient
from app.models.schemas import PatientCreate, PatientResponse, PatientUpdate, PatientLogin

router = APIRouter()

@router.post("/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.email == patient.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    data = patient.model_dump()
    password = data.pop("password", None)
    
    db_patient = Patient(**data)
    if password:
        db_patient.password_hash = hash_password(password)
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.post("/login", response_model=PatientResponse)
def login(credentials: PatientLogin, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.email == credentials.email).first()
    if not patient:
        raise HTTPException(status_code=401, detail="Email o password errati")
    if not patient.password_hash:
        raise HTTPException(status_code=401, detail="Account senza password, contatta il supporto")
    if not verify_password(credentials.password, patient.password_hash):
        raise HTTPException(status_code=401, detail="Email o password errati")
    return patient

@router.get("/", response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return patient

@router.delete("/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    db.delete(patient)
    db.commit()
    return {"message": "Paziente eliminato"}

@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: int, update: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient