import os
import uuid
import requests
from flask import Flask, render_template, redirect, request, make_response, flash, url_for
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.utils import secure_filename
from data import db_session
from data.users import User
from data.posts import Post
from data.messages import Message
from data.comments import Comment
from data.likes import Like
from forms.user import RegisterForm, LoginForm, EditProfileForm
from forms.post import PostForm
from forms.comment import CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_gram_secret_key_2024'
app.config['UPLOAD_FOLDER_AVATARS'] = 'static/uploads/avatars'
app.config['UPLOAD_FOLDER_POSTS'] = 'static/uploads/post_images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER_AVATARS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_POSTS'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def get_unread_count():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        count = db_sess.query(Message).filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()
        db_sess.close()
        return count
    return 0


def save_file(file, folder, old_file=None):
    if not file or not file.filename:
        return old_file
    if old_file and old_file != 'default.jpg':
        old_path = os.path.join(folder, old_file)
        if os.path.exists(old_path):
            os.remove(old_path)
    ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(folder, new_filename))
    return new_filename


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/')
def index():
    db_sess = db_session.create_session()
    posts = db_sess.query(Post).order_by(Post.created_date.desc()).all()
    posts_data = []
    for post in posts:
        user = db_sess.get(User, post.user_id)
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_date': post.created_date,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'user_id': post.user_id,
            'user_name': user.name if user else 'Unknown',
            'user_avatar': user.avatar if user else None,
            'image': post.image
        })
    db_sess.close()
    return render_template(
        'index.html', title='Лента',
        posts=posts_data, unread_count=get_unread_count()
    )


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    db_sess = db_session.create_session()
    post = db_sess.get(Post, post_id)
    if not post:
        flash('Пост не найден', 'danger')
        return redirect('/')
    user = db_sess.get(User, post.user_id)
    comments = db_sess.query(Comment).filter(Comment.post_id == post_id).all()
    comments_data = []
    for comment in comments:
        comment_user = db_sess.get(User, comment.user_id)
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'created_date': comment.created_date,
            'user_name': comment_user.name if comment_user else 'Unknown',
            'user_avatar': comment_user.avatar if comment_user else None
        })
    form = CommentForm()
    post_data = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'created_date': post.created_date,
        'likes_count': post.likes_count,
        'comments_count': post.comments_count,
        'user_id': post.user_id,
        'user_name': user.name if user else 'Unknown',
        'user_avatar': user.avatar if user else None,
        'image': post.image
    }
    db_sess.close()
    return render_template(
        'post_detail.html', title=post.title, post=post_data,
        comments=comments_data, form=form, unread_count=get_unread_count()
    )


@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        comment = Comment(
            text=form.text.data,
            user_id=current_user.id,
            post_id=post_id
        )
        db_sess.add(comment)
        post = db_sess.get(Post, post_id)
        if post:
            post.comments_count += 1
        db_sess.commit()
        db_sess.close()
        flash('Комментарий добавлен!', 'success')
    return redirect(f'/post/{post_id}')


@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    db_sess = db_session.create_session()
    existing_like = db_sess.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id
    ).first()
    post = db_sess.get(Post, post_id)
    if existing_like:
        db_sess.delete(existing_like)
        if post:
            post.likes_count -= 1
        flash('Лайк убран', 'info')
    else:
        like = Like(user_id=current_user.id, post_id=post_id)
        db_sess.add(like)
        if post:
            post.likes_count += 1
        flash('Лайк поставлен!', 'success')
    db_sess.commit()
    db_sess.close()
    return redirect(request.referrer or '/')


