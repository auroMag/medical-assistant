from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# ─── PATIENT ────────────────────────────────────────────────
class PatientBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class PatientCreate(PatientBase):
    password: Optional[str] = None

class PatientLogin(BaseModel):
    email: EmailStr
    password: str

class PatientResponse(PatientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # ex orm_mode in Pydantic v2

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# ─── DOCTOR ─────────────────────────────────────────────────
class DoctorBase(BaseModel):
    name: str
    specialization: str
    email: EmailStr
    phone: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int

    class Config:
        from_attributes = True

class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# ─── APPOINTMENT ────────────────────────────────────────────
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    datetime: datetime
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    datetime: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: int
    status: str
    patient: Optional[PatientResponse] = None
    doctor: Optional[DoctorResponse] = None

    class Config:
        from_attributes = True


# ─── CHAT ───────────────────────────────────────────────────
class ChatRequest(BaseModel):
    patient_id: int
    message: str

class ChatResponse(BaseModel):
    id: int
    patient_id: int
    message: str
    response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DoctorRecommendationRequest(BaseModel):
    message: str