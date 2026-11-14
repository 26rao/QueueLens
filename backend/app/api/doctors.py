from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Doctor, DoctorUnavailability

router = APIRouter()


@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    unavailabilities = db.query(DoctorUnavailability).all()

    result = []
    for d in doctors:
        unavs = [
            {"id": u.id, "doctor_id": u.doctor_id, "start_minute": u.start_minute,
             "end_minute": u.end_minute, "reason": u.reason}
            for u in unavailabilities if u.doctor_id == d.id
        ]
        result.append({
            "id": d.id, "name": d.name,
            "specialties": d.specialties if isinstance(d.specialties, list) else [],
            "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute,
            "active": d.active, "unavailabilities": unavs,
        })
    return result
