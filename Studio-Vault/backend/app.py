from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studio_vault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_photographer = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    photographer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photographer = db.relationship('User', backref=db.backref('galleries', lazy=True))

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    gallery_id = db.Column(db.Integer, db.ForeignKey('gallery.id'), nullable=False)
    gallery = db.relationship('Gallery', backref=db.backref('images', lazy=True))

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password, is_photographer=data.get('is_photographer', False))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'New user created!'})

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return jsonify({'message': 'Could not verify'}), 401

    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})

    return jsonify({'message': 'Could not verify'}), 401

@app.route('/api/galleries', methods=['POST'])
def create_gallery():
    data = request.get_json()
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['id']
        new_gallery = Gallery(name=data['name'], photographer_id=user_id)
        db.session.add(new_gallery)
        db.session.commit()
        return jsonify({'message': 'New gallery created!'})
    except:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/api/galleries', methods=['GET'])
def get_galleries():
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['id']
        galleries = Gallery.query.filter_by(photographer_id=user_id).all()
        output = []
        for gallery in galleries:
            gallery_data = {}
            gallery_data['id'] = gallery.id
            gallery_data['name'] = gallery.name
            output.append(gallery_data)
        return jsonify({'galleries': output})
    except:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/api/galleries/<int:gallery_id>/upload', methods=['POST'])
def upload_image(gallery_id):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_image = Image(filename=filename, gallery_id=gallery_id)
        db.session.add(new_image)
        db.session.commit()
        return jsonify({'message': 'File uploaded successfully'})

@app.route('/api/galleries/<int:gallery_id>/images', methods=['GET'])
def get_images(gallery_id):
    images = Image.query.filter_by(gallery_id=gallery_id).all()
    output = []
    for image in images:
        image_data = {}
        image_data['id'] = image.id
        image_data['filename'] = image.filename
        output.append(image_data)
    return jsonify({'images': output})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
