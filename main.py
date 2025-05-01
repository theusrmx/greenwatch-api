import os
import uvicorn

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import Column, Integer, Float, DateTime, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.responses import JSONResponse

app = FastAPI()

# Database
Base = declarative_base()

project_dir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(project_dir, "sensors.db")
DATABASE_URL = "sqlite:///./sensors.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_utc_minus_3():
    return datetime.utcnow() - timedelta(hours=3)
  
# Database Model
class DBDataModel(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    umidade = Column(Float, nullable=False)
    temperatura = Column(Float, nullable=False)
    data = Column(DateTime, default=get_utc_minus_3, onupdate=get_utc_minus_3)

# Model de informações
class SensorData(BaseModel):
    id: Optional[int]
    umidade: float
    temperatura: float
    data: Optional[datetime]

    class Config:
        orm_mode = True


# Obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/')
def home():
  return 'GreenWatch'

@app.get("/sensor_api", response_model=List[SensorData])
def read_sensor_data(db: Session = Depends(get_db)):
    data = db.query(DBDataModel).all()
    return data

@app.post("/sensor_api", response_model=SensorData, status_code=status.HTTP_201_CREATED)
def create_sensor_data(data: SensorData, db: Session = Depends(get_db)):
    db_data = DBDataModel(**data.dict(exclude_unset=True))
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@app.on_event("startup")
def on_startup():
    # Cria tabelas
    Base.metadata.create_all(bind=engine)
    print("Tables created")
    

if __name__ == "__main__":
  uvicorn.run(app)
