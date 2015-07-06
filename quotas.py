import os

from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from flask import Flask, Response, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from auth import requires_auth

app = Flask(__name__, static_url_path='')
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)

# Schedule Updates
from scripts import load_data
scheduler = BackgroundScheduler()
job = scheduler.add_job(load_data, 'cron', hour='3,12,18')
scheduler.start()

# Import Quota model
from api import QuotaResource


@app.route("/", methods=['GET'])
@requires_auth
def index():
    return app.send_static_file("index.html")


@app.route("/api/quotas/", methods=['GET'])
@requires_auth
def api_all_dates():
    """ Endpoint that lists all quotas with details between
    two specific dates """
    start_date = request.args.get('since')
    end_date = request.args.get('until', datetime.datetime.today().now())
    return jsonify(
        {'Quotas':
            QuotaResource.list_all(start_date=start_date, end_date=end_date)}
    )


@app.route("/api/quotas/<guid>/", methods=['GET'])
@requires_auth
def api_one_dates(guid):
    """ Endpoint that lists one quota details limited by date """
    start_date = request.args.get('since')
    end_date = request.args.get('until', datetime.datetime.today().now())
    data = QuotaResource.list_one_aggregate(
        guid=guid, start_date=start_date, end_date=end_date)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'No Data'}), 404


@app.route('/quotas.csv')
@requires_auth
def download_quotas():
    """ Route for downloading quotas """
    start_date = request.args.get('since')
    end_date = request.args.get('until', datetime.datetime.today().now())
    csv = QuotaResource.generate_cvs(start_date=start_date, end_date=end_date)
    return Response(csv, mimetype='text/csv')

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
