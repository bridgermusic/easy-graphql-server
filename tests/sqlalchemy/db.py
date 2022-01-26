from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base


engine = create_engine('sqlite://', echo=True)
session = Session(engine)


def init():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
