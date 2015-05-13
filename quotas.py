import os
from flask import Flask, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)

from models import Quota


@app.route("/", methods=['GET'])
def home():
    return "Quotas APP"


@app.route("/api/", methods=['GET'])
def api_index():
    return "API endpoints /api/quotas and /api/quotas/<guid>"


@app.route("/api/quotas", methods=['GET'])
def all():
    return jsonify({'Quotas': Quota.list_all()})


@app.route("/api/quotas/<guid>", methods=['GET'])
def one(guid):
    data = Quota.list_one(guid=guid)
    if data:
        return jsonify(data)
    else:
        return '404.html', 404


@app.route("/api/quotas/<guid>/<start_date>/<end_date>", methods=['GET'])
def details(guid, start_date, end_date):
    data = Quota.list_one(guid=guid, start_date=start_date, end_date=end_date)
    if data:
        return jsonify(data)
    else:
        return '404.html', 404

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='localhost', port=port)
