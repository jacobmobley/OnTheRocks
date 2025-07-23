from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from ..models import UserDrinkLog
from ..database import engine
from typing import List, Optional

router = APIRouter(prefix="/logs", tags=["logs"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=UserDrinkLog)
def create_log(log: UserDrinkLog, session: Session = Depends(get_session)):
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

@router.get("/", response_model=List[UserDrinkLog])
def read_logs(user_id: Optional[int] = Query(None), drink_id: Optional[int] = Query(None), session: Session = Depends(get_session)):
    query = select(UserDrinkLog)
    if user_id is not None:
        query = query.where(UserDrinkLog.user_id == user_id)
    if drink_id is not None:
        query = query.where(UserDrinkLog.drink_id == drink_id)
    logs = session.exec(query).all()
    return logs

@router.get("/{log_id}", response_model=UserDrinkLog)
def read_log(log_id: int, session: Session = Depends(get_session)):
    log = session.get(UserDrinkLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@router.delete("/{log_id}")
def delete_log(log_id: int, session: Session = Depends(get_session)):
    log = session.get(UserDrinkLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    session.delete(log)
    session.commit()
    return {"ok": True} 