from flask import Flask
from flask_restful import Resource, Api
from models import Movie
from mason import MasonBuilder
from flask_restful import Resource, Api
from flask import Flask

LINK_RELATIONS_URL = "/mwl/link-relations/"
MASON = "application/vnd.mason+json"
MOVIE_PROFILE = "/profiles/sensor/"

app = Flask(__name__)
api = Api(app)

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
                model=db_movie.model,
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
                "No sensor was found with the name {}".format(movie)
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
        
        
        