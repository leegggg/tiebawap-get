from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, Float, BigInteger, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

Base = declarative_base()

class ImagePost(Base):
    # 表的名字:
    __tablename__ = 'IMAGE_POST'

    def __init__(self):
        pass

    # 表的结构:
    img = Column(String, primary_key=True)  # observation,
    thread = Column(String, primary_key=True)  # observation,
    mod_date = Column(DateTime)


class Content(Base):
    # 表的名字:
    __tablename__ = 'CONTENT'

    def __init__(self):
        pass

    # 表的结构:
    cid = Column(String, primary_key=True)
    content = Column(String)
    source = Column(String)
    mod_date = Column(DateTime)


class Content_HTML(Base):
    # 表的名字:
    __tablename__ = 'CONTENT_HTML'

    def __init__(self):
        pass

    # 表的结构:
    cid = Column(String, primary_key=True)
    content = Column(String)
    source = Column(String)
    mod_date = Column(DateTime)


class AttachementHeader(Base):
    # 表的名字:
    __tablename__ = 'ATTACHEMENT_HEADER'

    def __init__(self):
        pass

    # 表的结构:
    downloaded = Column(DateTime)
    title = Column(String)
    source = Column(String)  # observation,
    link = Column(String, primary_key=True)
    path = Column(String)
    pid = Column(String)
    mod_date = Column(DateTime)
    status = Column(Integer)
    comment = Column(String)


class Link(Base):
    # 表的名字:
    __tablename__ = 'LINK'

    def __init__(self):
        pass

    # 表的结构:
    link = Column(String, primary_key=True)
    title = Column(String)  # observation,
    source = Column(String)  # observation,
    mod_date = Column(DateTime)


class Thread(Base):
    # 表的名字:
    __tablename__ = 'THREAD'

    def __init__(self):
        pass

    # 表的结构:
    kz = Column(BigInteger, primary_key=True)
    kw = Column(String)
    title = Column(String)
    good = Column(Boolean)
    top = Column(Boolean)
    info = Column(String)
    auth = Column(String)
    last_date = Column(DateTime)
    mod_date = Column(DateTime)


class ThreadHeader(Base):
    # 表的名字:
    __tablename__ = 'THREAD_HEADER'

    def __init__(self):
        pass

    # 表的结构:
    kz = Column(BigInteger, primary_key=True)
    kw = Column(String)
    title = Column(String)
    good = Column(Boolean)
    top = Column(Boolean)
    click = Column(BigInteger)
    reply = Column(BigInteger)
    comment = Column(String)
    last_date = Column(DateTime)
    mod_date = Column(DateTime)


class ThreadError(Base):
    # 表的名字:
    __tablename__ = 'THREAD_ERROR'

    def __init__(self):
        pass

    # 表的结构:
    uid = Column(String, primary_key=True)
    kz = Column(BigInteger)
    kw = Column(String)
    pn = Column(BigInteger)
    code = Column(Integer)
    comment = Column(String)
    detail = Column(String)
    mod_date = Column(DateTime)




class PostHeader(Base):
    # 表的名字:
    __tablename__ = 'POST_HEADER'

    def __init__(self):
        pass

    # 表的结构:
    pid = Column(String)
    parent = Column(BigInteger, primary_key=True)
    floor = Column(Integer, primary_key=True)
    flr = Column(Boolean, primary_key=True)
    un = Column(String)
    to = Column(String)
    create_date = Column(DateTime)
    cid = Column(String)
    mod_date = Column(DateTime)


class PostAttachement(Base):
    # 表的名字:
    __tablename__ = 'POST_ATTACHEMENT'

    def __init__(self):
        pass

    # 表的结构:
    parent = Column(BigInteger, primary_key=True)
    floor = Column(Integer, primary_key=True)
    link = Column(String, primary_key=True)
    attId = Column(String)
    status = Column(Integer)
    comment = Column(String)
    mod_date = Column(DateTime)

