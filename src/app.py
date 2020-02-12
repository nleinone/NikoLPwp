from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

#from models import Movie
#from resources import MovieCollection, MovieItem, MovieBuilder
import utils
from mason import MasonBuilder

from flask_restful import Resource, Api
from flask import Flask, Blueprint, Response, request
from flask_sqlalchemy import SQLAlchemy

from jsonschema import validate, ValidationError
import json

#api_bp = Blueprint("api", __name__, url_prefix="/api")
#api = Api(api_bp)

MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/mwl/link-relations/"
ERROR_PROFILE = "/profiles/error/"

MEASUREMENT_PAGE_SIZE = 50

#app.register_blueprint(api_bp)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///development.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

@app.route("/api/",  methods=["GET"])
def entry():
    """entry point"""
    try:
        body = MovieBuilder()
        print("test1")
        body.add_namespace("mwl", LINK_RELATIONS_URL)
        print("test2")
        body.add_control_all_movies()
        print("test3")
        MASON = "application/vnd.mason+json"
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    except Exception as error:
        print(error)
        return "GET method required: {}".format(error)

@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"

@app.route("/profiles/<profile>/")
def send_profile(profile):
    return "you requests {} profile".format(profile)

@app.route("/admin/")
def admin_site():
    return app.send_static_file("html/admin.html")

'''MODELS'''
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

'''RESOURCES'''

LINK_RELATIONS_URL = "/mwl/link-relations/"
MASON = "application/vnd.mason+json"
MOVIE_PROFILE = "/profiles/movie/"

class MovieCollection(Resource):

    def get(self):
        body = MovieBuilder()

        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(MovieCollection))
        body.add_control_add_movie()
        body["items"] = []
        for db_movie in Movie.query.all():
            item = MovieBuilder(
                name=db_movie.name,
                genre=db_movie.genre,
            )
            item.add_control("self", api.url_for(MovieItem, movie=db_movie.name))
            item.add_control("profile", MOVIE_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Movie.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        movie = Movie(
            name=request.json["name"],
            genre=request.json["genre"],
        )

        try:
            db.session.add(movie)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Movie with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=201, headers={
            "Location": api.url_for(MovieItem, movie=request.json["name"])
        })

class MovieItem(Resource):

    def get(self, movie):
        db_movie = Movie.query.filter_by(name=movie).first()
        if db_movie is None:
            return create_error_response(404, "Not found", 
                "No movie was found with the name {}".format(movie)
            )
        
        body = MovieBuilder(
            name=db_movie.name,
            genre=db_movie.genre,
        )
        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(MovieItem, movie=movie))
        body.add_control("collection", api.url_for(MovieCollection))
        body.add_control_delete_movie(movie)
        body.add_control_modify_movie(movie)
        
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, movie):
        db_movie = Movie.query.filter_by(name=movie).first()
        if db_movie is None:
            return create_error_response(404, "Not found", 
                "No movie was found with the name {}".format(movie)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Movie.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_movie.name = request.json["name"]
        db_movie.model = request.json["genre"]
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Movie with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    def delete(self, movie):

        db_movie = Movie.query.filter_by(name=movie).first()
        if db_movie is None:
            return create_error_response(404, "Not found", 
                "No movie was found with the name {}".format(movie)
            )

        db.session.delete(db_movie)
        db.session.commit()

        return Response(status=204)

class MovieBuilder(MasonBuilder):

    def add_control_all_movies(self):
        self.add_control(
            "mwl:movies-all",
            api.url_for(MovieCollection),
            method="GET",
            title="get all movies"
        )

    def add_control_delete_movie(self, movie):
        self.add_control(
            "mwl:delete",
            api.url_for(MovieItem, movie=movie),
            method="DELETE",
            title="Delete this movie"
        )

    def add_control_add_movie(self):
        self.add_control(
            "mwl:add-movie",
            api.url_for(MovieCollection),
            method="POST",
            encoding="json",
            title="Add a new movie",
            schema=Movie.get_schema()
        )

    def add_control_modify_movie(self, movie):
        self.add_control(
            "edit",
            api.url_for(MovieItem, movie=movie),
            method="PUT",
            encoding="json",
            title="Edit this movie",
            schema=Movie.get_schema()
        )

api.add_resource(MovieCollection, "/movies/")
api.add_resource(MovieItem, "/movies/<movie>/")

