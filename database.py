from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tailoring_management.db'
    app.config['SECRET_KEY'] = '8BYkEfBA3O6donzWlSihBXox7C0sKR6b'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    Bootstrap5(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app