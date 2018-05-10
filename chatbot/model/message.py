from chatbot.model import Base
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime


class Message(Base):

    __tablename__ = 'messages'

    idx = Column(Integer, primary_key=True)
    id = Column(String)
    uid = Column(Integer)
    text = Column(String)
    type = Column(Integer)
    interface = Column(String)
    datetime = Column(DateTime)
    state = Column(String)
    ext = Column(String)
