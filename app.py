from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import sqlite3
import os
import sched
from datetime import datetime
import time
from threading import Thread, Event
import shutil
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'kay'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER_AVATARS = 'static/avatars'
UPLOAD_FOLDER_COVERS = 'static/covers'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Указываем папку для сохранения аватарок
app.config['UPLOAD_FOLDER_AVATARS'] = UPLOAD_FOLDER_AVATARS
# Указываем папку для сохранения обложек новостей
app.config['UPLOAD_FOLDER_COVERS'] = UPLOAD_FOLDER_COVERS


# Создание таблицы пользователей и новостей, если они не существуют
conn = sqlite3.connect('Database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT NOT NULL,
        avatar TEXT,
        is_admin INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS gamenews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT,
        ganre TEXT NOT NULL,
        opsi TEXT NOT NULL,
        processor TEXT NOT NULL,
        videocard TEXT NOT NULL,
        operativ TEXT NOT NULL,
        place_disk TEXT NOT NULL,
        directx TEXT NOT NULL,
        release TEXT NOT NULL,
        oficials TEXT NOT NULL,
        creators TEXT NOT NULL,
        platform TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS novanews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

conn.commit()  

# Запрос для добавления администратора
admin_username = 'admin'
admin_password = 'admin_password'
admin_email = 'admin@example.com'
hashed_password = generate_password_hash(admin_password)

# Проверка существования администратора
cursor.execute(
    'SELECT * FROM users WHERE username = ? AND is_admin = 1',
    (admin_username,)
)
admin_exists = cursor.fetchone()

# Вставка администратора, если его нет
if not admin_exists:
    cursor.execute(
        'INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)',
        (admin_username, hashed_password, admin_email, 1)
    )
    conn.commit()  
    print('Администратор успешно добавлен в базу данных.')
else:
    print('Администратор уже существует в базе данных.')

# Закрытие соединения с базой данных
conn.close()

def is_admin_by_username(username):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
    is_admin = cursor.fetchone()
    conn.close()
    print(f"Is admin for {username}: {is_admin}")  # Debug print
    return is_admin[0] == 1 if is_admin else False  # Изменяем возвращаемое значение на булево

class User(UserMixin):
    def __init__(self, user_id, username, avatar):
        self.id = user_id
        self.username = username
        self.avatar = avatar

    def is_authenticated(self):
        return True  # Все пользователи аутентифицированы

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user = User(user_data[0], user_data[1], user_data[4])
        user.is_admin = is_admin_by_username(user_data[1])  # Установка атрибута is_admin
        return user
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_avatar(avatar, username):
    try:
        if avatar:
            if allowed_file(avatar.filename):
                filename = secure_filename(avatar.filename)
                # Добавляем идентификатор пользователя к имени файла
                user_id = get_user_id_by_username(username)
                new_filename = f"{user_id}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER_AVATARS'], new_filename)
                avatar.save(filepath)
                return new_filename  # Возвращаем новое имя файла
            else:
                print("Invalid file format for avatar")
                flash('Недопустимый формат файла для аватара. Пожалуйста, используйте форматы PNG, JPG, JPEG или GIF.')
        else:
            print("Avatar not uploaded")
            return None
    except Exception as e:
        print(f"Error saving avatar: {e}")
        flash('Ошибка при загрузке аватара. Пожалуйста, повторите попытку.')

    return None

def get_user_id_by_username(username):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_id = cursor.fetchone()
    conn.close()
    return user_id[0] if user_id else None

@app.route('/')
def index():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news')
    news_items = cursor.fetchall()
    news_length = len(news_items)
    conn.close()

    app.logger.debug('News loaded from the database: %s', news_items)

    return render_template('index.html', news=news_items, news_length=news_length)

@app.route('/gamenews')
def gamenews():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gamenews')
    gamenews_items = cursor.fetchall()
    gamenews_length = len(gamenews_items)
    conn.close()

    app.logger.debug('News loaded from the database: %s', gamenews_items)

    return render_template('indexGAME.html', gamenews=gamenews_items, gamenews_length=gamenews_length)

@app.route('/gamenews/<int:gamenews_id>')
def view_gamenews(gamenews_id):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gamenews WHERE id = ?', (gamenews_id,))
    gamenews_item = cursor.fetchone()
    conn.close()

    if gamenews_item:
        return render_template('view_gamenews.html', gamenews_item=gamenews_item)
    else:
        abort(404)

@app.route('/novanews')
def novanews():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM novanews')
    novanews_items = cursor.fetchall()
    novanews_length = len(novanews_items)
    conn.close()

    app.logger.debug('News loaded from the database: %s', novanews_items)

    return render_template('indexNEWS.html', novanews=novanews_items, novanews_length=novanews_length)

@app.route('/novanews/<int:novanews_id>')
def view_novanews(novanews_id):
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM novanews WHERE id = ?', (novanews_id,))
    novanews_item = cursor.fetchone()
    conn.close()

    if novanews_item:
        return render_template('view_novanews.html', novanews_item=novanews_item)
    else:
        abort(404) 
                 

@app.route('/register', methods=['GET', 'POST'])
def register():
    avatar = None
    if request.method == 'POST':
        print("POST request received for registration")
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        avatar = request.files['avatar'] if 'avatar' in request.files else None

        if not username or not password or not email:
            print("Invalid input: Please enter username, password, and email")
            return render_template('register.html', error='Пожалуйста, введите имя пользователя, пароль и email.', avatar=avatar)

        if len(password) < 6 or len(password) > 20:
            print("Invalid password length: Password should be between 6 and 20 characters")
            return render_template('register.html', error='Пароль должен быть от 6 до 20 символов.', avatar=avatar)

        if not avatar:
            print("Avatar not uploaded")
            # Return success message instead of error, as registration can proceed without avatar
            flash('Аватар не загружен. Регистрация будет завершена без аватара.')

        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            print("Username already exists")
            conn.close()
            return render_template('register.html', error='Пользователь с таким именем уже существует.', avatar=avatar)

        # Check if the email already exists
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_by_email = cursor.fetchone()
        if user_by_email:
            print("Email already registered")
            conn.close()
            return render_template('register.html', error='Пользователь с таким email уже зарегистрирован.', avatar=avatar)

        # Save avatar if provided
        new_avatar_filename = save_avatar(avatar, username)
        if new_avatar_filename or not avatar:  # Proceed with registration even if avatar is not uploaded
            print("Registration successful")
            cursor.execute(
                'INSERT INTO users (username, password, email, avatar) VALUES (?, ?, ?, ?)',
                (username, generate_password_hash(password), email, new_avatar_filename)
            )
            conn.commit()
            conn.close()
            flash('Регистрация успешна. Теперь вы можете войти.')
            return redirect(url_for('login'))

    print("Rendering registration template")
    return render_template('register.html', avatar=avatar)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Пожалуйста, введите имя пользователя и пароль.')
            return render_template('login.html')

        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            user_obj = User(user[0], user[1], user[4])
            user_obj.is_admin = is_admin_by_username(username)  # Установка флага администратора
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные имя пользователя или пароль.')

    return render_template('login.html')

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' in request.files:
        avatar = request.files['avatar']  
        if avatar.filename != '':
            new_avatar_filename = save_avatar(avatar, current_user.username)  
            if new_avatar_filename:
                conn = sqlite3.connect('Database.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (new_avatar_filename, current_user.id))
                conn.commit()
                conn.close()
                flash('Аватар успешно обновлен.')
            else:
                flash('Ошибка при загрузке аватара. Пожалуйста, повторите попытку.')
        else:
            flash('Не выбран файл для загрузки.')
    else:
        flash('Файл аватара не найден.')

    return redirect(url_for('dashboard'))

@app.route('/admin_panel')
@login_required
def admin_panel():
    if current_user.is_admin:
        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.execute('SELECT * FROM news')
        news = cursor.fetchall()
        cursor.execute('SELECT * FROM gamenews')
        gamenews = cursor.fetchall()
        cursor.execute('SELECT * FROM novanews')
        novanews = cursor.fetchall()
        conn.close()

        return render_template('admin_panel.html', users=users, news=news, gamenews=gamenews, novanews=novanews)
    else:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        # Получаем новый пароль из формы, если он был введен
        new_password = request.form['password'] if 'password' in request.form else None
        # Устанавливаем флаг is_admin
        is_admin = 1 if request.form.get('is_admin') == 'on' else 0

        # Обновляем запись пользователя в базе данных
        if new_password:
            hashed_password = generate_password_hash(new_password)
            cursor.execute('UPDATE users SET username = ?, email = ?, password = ?, is_admin = ? WHERE id = ?', (new_username, new_email, hashed_password, is_admin, user_id))
        else:
            cursor.execute('UPDATE users SET username = ?, email = ?, is_admin = ? WHERE id = ?', (new_username, new_email, is_admin, user_id))
        conn.commit()
        conn.close()
        flash('Пользователь успешно отредактирован.')
        return redirect(url_for('admin_panel'))

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return render_template('edit_user.html', user=user)
    else:
        flash('Пользователь не найден.')
        return redirect(url_for('admin_panel'))

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_admin = 1 if request.form.get('is_admin') == 'on' else 0

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)', (username, hashed_password, email, is_admin))
        conn.commit()
        conn.close()
        flash('Новый пользователь успешно добавлен.')
        return redirect(url_for('admin_panel'))

    return render_template('add_user.html')

@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Проверяем, был ли загружен файл
        if 'image_url' in request.files:
            # Получаем файл обложки новости
            image_file = request.files['image_url']
            # Сохраняем файл на сервере
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER_COVERS'], image_filename))
            image_url = secure_filename(image_file.filename)
        else:
            image_url = None  # Если файл не загружен, присваиваем None

        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO news (title, content, image_url, user_id) VALUES (?, ?, ?, ?)',
                       (title, content, image_url, current_user.id))  
        conn.commit()
        conn.close()
        flash('Новость успешно добавлена.')
        return redirect(url_for('admin_panel'))

    return render_template('add_news.html')

