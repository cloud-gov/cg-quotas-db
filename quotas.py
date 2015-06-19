import os

from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from flask import Flask, Response, jsonify, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)


# Schedule Updates
from scripts import load_data
scheduler = BackgroundScheduler()
job = scheduler.add_job(load_data, 'cron', hour='3,12,18')
scheduler.start()

# Import Quota model
from models import Quota


@app.route("/", methods=['GET'])
def all():
    """ Initalize site with a list of Quotas """
    return jsonify(quotas=Quota.list_all())


@app.route("/api/quotas/", methods=['GET'])
def api_all_dates():
    """ Endpoint that lists all quotas with details between
    two specific dates """
    start_date = request.args.get('since')
    end_date = request.args.get('until', datetime.datetime.today().now())
    return jsonify(
        {'Quotas': Quota.list_all(start_date=start_date, end_date=end_date)}
    )


@app.route("/api/quotas/<guid>/", methods=['GET'])
def api_one_dates(guid):
    """ Endpoint that lists one quota details limited by date """
    start_date = request.args.get('since')
    end_date = request.args.get('until', datetime.datetime.today().now())
    data = Quota.list_one_aggregate(
        guid=guid, start_date=start_date, end_date=end_date)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'No Data'}), 404


@app.route('/quotas.csv')
def download_quotas():
    """ Route for downloading quotas """
    start_date = request.args.get('since')
    end_date = request.args.get('until', datetime.datetime.today().now())
    csv = Quota.generate_cvs(start_date=start_date, end_date=end_date)
    return Response(csv, mimetype='text/csv')

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
