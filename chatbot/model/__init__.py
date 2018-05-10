from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///data.db', convert_unicode=True)
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    ))
Base = declarative_base()
Base.query = db_session.query_property()


def do_init():
    from chatbot.model.user import User  # noqa F401
    from chatbot.model.message import Message  # noqa F401
    Base.metadata.create_all(bind=engine)
