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

MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/mwl/link-relations/"
ERROR_PROFILE = "/profiles/error/"

MEASUREMENT_PAGE_SIZE = 50

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///development.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)

@app.route("/api/",  methods=["GET"])
def entry():
    """entry point"""
    try:
        body = MovieBuilder()
        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control_all_movies()
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

class Uploader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploader_name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    #movie_id = db.Column(db.Integer, db.ForeignKey("movie.id"))
    
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
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
example_movie()

'''RESOURCES'''

LINK_RELATIONS_URL = "/mwl/link-relations/"
MASON = "application/vnd.mason+json"
MOVIE_PROFILE = "/profiles/movie/"
UPLOADER_PROFILE = "/profiles/uploader/"

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
                genre=db_movie.genre
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
            genre=request.json["genre"]
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

class UploaderCollection(Resource):

#Uploader_Profile

    def get(self):
        body = MovieBuilder()

        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(UploaderCollection))
        body.add_control_add_uploader()
        
        body["items"] = []
        for db_uploaders in Uploader.query.all():
            item = MovieBuilder(
                name=db_uploaders.name,
                email=db_uploaders.email,
            )
            item.add_control("self", api.url_for(UploaderItem, uploader=db_uploaders.name))
            item.add_control("profile", UPLOADER_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Uploader.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        uploader = Uploader(
            name=request.json["name"],
            email=request.json["email"],
        )

        try:
            db.session.add(uploader)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Uploader with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=201, headers={
            "Location": api.url_for(UploaderItem, name=request.json["name"])
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
            genre=db_movie.genre
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
        db_movie.genre = request.json["genre"]
        
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

class UploaderItem(Resource):

    def get(self, uploader_name):
        db_uploader = Uploader.query.filter_by(uploader_name=uploader_name).first()
        if db_uploader is None:
            return create_error_response(404, "Not found", 
                "No uploader was found with the name {}".format(uploader_name)
            )
        
        body = MovieBuilder(
            uploader_name=db_uploader.uploader_name,
            email=db_uploader.email,
        )
        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(UploaderItem, uploader_name=uploader_name))
        body.add_control("collection", api.url_for(UploaderCollection))
        body.add_control_delete_uploader(uploader_name)
        body.add_control_modify_uploader(uploader_name)
        
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, uploader_name):
        db_uploader = Uploader.query.filter_by(uploader_name=uploader_name).first()
        if db_uploader is None:
            return create_error_response(404, "Not found", 
                "No uploader was found with the name {}".format(uploader_name)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Uploader.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_uploader.uploader_name = request.json["uploader_name"]
        db_uploader.email = request.json["genre"]
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Uploader with name '{}' already exists.".format(request.json["uploader_name"])
            )

        return Response(status=204)

    def delete(self, uploader_name):

        db_uploader = Uploader.query.filter_by(uploader_name=uploader_name).first()
        if db_uploader is None:
            return create_error_response(404, "Not found", 
                "No Uploader was found with the name {}".format(uploader_name)
            )

        db.session.delete(db_uploader)
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
    
    def add_control_all_uploaders(self):
        self.add_control(
            "mwl:uploaders-all",
            api.url_for(UploaderCollection),
            method="GET",
            title="get all uploaders"
        )
        
    def add_control_add_uploader(self):
        self.add_control(
            "mwl:add-uploader",
            api.url_for(UploaderCollection),
            method="POST",
            encoding="json",
            title="Add a new uploader",
            schema=Uploader.get_schema()
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
#api.add_resource(UploaderCollection, "/movies/uploaders/")
#api.add_resource(UploaderItem, "/movies/uploaders/<uploader>/")