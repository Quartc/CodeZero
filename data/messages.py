import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    sender_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    receiver_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    is_read = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    sender = sqlalchemy.orm.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = sqlalchemy.orm.relationship("User", foreign_keys=[receiver_id], backref="received_messages")