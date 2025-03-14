from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from .models import Base, Club, Content

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def add_club(name, description):
    with Session() as session:
        club = Club(name=name, description=description)
        session.add(club)
        session.commit()
        return club.id

def add_content(club_id, content_type, content):
    with Session() as session:
        # Convert dictionary to string if content is a dictionary
        if isinstance(content, dict):
            content = str(content)
            
        content_obj = Content(
            club_id=club_id,
            type=content_type,
            content=content,
            created_at=datetime.now()
        )
        session.add(content_obj)
        session.commit()
        return content_obj.id

def get_club_contents(club_id):
    with Session() as session:
        return session.query(Content).filter(Content.club_id == club_id).all()