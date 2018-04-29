"""This file contains the app.
Database search functionality and Flask app have been put together to fit into 1 free Heroku dyno (container).
Requires environmental variable:
DB_STRING - psycopg2 string to connect to database
"""

from flask import Flask, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from os import environ

app = Flask(__name__)
conn = None


def get_db():
    global conn
    if conn is None:
        try:
            conn = psycopg2.connect(environ["DB_STRING"])
        except Exception as e:
            print(e)
    return conn


@app.route("/search/<txt>", methods=["GET"])
def data(txt: str, czy_urzad: bool = False, limit: int = 100):
    with get_db().cursor(cursor_factory=RealDictCursor) as cur:
        s = str(txt).strip().replace(" ", "%")
        s = "%" + s + "%"

        try:
            cur.callproc('search', (str(txt).strip(), s, czy_urzad, limit))
        except Exception as e:
            print(e)
        json = jsonify(cur.fetchall())

    return json


@app.route("/get_uris/<id>")
def get_uris(id):
    with get_db().cursor(cursor_factory=RealDictCursor) as cur:
        try:
            print(int(id))
            cur.execute("SELECT skrytki FROM skrytki2 WHERE id = %s", (int(id),))
        except Exception as e:
            print(e)
        json = jsonify(cur.fetchall())

    return json


@app.route("/", methods=["GET"])
def index():

    return render_template("index.html")


if __name__ == '__main__':
    app.run()
