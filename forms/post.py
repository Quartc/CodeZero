from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class PostForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Текст поста", validators=[DataRequired()])
    image = FileField('Картинка к посту', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только картинки!')])
    submit = SubmitField('Опубликовать')