import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Patient
from ..schemas import PatientCreate, PatientRead

router = APIRouter()


@router.get("/patients", response_model=list[PatientRead])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()


@router.post("/patients", response_model=PatientRead, status_code=201)
def create_patient(body: PatientCreate, db: Session = Depends(get_db)):
    pid = body.id or f"P-{uuid.uuid4().hex[:8]}"
    if db.query(Patient).filter(Patient.id == pid).first():
        raise HTTPException(status_code=409, detail="Patient ID already exists")
    patient = Patient(
        id=pid,
        name=body.name,
        priority=body.priority,
        arrival_minute=body.arrival_minute,
        service_duration_minutes=body.service_duration_minutes,
        required_specialty=body.required_specialty,
        status="waiting",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