@app.route('/delete_post/<int:post_id>')
@login_required
def delete_post(post_id):
    db_sess = db_session.create_session()
    post = db_sess.get(Post, post_id)
    if post and post.user_id == current_user.id:
        if post.image:
            image_path = os.path.join(app.config['UPLOAD_FOLDER_POSTS'], post.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        db_sess.query(Comment).filter(Comment.post_id == post_id).delete()
        db_sess.query(Like).filter(Like.post_id == post_id).delete()
        db_sess.delete(post)
        db_sess.commit()
        flash('Пост удалён', 'success')
    else:
        flash('Нет прав для удаления', 'danger')
    db_sess.close()
    return redirect('/')


@app.route('/profile/<int:user_id>')
def profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect('/')
    posts = db_sess.query(Post).filter(Post.user_id == user_id).order_by(
        Post.created_date.desc()
    ).all()
    user_data = {
        'id': user.id,
        'name': user.name,
        'about': user.about,
        'city': user.city,
        'created_date': user.created_date,
        'avatar': user.avatar
    }
    posts_data = []
    for post in posts:
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'image': post.image
        })
    db_sess.close()
    return render_template(
        'profile.html', title=f'Профиль {user.name}',
        user=user_data, posts=posts_data, unread_count=get_unread_count()
    )


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    if request.method == 'GET':
        form.name.data = user.name
        form.about.data = user.about
        form.city.data = user.city
    if form.validate_on_submit():
        geocoder_key = "8013b162-6b42-4997-9691-77b7074026e0"
        geocode_url = "http://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": geocoder_key,
            "geocode": form.city.data,
            "format": "json"
        }
        response = requests.get(geocode_url, params=params)
        lon, lat = "37.618423", "55.751244"
        if response:
            json_resp = response.json()
            try:
                pos = json_resp["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
                lon, lat = pos.split()
            except:
                pass
        user.name = form.name.data
        user.about = form.about.data
        user.city = form.city.data
        user.lon = lon
        user.lat = lat

        if form.avatar.data:
            avatar = save_file(
                form.avatar.data,
                app.config['UPLOAD_FOLDER_AVATARS'],
                user.avatar
            )
            if avatar:
                user.avatar = avatar

        db_sess.commit()
        db_sess.close()
        flash('Профиль обновлён!', 'success')
        return redirect(f'/profile/{current_user.id}')
    db_sess.close()
    return render_template(
        'edit_profile.html', title='Редактирование',
        form=form, unread_count=get_unread_count()
    )


@app.route('/delete_avatar')
@login_required
def delete_avatar():
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    if user.avatar and user.avatar != 'default.jpg':
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER_AVATARS'], user.avatar)
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        user.avatar = 'default.jpg'
        db_sess.commit()
        flash('Аватарка удалена', 'success')
    db_sess.close()
    return redirect('/edit_profile')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            flash('Пароли не совпадают!', 'danger')
            return render_template('register.html', title='Регистрация', form=form)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash('Такой пользователь уже есть!', 'danger')
            db_sess.close()
            return render_template('register.html', title='Регистрация', form=form)

        geocoder_key = "8013b162-6b42-4997-9691-77b7074026e0"
        geocode_url = "http://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": geocoder_key,
            "geocode": form.city.data,
            "format": "json"
        }
        response = requests.get(geocode_url, params=params)
        lon, lat = "37.618423", "55.751244"
        if response:
            json_resp = response.json()
            try:
                pos = json_resp["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
                lon, lat = pos.split()
            except:
                pass

        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            city=form.city.data,
            lon=lon,
            lat=lat
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            resp = make_response(redirect("/"))
            resp.set_cookie('last_visitor', user.name, max_age=60*60*24*7)
            flash(f'С возвращением, {user.name}!', 'success')
            db_sess.close()
            return resp
        db_sess.close()
        flash('Неправильный логин или пароль', 'danger')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect("/")


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        image_filename = None
        if form.image.data:
            image_filename = save_file(
                form.image.data,
                app.config['UPLOAD_FOLDER_POSTS']
            )
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            image=image_filename
        )
        db_sess.add(post)
        db_sess.commit()
        db_sess.close()
        flash('Пост опубликован!', 'success')
        return redirect('/')
    return render_template(
        'add_post.html', title='Новый пост',
        form=form, unread_count=get_unread_count()
    )


@app.route('/map')
@login_required
def show_map():
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id != current_user.id).all()

    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'name': user.name,
            'city': user.city,
            'lon': user.lon,
            'lat': user.lat
        })

    points = []
    for user in users_data:
        points.append(f"{user['lon']},{user['lat']},pm2blm")
    points.append(f"{current_user.lon},{current_user.lat},pm2rdl")

    pt_str = "~".join(points)
    map_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
    map_url = f"https://static-maps.yandex.ru/v1?ll=60,60&spn=40,30&apikey={map_key}&pt={pt_str}"
    db_sess.close()
    return render_template(
        'map.html', title='Карта',
        map_url=map_url, users=users_data, unread_count=get_unread_count()
    )


@app.route('/messages')
@login_required
def messages_list():
    db_sess = db_session.create_session()
    sent_to = db_sess.query(Message.receiver_id).filter(
        Message.sender_id == current_user.id
    ).distinct()
    received_from = db_sess.query(Message.sender_id).filter(
        Message.receiver_id == current_user.id
    ).distinct()
    all_ids = set()
    for uid in sent_to:
        all_ids.add(uid[0])
    for uid in received_from:
        all_ids.add(uid[0])

    dialogs = []
    for uid in all_ids:
        user = db_sess.get(User, uid)
        if user:
            unread = db_sess.query(Message).filter(
                Message.sender_id == uid,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            dialogs.append({
                'id': user.id,
                'name': user.name,
                'about': user.about,
                'unread': unread
            })
    all_users = db_sess.query(User).filter(User.id != current_user.id).all()
    all_users_data = []
    for user in all_users:
        all_users_data.append({
            'id': user.id,
            'name': user.name,
            'about': user.about
        })
    db_sess.close()
    return render_template(
        'messages.html', title='Сообщения',
        dialogs=dialogs, all_users=all_users_data, unread_count=get_unread_count()
    )


@app.route('/chat/<int:companion_id>', methods=['GET', 'POST'])
@login_required
def chat(companion_id):
    db_sess = db_session.create_session()
    companion = db_sess.get(User, companion_id)
    if not companion:
        flash('Пользователь не найден', 'danger')
        return redirect('/messages')

    companion_data = {
        'id': companion.id,
        'name': companion.name,
        'about': companion.about
    }

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        if text:
            msg = Message(
                text=text,
                sender_id=current_user.id,
                receiver_id=companion_id,
                is_read=False
            )
            db_sess.add(msg)
            db_sess.commit()
            flash('Сообщение отправлено!', 'success')
            db_sess.close()
            return redirect(f'/chat/{companion_id}')

    messages = db_sess.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == companion_id)) |
        ((Message.sender_id == companion_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_date).all()

    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'text': msg.text,
            'created_date': msg.created_date,
            'sender_id': msg.sender_id,
            'receiver_id': msg.receiver_id
        })

    db_sess.query(Message).filter(
        Message.sender_id == companion_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({Message.is_read: True})
    db_sess.commit()
    db_sess.close()

    return render_template(
        'chat.html', title=f'Чат с {companion_data["name"]}',
        companion=companion_data, messages=messages_data, unread_count=get_unread_count()
    )


if __name__ == '__main__':
    db_session.global_init("db/gram.db")
    app.run(port=8080, host='127.0.0.1', debug=True)