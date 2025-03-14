from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Club(Base):
    __tablename__ = 'clubs'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime)
    contents = relationship("Content", back_populates="club")

class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey('clubs.id'))
    type = Column(String)  # poster, social_media_post, newsletter
    content = Column(String)
    created_at = Column(DateTime)
    club = relationship("Club", back_populates="contents")