import sqlalchemy
from .db_session import SqlAlchemyBase


class Like(SqlAlchemyBase):
    __tablename__ = 'likes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    post_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("posts.id"))

    user = sqlalchemy.orm.relationship("User", backref="likes")
    post = sqlalchemy.orm.relationship("Post", backref="likes")