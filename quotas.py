import os
from flask import Flask, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)

from models import Org


@app.route("/", methods=['GET'])
def home():
    return "Quotas APP"


@app.route("/api/", methods=['GET'])
def api_index():
    return "API endpoints /api/orgs and /api/orgs/<guid>"


@app.route("/api/orgs", methods=['GET'])
def all():
    return jsonify({'Orgs': Org.list_all()})


@app.route("/api/org/<guid>", methods=['GET'])
def one(guid):
    data = Org.list_one(guid=guid)
    if data:
        return jsonify({'Org': data})
    else:
        return '404.html', 404

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='localhost', port=port)
