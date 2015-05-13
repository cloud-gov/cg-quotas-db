from datetime import date
from quotas import db
from sqlalchemy.orm import relationship


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


class Quota(db.Model):
    """ Model for a specific quota """

    __tablename__ = 'quota'

    guid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    url = db.Column(db.String())
    created_at = db.Column(db.DateTime())
    updated_at = db.Column(db.DateTime())
    data = relationship("QuotaData")

    def __init__(self, guid, name, url):
        self.guid = guid
        self.name = name
        self.url = url

    def __repr__(self):
        return '<name {}>'.format(self.name)

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
        quota_data = QuotaData.query.filter_by(quota=self.guid)
        if start_date and end_date:
            quota_data = quota_data.filter(
                QuotaData.date_collected.between(start_date, end_date))
        quota_data = quota_data.order_by(QuotaData.date_collected).all()
        data = [item.details() for item in quota_data]
        return {
            'guid': self.guid,
            'name': self.name,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data': data
        }

    # Resources
    @classmethod
    def list_one(cls, guid, start_date=None, end_date=None):
        """ List one quota and all dates """
        quota = cls.query.filter_by(guid=guid).first()
        if quota:
            return quota.data_details(start_date=start_date, end_date=end_date)

    @classmethod
    def list_all(cls):
        """ Lists all of the Quota data (This endpoint will be
            refactored later) """
        quotas = cls.query.order_by(cls.guid).all()
        return [quota.details() for quota in quotas]
