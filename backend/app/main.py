from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.database import init_db
from app.api import patients, doctors, appointments, chat

app = FastAPI(
    title="Medical Assistant API",
    description="API per assistente virtuale sanitario",
    version="1.0.0"
)

# CORS - permette al frontend di comunicare col backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in produzione metti l'URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializza il database all'avvio
@app.on_event("startup")
def startup():
    init_db()

# Includi le routes
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

@app.get("/")
def root():
    return {"message": "Medical Assistant API is running"}