from flask import Flask, Blueprint, Response, request
from mason import MasonBuilder
import json

MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"

def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)