"""
Geographic Reference — matches Section 5.3 of the data dictionary.
District / Chiefdom reference tables (static data seeded once).
The submission_locations junction table is in submission.py.
"""
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.models.base import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


class District(Base):
    __tablename__ = "districts"

    id            = Column(Integer, primary_key=True)
    region_name   = Column(String(40))                              # East / North / North West / South / Western Area
    district_name = Column(String(60), unique=True, nullable=False)
    created_at    = Column(TIMESTAMPTZ, server_default=func.now())

    chiefdoms = relationship("Chiefdom", back_populates="district")


class Chiefdom(Base):
    __tablename__ = "chiefdoms"

    id            = Column(Integer, primary_key=True)
    district_id   = Column(Integer, ForeignKey("districts.id"), nullable=False)
    chiefdom_name = Column(String(80), nullable=False)
    created_at    = Column(TIMESTAMPTZ, server_default=func.now())

    district = relationship("District", back_populates="chiefdoms")
