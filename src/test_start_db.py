"""Unit testing examples are found from the course excercise material: Testing flask applications part 1, especially initial db_handle function and set_sqllite_pragma method"""
import os
import pytest
import tempfile

import app

from sqlalchemy.exc import IntegrityError
from app import Uploader, Movie
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.app.config["TESTING"] = True
    
    with app.app.app_context():
        app.db.create_all()
        
    yield app.db
    
    app.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

    
def get_movie(id_num=1):
    """BoilerPlate seen in the excercise 1 test examples"""
    movie = Movie(
        id=id_num,
        name="RAMBO1",
        genre="ACTION"
    )
    return movie
    
def get_uploader(id_num=1):
    """BoilerPlate seen in the excercise 1 test examples"""
    uploader = Uploader(
        id=id_num,
        uploader_name="Niko",
        email="mail@mail.com"
    )
    return uploader
    
def test_create_movie(db_handle):
    '''Unit test for creating a movie to the db succesfully'''
    #movie = _get_movie
    movie = get_movie()
    db_handle.session.add(movie)
    db_handle.session.commit()
    assert Movie.query.count() == 1
    
def test_movie_name_unique(db_handle):
    """Unit test for invalid db commit with 2 items with same id"""
    mov1 = get_movie()
    mov2 = get_movie()
    db_handle.session.add(mov1)
    db_handle.session.add(mov2)    
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
        
def test_uploader_name_unique(db_handle):
    """Unit test for invalid db commit with 2 items with same name"""
    up1 = get_uploader()
    up2 = get_uploader()
    db_handle.session.add(up1)
    db_handle.session.add(up2)    
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
        
        
        
        
        
        
        
        
        