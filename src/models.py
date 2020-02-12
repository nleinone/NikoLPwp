from flask import Flask, Blueprint, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api

from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError


app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///development.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    genre = db.Column(db.String(128), nullable=False)
    #release_year = db.Column(db.Integer, unique=True)
    
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

def example_movie():
    m = Movie(
        name="Rambo5",
        genre="action"
    )
    
    try:
        db.session.add(m)
        db.session.commit()
    except IntegrityError as e:
        print("Test movie already created. Continuing operation")
        db.session.rollback()
    
#Create sample movie for the user:
db.create_all()
example_movie()



