from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.database import get_db, Appointment, Doctor
from app.models.schemas import AppointmentCreate, AppointmentResponse, AppointmentUpdate

router = APIRouter()

@router.post("/", response_model=AppointmentResponse)
def create_appointment(appt: AppointmentCreate, db: Session = Depends(get_db)):
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == appt.doctor_id,
        Appointment.datetime == appt.datetime,
        Appointment.status == "scheduled"
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Slot già occupato per questo medico")
    
    db_appt = Appointment(**appt.model_dump())
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

@router.get("/", response_model=list[AppointmentResponse])
def get_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).all()

@router.get("/patient/{patient_id}", response_model=list[AppointmentResponse])
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    return db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).all()

@router.get("/doctor/{doctor_id}", response_model=list[AppointmentResponse])
def get_doctor_appointments(doctor_id: int, db: Session = Depends(get_db)):
    return db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).all()

@router.get("/doctor/{doctor_id}/slots")
def get_available_slots(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    
    booked = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "scheduled"
    ).all()
    booked_times = {a.datetime for a in booked}
    
    slots = []
    now = datetime.now()
    for day in range(1, 8):
        date = now + timedelta(days=day)
        for hour in range(9, 17):
            slot = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if slot not in booked_times:
                slots.append(slot.isoformat())
    
    return {
        "doctor_id": doctor_id,
        "doctor_name": doctor.name,
        "specialization": doctor.specialization,
        "available_slots": slots
    }

@router.get("/{appt_id}", response_model=AppointmentResponse)
def get_appointment(appt_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    return appt

@router.patch("/{appt_id}", response_model=AppointmentResponse)
def update_appointment(appt_id: int, update: AppointmentUpdate, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(appt, field, value)
    db.commit()
    db.refresh(appt)
    return appt

@router.delete("/{appt_id}")
def delete_appointment(appt_id: int, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")
    db.delete(appt)
    db.commit()
    return {"message": "Appuntamento eliminato"}