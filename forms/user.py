from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    city = StringField("Город (для карты)", default="Москва")
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class EditProfileForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("О себе")
    city = StringField("Город")
    avatar = FileField('Аватарка', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только картинки!')])
    submit = SubmitField('Сохранить изменения')