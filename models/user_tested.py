# models/user.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class BusinessCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    # Multiple phone numbers
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    phone_third = db.Column(db.String(20))
    phone_fourth = db.Column(db.String(20))
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    location = db.Column(db.String(200), nullable=False)
    photo_path = db.Column(db.String(200))

    unique_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Динамическая генерация полей в БД на основе данных из csse.py
    def __init__(self, **kwargs):
        # создаем поля для месенджеров и соцсетей что нашли 
        from csse import MESSAGE_n_SOCIAL_NETWORKS
        for social in MESSAGE_n_SOCIAL_NETWORKS:
            key = social['key']
            setattr(self.__class__, key, db.Column(db.String(200)))
            setattr(self, key, kwargs.pop(key, None))
        
        # Initialize remaining fields
        super().__init__(**kwargs)
    
    @classmethod
    def get_social_media_fields(cls):
        """ Возвращает список названий полей социальных сетей на основе csse.py """
        from csse import MESSAGE_n_SOCIAL_NETWORKS
        return [social['key'] for social in MESSAGE_n_SOCIAL_NETWORKS]

    def get_social_links(self):
        """Возвращает список ссылок на социальные сети с их метаданными на основе csse.py"""
        from csse import MESSAGE_n_SOCIAL_NETWORKS
        social_data = {}
        for social in MESSAGE_n_SOCIAL_NETWORKS:
            key = social['key']
            value = getattr(self, key)
            if value:
                social_data[key] = {
                    'value': value,
                    'icon': social['icon'],
                    'url': social['url'],
                    'class': social['class'],
                    'label': social['label']
                }
        return social_data


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Personal Information
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    business_type = db.Column(db.String(20), nullable=False)  # 'business' or 'individual'

    # Product Information
    products = db.Column(db.JSON, nullable=False)  # Store as JSON array
    purpose = db.Column(db.String(100), nullable=False)
    purpose_details = db.Column(db.Text)  # For additional details

    # Emergency Contacts
    emergency_contact_1 = db.Column(db.String(20), nullable=False)
    emergency_contact_2 = db.Column(db.String(20))  # Optional

    # Social Media Links
    social_media_1 = db.Column(db.String(200))
    social_media_2 = db.Column(db.String(200))
    social_media_3 = db.Column(db.String(200))
    social_media_4 = db.Column(db.String(200))

    # Обратная связь
    source = db.Column(db.String(50), nullable=False)  # Как узнали о нас
    source_details = db.Column(db.Text)  # Дополнительные сведения об источнике

    # Статусы
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Order {self.id} by {self.name}>'