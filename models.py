from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)

    @classmethod
    def createUser(cls, login_session):
        newUser = cls(name=login_session['username'], email=login_session[
                       'email'])
        session.add(newUser)
        session.commit()
        user = session.query(cls).filter_by(email=login_session['email']).one()
        return user.id

    @classmethod
    def getUserInfo(cls, user_id):
        user = session.query(cls).filter_by(id=user_id).one()
        return user

    @classmethod
    def getUserID(cls, email):
        try:
            user = session.query(cls).filter_by(email=email).one()
            return user.id
        except:
            return None


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @classmethod
    def createCategory(cls, category):
        try:
            session.query(cls).filter_by(name=category).one()
        except:
            newCategory = cls(name=category)
            session.add(newCategory)
            session.commit()

    @classmethod
    def getAllCategories(cls):
        return session.query(cls).order_by(asc(cls.name))


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'cat_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }


Base.metadata.create_all(engine)
