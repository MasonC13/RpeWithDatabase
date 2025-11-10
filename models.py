"""
SQLAlchemy Database Models for Truman RPE Tracker

This module defines the database schema using SQLAlchemy ORM.
The schema normalizes the flat CSV structure into relational tables.

CSV Structure:
- Base columns: Email, Last 4 Digits, Last Name, First Name, Position, Summer Attendance
- Dynamic date columns: One column per workout date (e.g., "01/15/2025", "01/16/2025")

Database Structure:
- athletes: Stores athlete information
- rpe_entries: Stores RPE values with athlete_id and date (normalized from date columns)
- caffeine_entries: Stores caffeine intake data
- sleep_entries: Stores sleep data
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Athlete(Base):
    """
    Athlete information table - stores static athlete data
    """
    __tablename__ = 'athletes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    last_4_digits = Column(String(4))
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    position = Column(String, nullable=False, index=True)
    summer_attendance = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rpe_entries = relationship("RPEEntry", back_populates="athlete", cascade="all, delete-orphan")
    caffeine_entries = relationship("CaffeineEntry", back_populates="athlete", cascade="all, delete-orphan")
    sleep_entries = relationship("SleepEntry", back_populates="athlete", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Athlete(email='{self.email}', name='{self.first_name} {self.last_name}', position='{self.position}')>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class RPEEntry(Base):
    """
    RPE (Rate of Perceived Exertion) entries table
    Each row represents one workout session for one athlete
    """
    __tablename__ = 'rpe_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    rpe_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    athlete = relationship("Athlete", back_populates="rpe_entries")
    
    # Ensure one entry per athlete per date
    __table_args__ = (
        UniqueConstraint('athlete_id', 'date', name='unique_athlete_date_rpe'),
    )
    
    def __repr__(self):
        return f"<RPEEntry(athlete_id={self.athlete_id}, date={self.date}, rpe_value={self.rpe_value})>"


class CaffeineEntry(Base):
    """
    Caffeine intake entries table
    """
    __tablename__ = 'caffeine_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    caffeine_mg = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    athlete = relationship("Athlete", back_populates="caffeine_entries")
    
    # Ensure one entry per athlete per date
    __table_args__ = (
        UniqueConstraint('athlete_id', 'date', name='unique_athlete_date_caffeine'),
    )
    
    def __repr__(self):
        return f"<CaffeineEntry(athlete_id={self.athlete_id}, date={self.date}, caffeine_mg={self.caffeine_mg})>"


class SleepEntry(Base):
    """
    Sleep quality entries table
    """
    __tablename__ = 'sleep_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    athlete_id = Column(Integer, ForeignKey('athletes.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    sleep_hours = Column(Float, nullable=False)
    sleep_quality = Column(Integer)  # Optional 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    athlete = relationship("Athlete", back_populates="sleep_entries")
    
    # Ensure one entry per athlete per date
    __table_args__ = (
        UniqueConstraint('athlete_id', 'date', name='unique_athlete_date_sleep'),
    )
    
    def __repr__(self):
        return f"<SleepEntry(athlete_id={self.athlete_id}, date={self.date}, sleep_hours={self.sleep_hours})>"


# Database connection helper functions
def get_engine(db_path='data/rpe_tracker.db'):
    """Create and return SQLAlchemy engine"""
    return create_engine(f'sqlite:///{db_path}', echo=False)


def get_session(engine=None):
    """Create and return a new database session"""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(db_path='data/rpe_tracker.db'):
    """Initialize the database - create all tables"""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    print(f"Database initialized at {db_path}")
    return engine