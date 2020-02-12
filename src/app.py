from mason import MasonBuilder
import utils

from resources import MovieCollection, MovieItem, MovieBuilder
from models import Movie

import click
import json
from flask import Flask, Blueprint, Response, request
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError

app = Flask(__name__)
#api_bp = Blueprint("api", __name__, url_prefix="/api")
#api = Api(api_bp)
api = Api(app)

MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/mwl/link-relations/"
ERROR_PROFILE = "/profiles/error/"

MEASUREMENT_PAGE_SIZE = 50

#app.register_blueprint(api_bp)

api.add_resource(MovieCollection, "/movies/")
api.add_resource(MovieItem, "/movies/<movie>/")

#api.init_app(app)

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

    