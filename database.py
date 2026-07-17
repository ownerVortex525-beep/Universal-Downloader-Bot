from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    download_count = Column(Integer, default=0)
    joined_date = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class Download(Base):
    __tablename__ = 'downloads'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    url = Column(Text, nullable=False)
    platform = Column(String(50))
    file_type = Column(String(20))
    status = Column(String(20))
    downloaded_at = Column(DateTime, default=datetime.utcnow)

# Create engine and tables
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)