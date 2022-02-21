import datetime

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.types import Date
from sqlalchemy.orm import relationship

from flaskr.database import Base, init_db


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<user: {self.username}, password: {self.password}>"


class Archive(Base):
    __tablename__ = 'archives'

    id = Column(String, primary_key=True)
    name = Column(String)
    archive_path = Column(String)
    tarfile_path = Column(String)
    size = Column(Integer)
    date = Column(Date, default=datetime.datetime.now())

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', foreign_keys=user_id)


    def __repr__(self):
        return '<ArchiveID: %r, Archive Path: %r>' % (self.id, self.archive_path)


init_db()
