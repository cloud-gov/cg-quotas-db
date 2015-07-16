from datetime import date
from quotas import db
from sqlalchemy.orm import relationship


class Service(db.Model):
    """ Model for storing specific service data """

    __tablename__ = 'service'

    quota = db.Column(db.String, db.ForeignKey('quota.guid'))
    guid = db.Column(db.String())
    date_collected = db.Column(db.Date())
    instance_name = db.Column(db.String())
    label = db.Column(db.String())
    provider = db.Column(db.String())

    # Limiting the data by date
    __table_args__ = (db.PrimaryKeyConstraint(
        'quota', 'guid', 'date_collected', name='quota_serviceguid_date'),)

    def __init__(self, quota, guid, instance_name,
                 label=None, provider=None, date_collected=None):
        self.quota = quota
        self.guid = guid
        self.instance_name = instance_name
        self.label = label
        self.provider = provider
        if date_collected:
            self.date_collected = date_collected
        else:
            self.date_collected = date.today()

    def __repr__(self):
        return '<guid {0} date {1}>'.format(self.quota, self.date_collected)


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

    def __init__(self, quota, date_collected=None):
        self.quota = quota
        if date_collected:
            self.date_collected = date_collected
        else:
            self.date_collected = date.today()

    def __repr__(self):
        return '<guid {0} date {1}>'.format(self.quota, self.date_collected)


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

    def __init__(self, guid, name=None, url=None):
        self.guid = guid
        if name:
            self.name = name
        if url:
            self.url = url

    def __repr__(self):
        return '<name {}>'.format(self.name)
