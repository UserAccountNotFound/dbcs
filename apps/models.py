from email.policy import default
from apps import db
from sqlalchemy.exc import SQLAlchemyError
from apps.exceptions.exception import InvalidUsage
import datetime as dt
from sqlalchemy.orm import relationship
from enum import Enum

class CURRENCY_TYPE(Enum):
    usd = 'usd'
    eur = 'eur'

class Product(db.Model):

    __tablename__ = 'products'

    id            = db.Column(db.Integer,      primary_key=True)
    name          = db.Column(db.String(128),  nullable=False)
    info          = db.Column(db.Text,         nullable=True)
    price         = db.Column(db.Integer,      nullable=False)
    currency      = db.Column(db.Enum(CURRENCY_TYPE), default=CURRENCY_TYPE.usd, nullable=False)

    date_created  = db.Column(db.DateTime,     default=dt.datetime.utcnow())
    date_modified = db.Column(db.DateTime,     default=db.func.current_timestamp(),
                                               onupdate=db.func.current_timestamp())
    
    def __init__(self, **kwargs):
        super(Product, self).__init__(**kwargs)

    def __repr__(self):
        return f"{self.name} / ${self.price}"

    @classmethod
    def find_by_id(cls, _id: int) -> "Product":
        return cls.query.filter_by(id=_id).first() 

    def save(self) -> None:
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)

    def delete(self) -> None:
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)
        return


#__MODELS__
class User_System(db.Model):

    __tablename__ = 'User_System'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(255),  nullable=True)
    password_hash = db.Column(db.String(255),  nullable=True)
    email = db.Column(db.String(255),  nullable=True)
    is_admin = db.Column(db.Boolean, nullable=True)


    def __init__(self, **kwargs):
        super(User_System, self).__init__(**kwargs)


class Bussiness_Card(db.Model):

    __tablename__ = 'Bussiness_Card'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255),  nullable=True)
    title = db.Column(db.String(255),  nullable=True)
    phone_primary = db.Column(db.String(255),  nullable=True)
    phone_secondary = db.Column(db.String(255),  nullable=True)
    phone_trird = db.Column(db.String(255),  nullable=True)
    phone_fourth = db.Column(db.String(255),  nullable=True)
    email = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255),  nullable=True)
    location = db.Column(db.Text, nullable=True)
    photo_path = db.Column(db.String(255),  nullable=True)
    telegram = db.Column(db.String(255),  nullable=True)
    rus_max = db.Column(db.String(255),  nullable=True)
    wechat = db.Column(db.String(255),  nullable=True)
    instagram = db.Column(db.String(255),  nullable=True)
    whatsapp = db.Column(db.String(255),  nullable=True)
    twitter = db.Column(db.String(255),  nullable=True)
    snapchat = db.Column(db.String(255),  nullable=True)
    facebook = db.Column(db.String(255),  nullable=True)
    linkedin = db.Column(db.String(255),  nullable=True)
    youtube = db.Column(db.String(255),  nullable=True)
    tiktok = db.Column(db.String(255),  nullable=True)
    unique_id = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.String(255),  nullable=True)
    updated_at = db.Column(db.String(255),  nullable=True)
    web_style = db.Column(db.String(255),  nullable=True)
    pdf_syle = db.Column(db.String(255),  nullable=True)


    def __init__(self, **kwargs):
        super(Bussiness_Card, self).__init__(**kwargs)
