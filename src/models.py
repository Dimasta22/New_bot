from sqlalchemy import Column, Integer, String

from botmanlib.models import Database

database = Database()
Base = database.Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)


class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    discription = Column(String)


Session = database.create_session("Session")