import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Page(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "pages"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(120), unique=True)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    last_modified_user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    categories = orm.relationship("Category",
                                  secondary="association", back_populates="pages")
    history_versions = orm.relationship("HistoryPage", back_populates='page')

    def __repr__(self):
        return self.title
