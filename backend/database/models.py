from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

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

# Create the tables in the database
Base.metadata.create_all(bind=engine)
