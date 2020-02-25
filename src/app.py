from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

import utils


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

app = Flask(__name__)
from models import Movie, Uploader, db
from mason import MasonBuilder
import resources
from resources import MovieBuilder

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
