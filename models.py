from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, asc, desc
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

    @classmethod
    def getCategoryID(cls, category):
        category = session.query(cls).filter_by(name=category).one()
        return category.id

    @classmethod
    def getCategory(cls, category_id):
        category = session.query(cls).filter_by(id=category_id).one()
        return category

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }

    @property
    def serialize_with_items(self):
        """Return object data in easily serializeable format"""
        items = Item.getByCategory(self.id)
        item_json = [i.serialize for i in items]
        return {
            'Item': item_json,
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(1000))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @classmethod
    def createItem(cls, name, description, category_id, user_id):
        newItem = cls(name=name, description=description,
                      category_id=category_id, user_id=user_id)
        session.add(newItem)
        session.commit()
        item = session.query(cls).filter_by(name=name).order_by(desc(cls.id)).first()
        return item.id

    @classmethod
    def updateItem(cls, item_id, name, description, category_id, user_id):
        editedItem = session.query(cls).filter_by(id=item_id).one()
        editedItem.name = name
        editedItem.description = description
        editedItem.category_id = category_id
        editedItem.user_id = user_id
        session.add(editedItem)
        session.commit()

    @classmethod
    def deleteItem(cls, item_id):
        item = session.query(cls).filter_by(id=item_id).one()
        session.delete(item)
        session.commit()

    @classmethod
    def getAllItems(cls):
        return session.query(cls).order_by(desc(cls.id)).all()

    @classmethod
    def getItemInfo(cls, item_id):
        item = session.query(cls).filter_by(id=item_id).one()
        return item

    @classmethod
    def getByCategory(cls, category_id):
        items = session.query(cls).filter_by(category_id=category_id).order_by(asc(cls.name)).all()
        return items

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'cat_id': self.category_id,
            'description': self.description,
            'name': self.name,
            'id': self.id,
        }


Base.metadata.create_all(engine)
