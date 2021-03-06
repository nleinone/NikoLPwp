# NikoLPwp
MOVIE WISHLISTER

Student 1: Niko Leinonen <nikoleino91@gmail.com>

DEPENDENCIES:

Python 3.7.2 or newer

Sqlalchemy: https://docs.sqlalchemy.org/en/13/intro.html#installation

flask_restful library: https://flask-restful.readthedocs.io/en/latest/installation.html

flask library: https://flask.palletsprojects.com/en/1.1.x/installation/

json library: command line :> pip install json

HOW TO OPERATE (On windows):

1. Open command line terminal.
2. Go to the folder where the files are installed with the terminal (./src/).
3. Type the following line to the terminal: flask run

This will initialize the empty SQLAlchemy database and start running the server application.

4. Open another command line terminal.
5. Go to the folder where the files are installed with the terminal (./src/).
6. Type the following line to the terminal: Python start_client.py

This launches the client app, which communicates with the server app (observable in the first command line terminal)

As both the server application and the client application is running, data items can be inserted with command line following the User interface options.

TESTING:
DEPENDENCIES:
pytest: pip install pytest
pytest coverage: pip install pytest.cov

HOW TO OPERATE:

1. Open command line terminal.
2. Go to the folder where the files are installed with the terminal (./src/).
3. Type the following line to the terminal: pytest

This will run a series of unit tests, testing the functionalities of database insertions and server application methods/resources.
Two separate scripts are ran: test_start_db (db unit tests) and test_start_resources (resource and API tests). These tests were created with the help of lecture materials, customized to the project's needs.

All different components of the server application are located in the /src/.






