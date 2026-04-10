from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, Doctor
from app.models.schemas import DoctorCreate, DoctorResponse, DoctorUpdate, DoctorRecommendationRequest

router = APIRouter()

@router.post("/", response_model=DoctorResponse)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    existing = db.query(Doctor).filter(Doctor.email == doctor.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    db_doctor = Doctor(**doctor.model_dump())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

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