import os
from flask import Flask, jsonify, render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)

from models import Quota


@app.route("/", methods=['GET'])
def all():
    return render_template('index.html', quotas=Quota.list_all())


@app.route("/quotas/<guid>/", methods=['GET'])
def one(guid):
    data = Quota.list_one_aggregate(guid=guid)
    if data:
        return render_template('details.html', quota=data)
    else:
        return '404.html', 404


@app.route("/quotas/<guid>/<start_date>/<end_date>", methods=['GET'])
def dates(guid, start_date, end_date):
    data = Quota.list_one_aggregate(
        guid=guid, start_date=start_date, end_date=end_date)
    if data:
        return render_template('details.html', quota=data)
    else:
        return '404.html', 404


@app.route("/api/", methods=['GET'])
def api_index():
    return "API endpoints /api/quotas/ and /api/quotas/<guid>/"


@app.route("/api/quotas/", methods=['GET'])
def api_all():
    return jsonify({'Quotas': Quota.list_all()})


@app.route("/api/quotas/<guid>/", methods=['GET'])
def api_one(guid):
    data = Quota.list_one_aggregate(guid=guid)
    if data:
        return jsonify(data)
    else:
        return '404.html', 404


@app.route("/api/quotas/<guid>/<start_date>/<end_date>/", methods=['GET'])
def api_one_dates(guid, start_date, end_date):
    data = Quota.list_one_aggregate(
        guid=guid, start_date=start_date, end_date=end_date)
    if data:
        return jsonify(data)
    else:
        return '404.html', 404

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
