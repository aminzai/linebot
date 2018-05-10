from chatbot.model import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean


class User(Base):
    __tablename__ = 'users'

    idx = Column(Integer, primary_key=True)
    id = Column(String)
    interface = Column(String)
    display_name = Column(String)
    admin = Column(Boolean)
