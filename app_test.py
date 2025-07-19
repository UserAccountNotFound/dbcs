from flask import Flask, Response, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import qrcode
from io import BytesIO
import base64
import os
import json
from models.user import db, Admin, BusinessCard, Order
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Импортируем конфиг с перечнем месенджеров и социальных сетей
try:
    from csse import MESSAGE_n_SOCIAL_NETWORKS
except ImportError:
    # Fallback на случай если файл не найден
    MESSAGE_n_SOCIAL_NETWORKS = []
    print("Warning: social_config.py не найден, отсутствуют значения для точек входа Месенджеров и Соц.Сетей")

# Разрешенные расширения для аватарок
ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}

""""app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
"""

print("Database URL:", os.getenv('DATABASE_URL'))
print("Secret Key:", os.getenv('FLASK_SECRET_KEY'))

app = Flask(__name__)
# Определяем префикс для переменных среды
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex()) # случайный ключ - fallback, если не задан в .env
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     'business_cards.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'avatars')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Максимальный размер аватарок
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

nfc_data_store = {}

def allowed_file(file_obj_or_name):
    if isinstance(file_obj_or_name, str):
        # Если передано имя файла (строка)
        filename = file_obj_or_name
        if not filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in ALLOWED_PHOTO_EXTENSIONS
    else:
        # Если передан объект файла
        if not (file_obj_or_name and file_obj_or_name.filename):
            return False
        ext = file_obj_or_name.filename.rsplit('.', 1)[1].lower() if '.' in file_obj_or_name.filename else ''
        mime = getattr(file_obj_or_name, 'mimetype', '')
        return ext in ALLOWED_PHOTO_EXTENSIONS and mime in ALLOWED_MIME_TYPES


@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}


# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)

migrate = Migrate(app, db)


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin if none exists
    if not Admin.query.first():
        admin = Admin(username='admin', email='admin@example.com')
        admin.set_password('admin')  # Написать функцию генерации деволтового пароля!
        try:
            db.session.add(admin)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise

