import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from wiki_app.data.db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class HistoryPage(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "history_pages"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String(120))
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    is_rollback = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    categories = orm.relationship("Category",
                                  secondary="history_association", back_populates="history_pages")
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    page_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("pages.id"))
    page = orm.relationship('Page', back_populates='history_versions')
    user = orm.relationship('User', back_populates='edits')

    def __repr__(self):
        return self.title