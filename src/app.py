from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError


#from resources import MovieCollection, MovieItem, MovieBuilder
import utils
from mason import MasonBuilder

from flask_restful import Resource, Api
from flask import Flask, Blueprint, Response, request
from flask_sqlalchemy import SQLAlchemy

from jsonschema import validate, ValidationError
import json

"""
REFERENCES:
Course lecture materials were used as a guideance of this project. The MasonBuilder in entirety was downloaded  from the excercise pages.
"""

MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/mwl/link-relations/"
ERROR_PROFILE = "/profiles/error/"

MEASUREMENT_PAGE_SIZE = 50

app = Flask(__name__)

from models import Movie, Uploader, db

api = Api(app)

def create_error_response(status_code, title, message=None):
    """Method for creating Mason error response"""
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)

@app.route("/api/",  methods=["GET"])
def entry():
    """API entry point method"""
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
    """Template function for sending link relations"""
    return "link relations"

@app.route("/profiles/<profile>/")
def send_profile(profile):
    """Template function for sending profiles"""
    return "you requests {} profile".format(profile)

@app.route("/admin/")
def admin_site():
    """Template function for admin.html responses"""
    return app.send_static_file("html/admin.html")

'''RESOURCES'''

LINK_RELATIONS_URL = "/mwl/link-relations/"
MASON = "application/vnd.mason+json"
MOVIE_PROFILE = "/profiles/movie/"
UPLOADER_PROFILE = "/profiles/uploader/"

class MovieCollection(Resource):
    '''Collection of all the movies in the database'''

    def get(self):
        """Method for GET all movies with appriopriate controls"""
        body = MovieBuilder()
        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(MovieCollection))
        body.add_control_add_movie()
        body.add_control_all_uploaders()
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
        """Method for POST a new single movie item to the database"""
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Movie.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        
        #Find uploader for the movie:
        uploader=request.json["uploader"]
        #email=request.json["email"]
        uploader_object = Uploader.query.filter_by(uploader_name=uploader).first()
        
        movie = Movie(
            name=request.json["name"],
            genre=request.json["genre"],
            uploader=uploader_object
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
    """Resource class for accessing all uploaders"""

    def get(self):
        """Method for GET all uploaders from the database"""
        body = MovieBuilder()

        body.add_namespace("mwl", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(UploaderCollection))
        body.add_control_add_uploader()
        
        body["items"] = []
        for db_uploaders in Uploader.query.all():
            item = MovieBuilder(
                uploader_name=db_uploaders.uploader_name,
                email=db_uploaders.email,
            )
            item.add_control("self", api.url_for(UploaderItem, uploader_name=db_uploaders.uploader_name))
            item.add_control("profile", UPLOADER_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        """Method for POST a new single uploader to the database"""
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Uploader.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        uploader = Uploader(
            uploader_name=request.json["uploader_name"],
            email=request.json["email"],
        )

        try:
            db.session.add(uploader)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Uploader with name '{}' already exists.".format(request.json["uploader_name"])
            )

        return Response(status=201, headers={
            "Location": api.url_for(UploaderItem, uploader_name=request.json["uploader_name"])
        })
    
class MovieItem(Resource):
    """Resource class for single movie item"""
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
        """Method for editing (PUT) a single movie item in the database"""
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
        """Method for deleting a movie from the database with movie name"""
        db_movie = Movie.query.filter_by(name=movie).first()
        if db_movie is None:
            return create_error_response(404, "Not found", 
                "No movie was found with the name {}".format(movie)
            )

        db.session.delete(db_movie)
        db.session.commit()

        return Response(status=204)

class UploaderItem(Resource):
    """Resource class for single uploader"""
    def get(self, uploader_name):
        """Method for getting a single uploader from the database"""
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
        
        body["items"] = []
        for db_movie in Movie.query.all():

            uploader_object = db_movie.uploader
            if uploader_object is not None:
                uploader_object_name = uploader_object.uploader_name
            else:
                uploader_object_name = "No name"
            if uploader_object_name == uploader_name:
                item = MovieBuilder(
                    name=db_movie.name,
                    genre=db_movie.genre
                )
                item.add_control("self", api.url_for(MovieItem, movie=db_movie.name))
                item.add_control("profile", MOVIE_PROFILE)
                body["items"].append(item)
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, uploader_name):
        """Method for editing a single uploader in the database"""
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
        db_uploader.email = request.json["email"]
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Uploader with name '{}' already exists.".format(request.json["uploader_name"])
            )

        return Response(status=204)

    def delete(self, uploader_name):
        """Method for deleting a uploader from the database"""
        db_uploader = Uploader.query.filter_by(uploader_name=uploader_name).first()
        if db_uploader is None:
            return create_error_response(404, "Not found", 
                "No Uploader was found with the name {}".format(uploader_name)
            )

        db.session.delete(db_uploader)
        db.session.commit()

        return Response(status=204)        
        
class MovieBuilder(MasonBuilder):
    """Custom Masonbuilder for building different controls for resources"""
    def add_control_all_movies(self):
        """Control for getting all the movie in the entry point"""
        self.add_control(
            "mwl:movies-all",
            api.url_for(MovieCollection),
            method="GET",
            title="get all movies"
        )
    
    def add_control_all_uploaders(self):
        """Control for getting all the uploaders from the movie collection resource"""
        self.add_control(
            "mwl:uploaders-all",
            api.url_for(UploaderCollection),
            method="GET",
            title="get all uploaders"
        )
        
    def add_control_add_uploader(self):
        """Control for adding a new uploader"""
        self.add_control(
            "mwl:add-uploader",
            api.url_for(UploaderCollection),
            method="POST",
            encoding="json",
            title="Add a new uploader",
            schema=Uploader.get_schema()
        )    
        
    def add_control_delete_movie(self, movie):
        """Control for deleting a movie"""
        self.add_control(
            "mwl:delete",
            api.url_for(MovieItem, movie=movie),
            method="DELETE",
            title="Delete this movie"
        )
        
    def add_control_delete_uploader(self, uploader_name):
        """Control for deleting a uploader"""
        self.add_control(
            "mwl:delete-uploader",
            api.url_for(UploaderItem, uploader_name=uploader_name),
            method="DELETE",
            title="Delete this uploader"
        )
        
    def add_control_modify_uploader(self, uploader_name):
        """Control for editing a uploader"""
        self.add_control(
            "edit-uploader",
            api.url_for(UploaderItem, uploader_name=uploader_name),
            method="PUT",
            encoding="json",
            title="Edit this uploader",
            schema=Uploader.get_schema()
        )

    def add_control_add_movie(self):
        """Control for adding a movie"""
        self.add_control(
            "mwl:add-movie",
            api.url_for(MovieCollection),
            method="POST",
            encoding="json",
            title="Add a new movie",
            schema=Movie.get_schema()
        )

    def add_control_modify_movie(self, movie):
        """Control for editing a movie"""
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
api.add_resource(UploaderCollection, "/movies/uploaders/")
api.add_resource(UploaderItem, "/movies/uploaders/<uploader_name>/")