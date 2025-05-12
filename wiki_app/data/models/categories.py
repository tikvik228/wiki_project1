import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from wiki_app.data.db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin

association_table = sqlalchemy.Table(
    'association',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('pages', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('pages.id')),
    sqlalchemy.Column('categories', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('categories.id'))
)

history_association_table = sqlalchemy.Table(
    'history_association',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('history_pages', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('history_pages.id')),
    sqlalchemy.Column('categories', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('categories.id'))
)


class Category(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = "categories"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(120), unique=True)
    pages = orm.relationship("Page",
                                  secondary="association",
                                  back_populates='categories')
    history_pages = orm.relationship("HistoryPage",
                                  secondary="history_association",
                                  back_populates='categories')

    def __repr__(self):
        return self.name