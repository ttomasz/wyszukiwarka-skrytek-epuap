"""This file contains the app.
Database search functionality and Flask app have been put together to fit into 1 free Heroku dyno (container).
"""

from flask import Flask, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from os import environ

app = Flask(__name__)


@app.route("/search/<txt>", methods=["GET"])
def data(txt):
    s = str(txt).strip().replace(" ", "%")
    cur.callproc('search', (s,))

    return jsonify(cur.fetchall())


@app.route("/", methods=["GET"])
def index():

    return render_template("index.html")


if __name__ == '__main__':
    conn = psycopg2.connect(environ["DB_STRING"])
    cur = conn.cursor(cursor_factory=RealDictCursor)
    app.run()
