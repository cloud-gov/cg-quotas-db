from datetime import date
from quotas import db
from sqlalchemy import func
from sqlalchemy.orm import relationship


class Service(db.Model):
    """ Model for storing specific service data """

    __tablename__ = 'service'

    quota = db.Column(db.String, db.ForeignKey('quota.guid'))
    guid = db.Column(db.String())
    date_collected = db.Column(db.Date())
    name = db.Column(db.String())

    # Limiting the data by date
    __table_args__ = (db.PrimaryKeyConstraint(
        'quota', 'guid', 'date_collected', name='quota_guid_date'),)

    def __init__(self, quota, guid, name):
        self.quota = quota
        self.guid = guid
        self.name = name
        self.date_collected = date.today()

    def __repr__(self):
        return '<guid {0} date {1}>'.format(self.quota, self.date_collected)

    def details(self):
        """ Displays Service in dict format """
        return {
            'quota_guid': self.quota,
            'date_collected': str(self.date_collected),
            'guid': self.guid,
            'name': self.name,
        }

    @classmethod
    def aggregate(cls, quota_guid, start_date=None, end_date=None):
        """ Counts the number of days a Service has been active """
        q = db.session.query(
            cls.name, cls.guid, func.count(cls.date_collected))
        if start_date and end_date:
            q = q.filter(cls.date_collected.between(start_date, end_date))
        q = q.filter_by(quota=quota_guid).group_by(cls.guid)
        return q.all()


class QuotaData(db.Model):
    """ Model for a specific Quotas's data """

    __tablename__ = 'data'

    quota = db.Column(db.String, db.ForeignKey('quota.guid'))
    date_collected = db.Column(db.Date())
    memory_limit = db.Column(db.Integer())
    total_routes = db.Column(db.Integer())
    total_services = db.Column(db.Integer())

    # Limiting the data by date
    __table_args__ = (db.PrimaryKeyConstraint(
        'quota', 'date_collected', name='quota_guid_date'),)

    def __init__(self, quota):
        self.quota = quota
        self.date_collected = date.today()

    def __repr__(self):
        return '<guid {0} date {1}>'.format(self.quota, self.date_collected)

    def details(self):
        """ Displays QuotaData in dict format """
        return {
            'quota_guid': self.quota,
            'date_collected': str(self.date_collected),
            'memory_limit': self.memory_limit,
            'total_routes': self.total_routes,
            'total_services': self.total_services,
        }

    @classmethod
    def aggregate(cls, quota_guid, start_date=None, end_date=None):
        """ Counts the number of days a specific memory setting has
        been active """
        q = db.session.query(cls.memory_limit, func.count(cls.date_collected))
        if start_date and end_date:
            q = q.filter(cls.date_collected.between(start_date, end_date))
        q = q.filter_by(quota=quota_guid).group_by(cls.memory_limit)
        return q.all()


class Quota(db.Model):
    """ Model for a specific quota """

    __tablename__ = 'quota'

    guid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    url = db.Column(db.String())
    created_at = db.Column(db.DateTime())
    updated_at = db.Column(db.DateTime())
    data = relationship("QuotaData")
    services = relationship("Service")

    def __init__(self, guid, name, url):
        self.guid = guid
        self.name = name
        self.url = url

    def __repr__(self):
        return '<name {}>'.format(self.name)

    def foreign_key_preparer(self, model, start_date=None, end_date=None):
        """ Prepares data from foreign keys """
        data = model.query.filter_by(quota=self.guid)
        if start_date and end_date:
            data = data.filter(
                model.date_collected.between(start_date, end_date))
        data = data.order_by(model.date_collected).all()
        return [item.details() for item in data]

    def details(self):
        """ Displays Quota in dict format """
        return {
            'guid': self.guid,
            'name': self.name,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def data_details(self, start_date=None, end_date=None):
        """ Displays Quota in dict format with data details """
        data = self.foreign_key_preparer(
            model=QuotaData, start_date=start_date, end_date=end_date)
        services = self.foreign_key_preparer(
            model=Service, start_date=start_date, end_date=end_date)
        return {
            'guid': self.guid,
            'name': self.name,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data': data,
            'services': services
        }

    def data_aggregates(self, start_date=None, end_date=None):
        """ Displays Quota in dict format with data details """
        data = QuotaData.aggregate(
            quota_guid=self.guid, start_date=start_date, end_date=end_date)
        services = Service.aggregate(
            quota_guid=self.guid, start_date=start_date, end_date=end_date)
        return {
            'guid': self.guid,
            'name': self.name,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data': data,
            'services': services
        }

    # Resources
    @classmethod
    def list_one_details(cls, guid, start_date=None, end_date=None):
        """ List one quota along with all data on memory usage and services """
        quota = cls.query.filter_by(guid=guid).first()
        if quota:
            return quota.data_details(
                start_date=start_date, end_date=end_date)

    @classmethod
    def list_one_aggregate(cls, guid, start_date=None, end_date=None):
        """ List one quota and aggregation of service and memory usage
        by date """
        quota = cls.query.filter_by(guid=guid).first()
        if quota:
            return quota.data_aggregates(
                start_date=start_date, end_date=end_date)

    @classmethod
    def list_all(cls):
        """ Lists all of the Quota data (This endpoint will be
            refactored later) """
        quotas = cls.query.order_by(cls.guid).all()
        return [quota.details() for quota in quotas]
