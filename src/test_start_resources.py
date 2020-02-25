"""Unit testing examples are found from the course excercise material: Testing flask applications part 1, especially initial db_handle function and set_sqllite_pragma method"""
import json
import os
import pytest
import tempfile
import time

import app

from app import app, db
from jsonschema import validate
from sqlalchemy.exc import IntegrityError
from app import Uploader, Movie
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture

def client():
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    _populate_db()

    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _get_movie_json(number=1):
    """
    Creates a valid json JSON object to be used for PUT and POST tests.
    """
    uploader_object = Uploader.query.filter_by(uploader_name="Niko").first()
    
    return {"name": "RAMBO{}".format(number), "genre": "action", "uploader": str(uploader_object)}

def _get_uploader_json():
    """
    Creates a valid json JSON object to be used for PUT and POST tests.
    """

    return {"uploader_name": "Niko", "email": "gmail"}
    
def _populate_db():
    #Populate database with 3 movies and 1 uploader:
    for i in range(1, 4):
        
        u = Uploader(
            uploader_name="Niko",
            email="gmail")
        
        s = Movie(
            name="RAMBO{}".format(i),
            genre="action",
            uploader=u
        )
        db.session.add(s)
        
    db.session.commit()

def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """
    
    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200

def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """
    
    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204
    
def _check_control_put_method(ctrl, client, obj, isUploaderMethod=False):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    
    if isUploaderMethod == True:
        body = _get_uploader_json()
        body["uploader_name"] = obj["uploader_name"]
    else:
        body = _get_movie_json()
        body["name"] = obj["name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204
    
def _check_control_post_method(ctrl, client, obj):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_movie_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201
  
class TestMovieCollection(object):

    RESOURCE_URL = "/movies/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item
            assert "genre" in item
            
    def test_post_valid_request(self, client):
        valid = _get_movie_json(5)
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "RAMBO5"
        assert body["genre"] == "action"
        
    def test_post_wrong_mediatype(self, client):
        valid = _get_movie_json()
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
    def test_post_missing_field(self, client):
        valid = _get_movie_json()
        valid.pop("genre")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
            
class TestMovieItem(object):

    RESOURCE_URL = "/movies/RAMBO1/"
    INVALID_URL = "/movies/non-movie-x/"
    MODIFIED_URL = "/movies/RAMBO1/"
    
    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "RAMBO1"
        assert body["genre"] == "action"
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body)
        _check_control_delete_method("mwl:delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404
    
    def test_put(self, client):
        """
        Tests the PUT method. Checks all of the possible erroe codes, and also
        checks that a valid request receives a 204 response. Also tests that
        when name is changed, the sensor can be found from a its new URI. 
        """
        
        valid = _get_movie_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another movie's name
        valid["name"] = "RAMBO2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid (only change model)
        valid["name"] = "RAMBO1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
        # remove field for 400
        valid.pop("genre")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        valid = _get_movie_json()
        resp = client.put(self.RESOURCE_URL, json=valid)
        resp = client.get(self.MODIFIED_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["genre"] == valid["genre"]
    
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404
            
            
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
            
class TestUploaderCollection(object):

    RESOURCE_URL = "/movies/uploaders/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "uploader_name" in item
            assert "email" in item
    
    def test_post_valid_request(self, client):
        valid = _get_uploader_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["uploader_name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["uploader_name"] == "Niko"
        assert body["email"] == "gmail"
        
    def test_post_wrong_mediatype(self, client):
        valid = _get_uploader_json()
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
    def test_post_missing_field(self, client):
        valid = _get_uploader_json()
        valid.pop("email")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
            
class TestUploaderItem(object):

    RESOURCE_URL = "/movies/uploaders/Niko/"
    INVALID_URL = "/movies/uploaders/kati/"
    MODIFIED_URL = "/movies/uploaders/Niko/"
    
    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["uploader_name"] == "Niko"
        assert body["email"] == "gmail"
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit-uploader", client, body, True)
        _check_control_delete_method("mwl:delete-uploader", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404
    
    def test_put(self, client):
        """
        Tests the PUT method. Checks all of the possible erroe codes, and also
        checks that a valid request receives a 204 response. Also tests that
        when name is changed, the sensor can be found from a its new URI. 
        """
        
        valid = _get_uploader_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with valid (only change model)
        valid["uploader_name"] = "Niko2"
        valid["email"] = "gmail2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
        # remove field for 400
        valid.pop("email")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        valid = _get_uploader_json()
        resp = client.put(self.RESOURCE_URL, json=valid)
        resp = client.get(self.MODIFIED_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["email"] == valid["email"]
            
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
            
            