@app.route('/robots.txt') # инструкции для поисковых роботов
def robots():
    # Получаем настройки из .env
    is_production = os.getenv("FLASK_ENV") == "production"
    site_url = os.getenv("SITE_URL", "https://dbcs.example.local")  # fallback, если нет переменной
    
    # Правила для продакшена
    if is_production:
        rules = f"""
        User-agent: *
        Allow: /
        Disallow: /admin/
        Disallow: /card/
        Sitemap: {site_url}/sitemap.xml
        """
    # В разработке запрещаем индексацию
    else:
        rules = """
        User-agent: *
        Disallow: /
        """
    
    return Response(rules.strip(), mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    site_url = os.getenv("SITE_URL", "https://dbcs.example.local")  # fallback, если не задан
    
    # Генерация sitemap.xml
    # Основные URL сайта
    pages = [
        {"url": "", "lastmod": datetime.now(timezone.utc), "changefreq": "daily", "priority": "1.0"},
        {"url": "about", "lastmod": datetime.now(timezone.utc), "changefreq": "monthly", "priority": "0.8"},
        {"url": "contact", "lastmod": datetime.now(timezone.utc), "changefreq": "yearly", "priority": "0.5"},
    ]

    # Формируем XML
    sitemap_xml = render_template(
        'sitemap_template.xml',
        pages=pages,
        site_url=site_url  # Замените на ваш домен
    )
    
    return Response(sitemap_xml, mimetype='application/xml')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Admin.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Нет такого аккаунта. Проверьте логин или пароль')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():   
    cards = BusinessCard.query.order_by(BusinessCard.created_at.desc()).all()
    template_name = 'dashboard_admin.html' if current_user.is_admin else 'dashboard_user.html'
    return render_template(template_name, cards=cards)


@app.route('/create_card', methods=['GET', 'POST'])
def create_card():
    if request.method == 'POST':
        try:
            unique_id = base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8')

            social_data = {}
            for social in MESSAGE_n_SOCIAL_NETWORKS:
                key = social['key']
                value = request.form.get(key)
                if value:  # Сохраняем только если значение есть
                    social_data[key] = value

            # Handle photo upload
            photo = request.files.get('photo')
            photo_path = None
            if photo and photo.filename:
                if not allowed_file(photo):  # Проверяем объект файла
                    flash('Недопустимый тип файла. Разрешены только: ' + ', '.join(ALLOWED_PHOTO_EXTENSIONS))
                    return redirect(request.url)
                # Получаем расширение файла
                file_ext = photo.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{unique_id}.{file_ext}")
                photo_path = os.path.join('avatars', filename)
                
                try:
                    os.makedirs(os.path.join('static', 'avatars'), exist_ok=True)
                    photo.save(os.path.join('static', photo_path))
                except Exception as e:
                    app.logger.error(f"Ошибка сохранения файла: {str(e)}")
                    flash('Ошибка при сохранении файла', 'error')
                    return redirect(request.url)

            # Создаем карточку с динамическими полями
            card_data = {
                'name': request.form['name'],
                'title': request.form['title'],
                'phone_primary': request.form['phone_primary'],
                'phone_secondary': request.form.get('phone_secondary'),
                'phone_third': request.form.get('phone_third'),
                'phone_fourth': request.form.get('phone_fourth'),
                'email': request.form['email'],
                'address': request.form['address'],
                'location': request.form['location'],
                'photo_path': photo_path,
                'unique_id': unique_id,
                **social_data
            }
            
            # Create new user
            new_user = BusinessCard(**card_data)

            try:
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise
            
            # генерирууем QR code
            qr = qrcode.QRCode(version=1,
                             error_correction=qrcode.constants.ERROR_CORRECT_L, 
                             box_size=10, 
                             border=5)
            qr.add_data(f"{request.host_url}card/{unique_id}")
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Преобразуйте QR-код в base64 для отображения
            buffered = BytesIO()
            qr_img.save(buffered)
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()

            return jsonify({
                'success': True,
                'qr_code': qr_base64,
                'card_url': f"{request.host_url}card/{unique_id}"
            })

        except Exception as e:
            db.session.rollback()  # откат транзакции при ошибке
            app.logger.error(f"Error creating card: {str(e)}")  # Логирование ошибки
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

    # Фильтруем соцсети для JS
    js_mnsn_config = [s for s in MESSAGE_n_SOCIAL_NETWORKS if s['key']]
    
    # GET request - display the form
    return render_template('create_card.html', 
                         MESSAGE_n_SOCIAL_NETWORKS=MESSAGE_n_SOCIAL_NETWORKS,
                         mnsn_config=json.dumps(js_mnsn_config))


@app.route('/edit_card/<unique_id>', methods=['GET', 'POST'])
@login_required
def edit_card(unique_id):
    # Извлекаем существующую визитку или возвращаем 404 ошибку
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()

    if request.method == 'POST':
        try:
            # Обновляем основные поля
            card.name = request.form.get('name')
            card.title = request.form.get('title')
            card.email = request.form.get('email')
            card.phone_primary = request.form.get('phone_primary')
            card.phone_secondary = request.form.get('phone_secondary')
            card.phone_third = request.form.get('phone_third')
            card.phone_fourth = request.form.get('phone_fourth')
            card.address = request.form['address']

            # обновляем локацию
            new_location = request.form.get('location')
            if new_location:
                card.location = new_location
            # Если местоположение не указано и не существует, значение по умолчанию
            elif not card.location:
                card.location = "Location not specified"

            # обработчик изменений в полях соцсетей
            for social in MESSAGE_n_SOCIAL_NETWORKS:
                key = social['key']
                setattr(card, key, request.form.get(key))

            # обработчик изменений аватарок
#            if 'photo' in request.files:
#                photo = request.files['photo']
#                if photo and photo.filename and allowed_file(photo.filename):
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename:
                    if not allowed_file(photo):  # Проверяем объект файла
                        flash('Недопустимый тип файла', 'error')
                        return render_template('edit_card.html', card=card)
                    # Удаляем старую фотографию, если она есть
                    if card.photo_path:
                        old_photo_path = os.path.join('static', card.photo_path)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Получаем расширение файла
                    file_ext = photo.filename.rsplit('.', 1)[1].lower()
                    # Присваеваем новое имя файлу
                    filename = secure_filename(f"{unique_id}.{file_ext}")
                    photo_path = os.path.join('avatars', filename)
                    os.makedirs(os.path.join('static', 'avatars'), exist_ok=True)
                    photo.save(os.path.join('static', photo_path))
                    card.photo_path = photo_path

            # Обновляем время изменения визитки 
            card.updated_at = datetime.now(timezone.utc)

            # Запись изменений в БД
            try:    
                db.session.commit()
                flash('Визитная карточка успешно обновлена!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                raise
            
        except Exception as e:
            # Log the error for debugging
            print(e)
            app.logger.error(f"Error updating card: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the card. Please try again.', 'error')
            return render_template('edit_card.html', card=card)

    # Фильтруем соцсети для JS (исключаем основные)
    js_mnsn_config = [s for s in MESSAGE_n_SOCIAL_NETWORKS if s['key']]
    
    # GET request - display the form
    return render_template('edit_card.html', 
                           card=card,
                           MESSAGE_n_SOCIAL_NETWORKS=MESSAGE_n_SOCIAL_NETWORKS,
                           mnsn_config=json.dumps(js_mnsn_config)
                           )


@app.route('/delete_card/<unique_id>', methods=['POST'])
@login_required
def delete_card(unique_id):
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()

    # Удаляем аватарку если она была
    if card.photo_path:
        try:
            old_photo_path = os.path.join('static', card.photo_path)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)
        except Exception as e:
            app.logger.error(f"Error deleting photo: {str(e)}")

    try:
        db.session.delete(card)
        db.session.commit()
        flash('Визитная карточка удалена!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting card: {str(e)}")
        flash('Ошибка при удалении визитной карточки', 'error')
    return redirect(url_for('dashboard'))


@app.route('/form', methods=['GET', 'POST'])
def order_form():
    if request.method == 'POST':
        try:
            # Parse products array from JSON string
            products = json.loads(request.form.get('products[]', '[]'))

            # Create new order object
            new_order = Order(
                # Personal Information
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                business_type=request.form.get('business_type'),

                # Product Information
                products=products,
                purpose=request.form.get('purpose'),
                purpose_details=request.form.get('other_purpose') if request.form.get('purpose') == 'other' else None,

                # Emergency Contacts
                emergency_contact_1=request.form.get('emergency_contact_1'),
                emergency_contact_2=request.form.get('emergency_contact_2'),

                # Social Media Links
                social_media_1=request.form.get('social_media_1'),
                social_media_2=request.form.get('social_media_2'),
                social_media_3=request.form.get('social_media_3'),
                social_media_4=request.form.get('social_media_4'),

                # Feedback Information
                source=request.form.get('source'),
                source_details=request.form.get('source_details') if request.form.get('source') == 'other' else None
            )

            # Add and commit to database
            try:    
                db.session.add(new_order)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise

            return jsonify({
                'success': True,
                'message': 'Ваша форма успешно отправлена!'
            })

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Order form submission error: {str(e)}')
            return jsonify({
                'success': False,
                'error': 'Произошла ошибка \' при отправке формы.'
            }), 400

    return render_template('form.html')


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# Your existing card view route (no authentication required)
@app.route('/card/<unique_id>')
def view_card(unique_id):
    card = BusinessCard.query.filter_by(unique_id=unique_id).first_or_404()

    # Фильтруем соцсети для JS (исключаем основные)
    js_mnsn_config = [s for s in MESSAGE_n_SOCIAL_NETWORKS if s['key']]
    
    # Используем новый метод для получения социальных сетей
    social_links = card.get_social_links()
    
    # GET request - display the form
    return render_template('view_card.html', 
                           user=card,
                           social_links=social_links,
                           MESSAGE_n_SOCIAL_NETWORKS=MESSAGE_n_SOCIAL_NETWORKS,
                           mnsn_config=json.dumps(js_mnsn_config)
                           )


@app.route('/admin/orders')
@login_required
def admin_orders():
    status = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')

    # Base query
    query = Order.query

    # Apply status filter
    if status != 'all':
        query = query.filter(Order.status == status)

    # Apply sorting
    if sort_by == 'created_at':
        query = query.order_by(Order.created_at.desc() if order == 'desc' else Order.created_at.asc())
    elif sort_by == 'name':
        query = query.order_by(Order.name.desc() if order == 'desc' else Order.name.asc())
    elif sort_by == 'status':
        query = query.order_by(Order.status.desc() if order == 'desc' else Order.status.asc())

    # Execute query
    orders = query.all()

    return render_template('orders.html',
                           orders=orders,
                           current_status=status,
                           current_sort=sort_by,
                           current_order=order)


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'processing', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash('Статус успешно обновлен!', 'success')
    else:
        flash('Статус недействителен!', 'error')
    return redirect(url_for('admin_orders'))


@app.route('/admin/orders/<int:order_id>/details')
@login_required
def order_details(order_id):
    app.logger.info(f"Получен запрос: {order_id}")  # Debug log

    try:
        order = Order.query.get_or_404(order_id)

        # Debug prints
        print(f"Found order: {order}")
        print(f"Order attributes: {vars(order)}")

        response_data = {
            'id': order.id,
            'name': order.name,
            'email': order.email,
            'phone': order.phone,
            'business_type': order.business_type,
            'products': order.products,
            'purpose': order.purpose,
            'purpose_details': order.purpose_details,
            'emergency_contact_1': order.emergency_contact_1,
            'emergency_contact_2': order.emergency_contact_2,
            'social_media_1': order.social_media_1,
            'social_media_2': order.social_media_2,
            'social_media_3': order.social_media_3,
            'social_media_4': order.social_media_4,
            'source': order.source,
            'source_details': order.source_details,
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Error in order_details: {str(e)}")  # Debug print
        app.logger.error(f"Error in order_details: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/nfc/read')
@login_required
def nfc_read():
    return render_template('nfc_read.html')

@app.route('/nfc/write')
@login_required
def nfc_write():
    return render_template('nfc_write.html')

@app.route('/api/nfc', methods=['POST'])
@login_required
def handle_nfc_data():
    data = request.json
    nfc_id = data.get('id')
    nfc_content = data.get('content')
    
    if nfc_id:
        if request.method == 'POST':
            # Запись данных
            nfc_data_store[nfc_id] = nfc_content
            return jsonify({"status": "success", "message": "Data saved"})
        else:
            # Чтение данных (GET)
            content = nfc_data_store.get(nfc_id, "No data found")
            return jsonify({"status": "success", "content": content})
    
    return jsonify({"status": "error", "message": "Invalid NFC ID"})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
