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
conn = psycopg2.connect(environ["DB_STRING"])
cur = conn.cursor(cursor_factory=RealDictCursor)


@app.route("/search/<txt>", methods=["GET"])
def data(txt):
    global cur, conn
    s = str(txt).strip().replace(" ", "%")
    try:
        cur.callproc('search', (s,))
        json = jsonify(cur.fetchall())
        return json
    except Exception as e:
        print(e)
        # try to reconnect and query again
        conn = psycopg2.connect(environ["DB_STRING"])
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.callproc('search', (s,))
        json = jsonify(cur.fetchall())
        return json


@app.route("/", methods=["GET"])
def index():

    return render_template("index.html")


if __name__ == '__main__':
    app.run()
