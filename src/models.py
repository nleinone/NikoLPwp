from flask_sqlalchemy import SQLAlchemy
import app
from app import app
"""
REFERENCES:
Course lecture materials were used as a guideance of this project. The MasonBuilder in entirety was downloaded  from the excercise pages.
"""

db = SQLAlchemy(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///development.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

'''MODELS'''  

class Uploader(db.Model):
    """Database model for movie uploader"""
    id = db.Column(db.Integer, primary_key=True)
    uploader_name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    
    movies = db.relationship('Movie', backref='uploader')
    
    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["uploader_name", "email"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "uploaders's unique name",
            "type": "string"
        }
        props["email"] = {
            "description": "email address of the uploader",
            "type": "string"
        }
        return schema

class Movie(db.Model):
    """Database model for movie item"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    genre = db.Column(db.String(128), nullable=False)
    
    uploader_id = db.Column(db.Integer, db.ForeignKey('uploader.id'))
    
    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name", "genre"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Movie's unique name",
            "type": "string"
        }
        props["genre"] = {
            "description": "Genre of the movie",
            "type": "string"
        }

        return schema
        
db.create_all()
