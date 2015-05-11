from datetime import date
from quotas import db
from sqlalchemy import PrimaryKeyConstraint


class Org(db.Model):
    """ Model for a specific Org's quota """
    __tablename__ = 'quotas'

    guid = db.Column(db.String)
    date_collected = db.Column(db.DateTime())
    name = db.Column(db.String)
    memory_limit = db.Column(db.Integer())
    total_routes = db.Column(db.Integer())
    total_services = db.Column(db.Integer())
    url = db.Column(db.String())
    created_at = db.Column(db.DateTime())
    updated_at = db.Column(db.DateTime())

    __table_args__ = (PrimaryKeyConstraint(
        'guid', 'date_collected', name='guid_date'),)

    def __init__(self, guid, name, url):
        self.guid = guid
        self.name = name
        self.url = url
        self.date_collected = date.today()

    def __repr__(self):
        return '<name {}>'.format(self.name)

    def display(self):
        """ Displays Org in dict format """
        return {
            'guid': self.guid,
            'date_collected': self.date_collected,
            'name': self.name,
            'memory_limit': self.memory_limit,
            'total_routes': self.total_routes,
            'total_services': self.total_services,
            'url': self.url,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    # Resources
    @classmethod
    def list_all(cls):
        """ Lists all of the Orgs data (This endpoint will be
            refactored later) """
        data = cls.query.order_by(cls.guid).all()
        return [org.display() for org in data]

    @classmethod
    def list_one(cls, guid):
        """ List one Org and all dates """
        data = cls.query.filter_by(guid=guid).all()
        if len(data) > 0:
            return [org.display() for org in data]
