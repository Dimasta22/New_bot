from botmanlib.models import Database, BaseUser
from sqlalchemy import Column, Integer, String

database = Database()
Base = database.Base


class User(Base, BaseUser):
    __tablename__ = 'users'


class Products(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    discription = Column(String)


Session = database.create_session("Session")
