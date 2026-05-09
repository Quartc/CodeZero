import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    likes_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    comments_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    user = sqlalchemy.orm.relationship("User", backref="posts")