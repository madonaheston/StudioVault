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
    is_public = db.Column(db.Boolean, default=False)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    gallery_id = db.Column(db.Integer, db.ForeignKey('gallery.id'), nullable=False)
    gallery = db.relationship('Gallery', backref=db.backref('images', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    image = db.relationship('Image', backref=db.backref('comments', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    image = db.relationship('Image', backref=db.backref('likes', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('likes', lazy=True))

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    photographer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photographer = db.relationship('User', foreign_keys=[photographer_id], backref=db.backref('ratings', lazy='dynamic'))
    client = db.relationship('User', foreign_keys=[client_id], backref=db.backref('given_ratings', lazy='dynamic'))

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

@app.route('/api/galleries/<int:gallery_id>', methods=['PUT'])
def update_gallery(gallery_id):
    data = request.get_json()
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['id']
        gallery = Gallery.query.filter_by(id=gallery_id, photographer_id=user_id).first()
        if not gallery:
            return jsonify({'message': 'Gallery not found'}), 404
        gallery.is_public = data.get('is_public', gallery.is_public)
        db.session.commit()
        return jsonify({'message': 'Gallery updated successfully'})
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
            gallery_data['is_public'] = gallery.is_public
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

@app.route('/api/public/galleries/<int:gallery_id>', methods=['GET'])
def get_public_gallery(gallery_id):
    gallery = Gallery.query.filter_by(id=gallery_id, is_public=True).first()
    if not gallery:
        return jsonify({'message': 'Gallery not found or not public'}), 404
    images = Image.query.filter_by(gallery_id=gallery.id).all()
    gallery_data = {'id': gallery.id, 'name': gallery.name, 'photographer_id': gallery.photographer_id}
    images_data = []
    for image in images:
        image_data = {}
        image_data['id'] = image.id
        image_data['filename'] = image.filename
        images_data.append(image_data)
    return jsonify({'gallery': gallery_data, 'images': images_data})

@app.route('/api/images/<int:image_id>/comments', methods=['POST'])
def add_comment(image_id):
    data = request.get_json()
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['id']
        new_comment = Comment(text=data['text'], image_id=image_id, user_id=user_id)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': 'Comment added successfully'})
    except:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/api/images/<int:image_id>/likes', methods=['POST'])
def add_like(image_id):
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['id']
        # Check if user already liked the image
        like = Like.query.filter_by(image_id=image_id, user_id=user_id).first()
        if like:
            return jsonify({'message': 'You already liked this image'}), 400
        new_like = Like(image_id=image_id, user_id=user_id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'message': 'Image liked successfully'})
    except:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/api/images/<int:image_id>/comments', methods=['GET'])
def get_comments(image_id):
    comments = Comment.query.filter_by(image_id=image_id).all()
    output = []
    for comment in comments:
        comment_data = {}
        comment_data['id'] = comment.id
        comment_data['text'] = comment.text
        comment_data['user'] = comment.user.username
        output.append(comment_data)
    return jsonify({'comments': output})

@app.route('/api/images/<int:image_id>/likes', methods=['GET'])
def get_likes(image_id):
    likes = Like.query.filter_by(image_id=image_id).all()
    return jsonify({'likes': len(likes)})

@app.route('/api/photographers/<int:photographer_id>/ratings', methods=['POST'])
def add_rating(photographer_id):
    data = request.get_json()
    token = request.headers.get('Authorization').split(' ')[1]
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        client_id = decoded_token['id']
        # Check if client has already rated this photographer
        rating = Rating.query.filter_by(photographer_id=photographer_id, client_id=client_id).first()
        if rating:
            return jsonify({'message': 'You have already rated this photographer'}), 400
        new_rating = Rating(value=data['value'], photographer_id=photographer_id, client_id=client_id)
        db.session.add(new_rating)
        db.session.commit()
        return jsonify({'message': 'Rating added successfully'})
    except:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