@app.route('/edit_news/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        if 'image_url' in request.files:  # Изменено с 'image' на 'image_url'
            new_image = request.files['image_url']
            if new_image.filename != '':
                # Сохраняем файл на сервере
                filename = secure_filename(new_image.filename)
                new_image.save(os.path.join(app.config['UPLOAD_FOLDER_COVERS'], filename))
                image_url = filename
            else:
                image_url = None  # Если файл не загружен, присваиваем None
        else:
            image_url = None
        cursor.execute('UPDATE news SET title = ?, content = ?, image_url = ? WHERE id = ?', (new_title, new_content, image_url, news_id))  # Исправлено new_image на image_url
        conn.commit()  # Сохраняем изменения в базе данных
        conn.close()
        flash('Новость успешно отредактирована.')
        return redirect(url_for('admin_panel'))
    cursor.execute('SELECT * FROM news WHERE id = ?', (news_id,))
    news = cursor.fetchone()
    conn.close()
    if news:
        return render_template('edit_news.html', news=news)
    else:
        flash('Новость не найдена.')
        return redirect(url_for('admin_panel'))

@app.route('/add_gamenews', methods=['GET', 'POST'])
@login_required
def add_gamenews():
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        ganre = request.form['ganre']
        opsi = request.form['opsi']
        processor= request.form['processor']
        videocard = request.form['videocard']
        operativ = request.form['operativ']
        place_disk = request.form['place_disk']
        directx = request.form['directx']
        release = request.form['release']
        oficials = request.form['oficials']
        creators = request.form['creators']
        platform = request.form['platform']

        
        # Проверяем, был ли загружен файл
        if 'image_url' in request.files:
            # Получаем файл обложки новости
            image_file = request.files['image_url']
            # Сохраняем файл на сервере
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER_COVERS'], image_filename))
            image_url = secure_filename(image_file.filename)
        else:
            image_url = None  # Если файл не загружен, присваиваем None

        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO gamenews (title, content, image_url, ganre, opsi, processor, videocard, operativ, place_disk, directx, release, oficials, creators, platform, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
               (title, content, image_url, ganre, opsi, processor, videocard, operativ, place_disk, directx, release, oficials, creators, platform, current_user.id))
        conn.commit()
        conn.close()
        flash('Игра успешно добавлена.')
        return redirect(url_for('admin_panel'))

    return render_template('add_gamenews.html')

@app.route('/edit_gamenews/<int:gamenews_id>', methods=['GET', 'POST'])
@login_required
def edit_gamenews(gamenews_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        if 'image_url' in request.files:  # Изменено с 'image' на 'image_url'
            new_image = request.files['image_url']
            if new_image.filename != '':
                # Сохраняем файл на сервере
                filename = secure_filename(new_image.filename)
                new_image.save(os.path.join(app.config['UPLOAD_FOLDER_COVERS'], filename))
                image_url = filename
            else:
                image_url = None  # Если файл не загружен, присваиваем None
        else:
            image_url = None
        cursor.execute('UPDATE gamenews SET title = ?, content = ?, image_url = ? WHERE id = ?', (new_title, new_content, image_url, gamenews_id))  # Исправлено new_image на image_url
        conn.commit()  # Сохраняем изменения в базе данных
        conn.close()
        flash('Новость успешно отредактирована.')
        return redirect(url_for('admin_panel'))
    cursor.execute('SELECT * FROM gamenews WHERE id = ?', (gamenews_id,))
    gamenews = cursor.fetchone()
    conn.close()
    if gamenews:
        return render_template('edit_gamenews.html', gamenews=gamenews)
    else:
        flash('Новость не найдена.')
        return redirect(url_for('admin_panel'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('admin_panel'))

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('Пользователь успешно удален.')
    return redirect(url_for('admin_panel'))

@app.route('/delete_news/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('admin_panel'))

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()
    flash('Новость успешно удалена.')
    return redirect(url_for('admin_panel'))

@app.route('/delete_gamenews/<int:gamenews_id>', methods=['POST'])
@login_required
def delete_gamenews(gamenews_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('admin_panel'))

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gamenews WHERE id = ?', (gamenews_id,))
    conn.commit()
    conn.close()
    flash('Новость успешно удалена.')
    return redirect(url_for('admin_panel'))

@app.route('/add_novanews', methods=['GET', 'POST'])
@login_required
def add_novanews():
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Проверяем, был ли загружен файл
        if 'image_url' in request.files:
            # Получаем файл обложки новости
            image_file = request.files['image_url']
            # Сохраняем файл на сервере
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER_COVERS'], image_filename))
            image_url = secure_filename(image_file.filename)
        else:
            image_url = None  # Если файл не загружен, присваиваем None

        conn = sqlite3.connect('Database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO novanews (title, content, image_url, user_id) VALUES (?, ?, ?, ?)',
                       (title, content, image_url, current_user.id))  
        conn.commit()
        conn.close()
        flash('Игра успешно добавлена.')
        return redirect(url_for('admin_panel'))

    return render_template('add_novanews.html')

@app.route('/edit_novanews/<int:novanews_id>', methods=['GET', 'POST'])
@login_required
def edit_novanews(novanews_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('index'))
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        if 'image_url' in request.files:  # Изменено с 'image' на 'image_url'
            new_image = request.files['image_url']
            if new_image.filename != '':
                # Сохраняем файл на сервере
                filename = secure_filename(new_image.filename)
                new_image.save(os.path.join(app.config['UPLOAD_FOLDER_COVERS'], filename))
                image_url = filename
            else:
                image_url = None  # Если файл не загружен, присваиваем None
        else:
            image_url = None
        cursor.execute('UPDATE novanews SET title = ?, content = ?, image_url = ? WHERE id = ?', (new_title, new_content, image_url, novanews_id))  # Исправлено new_image на image_url
        conn.commit()  # Сохраняем изменения в базе данных
        conn.close()
        flash('Новинка успешно отредактирована.')
        return redirect(url_for('admin_panel'))
    cursor.execute('SELECT * FROM novanews WHERE id = ?', (novanews_id,))
    novanews = cursor.fetchone()
    conn.close()
    if novanews:
        return render_template('edit_novanews.html', novanews=novanews)
    else:
        flash('Новинка не найдена.')
        return redirect(url_for('admin_panel'))
    
@app.route('/delete_novanews/<int:novanews_id>', methods=['POST'])
@login_required
def delete_novanews(novanews_id):
    if not current_user.is_admin:
        flash('Доступ к админ-панели разрешен только администраторам.')
        return redirect(url_for('admin_panel'))

    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM novanews WHERE id = ?', (novanews_id,))
    conn.commit()
    conn.close()
    flash('Новость успешно удалена.')
    return redirect(url_for('admin_panel'))

@app.route('/dashboard')
@login_required
def dashboard():
        return render_template('dashboard.html')

@app.route('/contact')
@login_required
def contact():
        return render_template('contact.html')

@app.route('/feedback')
@login_required
def feedback():
        return render_template('feedback.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


scheduler = sched.scheduler(time.time, time.sleep)

def startserver(stop_event):
    app.run(debug=True, use_reloader=False)

def backup_database(source_path, backup_dir, stop_event):
    while not stop_event.is_set():
        timestamp = datetime.now().strftime('%Y-%m-%d%H-%M-%S')
        backup_filename = f"backup{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy(source_path, backup_path)
        print(f"Резервная копия создана: {backup_filename}")
        time.sleep(21600)  # Повторяем каждые 6 часов

def start_scheduler(stop_event):
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, backup_database, (source_path, backup_dir, stop_event))
    scheduler.run()

if __name__ == '__main__':
    source_path = os.path.join(app.root_path, 'Database.db')
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    stop_event = Event()

    scheduler_thread = Thread(target=start_scheduler, args=(stop_event,), daemon=True)
    scheduler_thread.start()

    try:
        startserver(stop_event)
    except KeyboardInterrupt:
        print("Stopping server and scheduler...")
        stop_event.set()
        scheduler_thread.join()




@app.route('/gamenews', methods=['GET', 'POST'])
def search_gamenews():
    if request.method == 'POST':
        search_term = request.form['search_term']
        conn = sqlite3.connect('Database.db')  # Подключение к базе данных
        cursor = conn.cursor()
        
        # SQL-запрос с учетом поискового запроса 
        cursor.execute("SELECT * FROM gamenews WHERE title LIKE ? OR content LIKE ?", ('%'+search_term+'%', '%'+search_term+'%'))
        results = cursor.fetchall()
        conn.close()  # Закрытие соединения

        return render_template('indexGAME.html', results=results)  # Передача результатов в шаблон 
    else:
        return render_template('indexGAME.html') 

if __name__ == '__main__':
    app.run(debug=True)

