import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from wiki_app.data.db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "users"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String(60), unique=True)
    email = sqlalchemy.Column(sqlalchemy.String(120),  unique=True, nullable=True)
    image_file = sqlalchemy.Column(sqlalchemy.String(120))
    about = sqlalchemy.Column(sqlalchemy.String(300), nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    role = sqlalchemy.Column(sqlalchemy.String, default='user')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    edits = orm.relationship("HistoryPage", back_populates='user')
    files = orm.relationship("Uploads", back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return self.username
