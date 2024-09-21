import datetime as dt

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from prep.database import Base


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, unique=True)

    token_limit = Column(Integer, default=2000)
    token_usage = Column(Integer, default=0)

    last_message_date = Column(DateTime, default=dt.datetime.utcnow)


class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))

    user_message = Column(String)
    assistant_message = Column(String)
