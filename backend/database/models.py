from sqlalchemy import Column, Integer, String, Text, create_engine, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
import datetime

# Setup SQLite database locally
SQLALCHEMY_DATABASE_URL = "sqlite:///./clinicaflow.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PatientProfile(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String) 
    
    # Permanent Medical Profile
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    blood_group = Column(String)
    family_history = Column(Text) # e.g., "Father: Diabetes, Mother: Hypertension"
    pre_existing_conditions = Column(Text) # e.g., "Asthma, Peanut Allergy"
    
    appointments = relationship("Appointment", back_populates="patient")
    reports = relationship("MedicalReport", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")

class DoctorProfile(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String, index=True)
    specialty = Column(String) # 'Cardiology' or 'General Medicine'
    
    appointments = relationship("Appointment", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    appointment_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="Scheduled") # 'Scheduled', 'Completed'
    
    doctor = relationship("DoctorProfile", back_populates="appointments")
    patient = relationship("PatientProfile", back_populates="appointments")

class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    report_url = Column(String)
    report_data = Column(Text) # JSON serialized data
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("PatientProfile", back_populates="reports")

# Create the tables in the database
class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    medicine_name = Column(String, index=True)
    frequency = Column(String)
    date_given = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("PatientProfile", back_populates="prescriptions")
    doctor = relationship("DoctorProfile", back_populates="prescriptions")

# Create the tables in the database
Base.metadata.create_all(bind=engine)
