from sqlalchemy import Integer, Column, String, Date, Boolean, Enum
from sqlalchemy import ForeignKey, Column
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.sql


Base = declarative_base()


"""
    columns = Person._sa_class_manager.mapper.columns.values()

    relationships = list(Person._sa_class_manager.mapper.relationships)
    for relationship in relationships:
        # attribute name
        print(relationships[0].class_attribute.key)
        # 'MANYTOONE' or 'ONETOMANY'
        print(relationship.direction.name)
        # backref name
        print(relationship.backref[0])
        # referenced table name
        relationship.entity.class_
"""


GENDER_CHOICES = ('female', 'male', 'other')

class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    gender = Column(Enum(*GENDER_CHOICES))
    username = Column(String(255), unique=True)
    password = Column(String(255), nullable=True)
    first_name = Column(String(32))
    last_name = Column(String(64))
    birth_date = Column(Date(), nullable=True)
    is_staff = Column(Boolean(), default=False)
    is_superuser = Column(Boolean(), default=False)
    home_id = Column(Integer(), ForeignKey('houses.id'))
    home = relationship('House', foreign_keys=[home_id], backref=backref('tenants', order_by=id))


class House(Base):
    __tablename__ = 'houses'
    id = Column(Integer, primary_key=True)
    location = Column(String(255))
    construction_date = Column(Date(), nullable=True)
    owner_id = Column(Integer(), ForeignKey(Person.id))
    owner = relationship(Person, foreign_keys=[owner_id], backref=backref('houses', order_by=id))

    def filter_by_authenticated_user(cls, authenticated_user):
        if not authenticated_user:
            return cls.filter(sqlalchemy.sql.false())
        if authenticated_user.is_superuser:
            return cls
        return cls.filter(
            cls.owner_id == authenticated_user.id or
            cls.tenants.id == authenticated_user.id
        )


OCCUPATION_CHOICES = ('EAT', 'SLEEP', 'WORK', 'COMMUTE', '_')

class DailyOccupation(Base):
    __tablename__ = 'daily_occupation'
    id = Column(Integer, primary_key=True)
    hours_per_day = Column(Integer())
    occupation = Column(Enum(*OCCUPATION_CHOICES))
    person_id = Column(Integer(), ForeignKey(Person.id, ondelete='CASCADE'))
    person = relationship(Person, foreign_keys=[person_id], backref=backref('daily_occupations', order_by=id))


class BankAccount(Base):
    __tablename__ = 'bank_account'
    id = Column(Integer, primary_key=True)
    location = Column(String(34))
    owner_id = Column(Integer(), ForeignKey(Person.id, ondelete='CASCADE'))
    owner = relationship(Person, foreign_keys=[owner_id], backref=backref('bank_accounts', order_by=id))

    def ensure_permissions(self, authenticated_user, operation, data):
        if authenticated_user.is_superuser:
            return True
        return self.owner_id == authenticated_user.id

    @classmethod
    def filter_permitted(cls, authenticated_user):
        if not authenticated_user:
            return cls.filter(sqlalchemy.sql.false())
        if authenticated_user.is_superuser:
            return cls
        return cls.filter(cls.owner_id == authenticated_user.id)
