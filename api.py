import io
import csv
import os

from sqlalchemy import func
from models import Service, QuotaData, Quota
from quotas import db


class ServiceResource(Service):

    def details(self):
        """ Displays Service in dict format """
        return {
            'quota_guid': self.quota,
            'date_collected': str(self.date_collected),
            'guid': self.guid,
            'instance_name': self.instance_name,
            'label': self.label,
            'provider': self.provider,
        }

    @classmethod
    def aggregate(cls, quota_guid, start_date=None, end_date=None):
        """ Counts the number of days a Service has been active """
        q = db.session.query(
            cls.label, cls.guid, func.count(cls.date_collected))
        if start_date and end_date:
            q = q.filter(cls.date_collected.between(start_date, end_date))
        q = q.filter_by(quota=quota_guid).group_by(cls.guid, cls.label)
        return q.all()


class QuotaDataResource(QuotaData):

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


class QuotaResource(Quota):

    def foreign_key_preparer(self, model, start_date=None, end_date=None):
        """ Prepares data from foreign keys """
        data = model.query.filter_by(quota=self.guid)
        if start_date and end_date:
            data = data.filter(
                model.date_collected.between(start_date, end_date))
        data = data.order_by(model.date_collected).all()
        return [item.details() for item in data]

    @staticmethod
    def get_mem_cost(data):
        """ Calculate the cost of services currently contains a
        hard-coded cost for the short-term """
        if data:
            mb_cost = os.getenv('MB_COST_PER_DAY', 0.0033)
            return sum([mem[0] * mem[1] * mb_cost for mem in data])
        return 0

    @staticmethod
    def prepare_memory_data(data):
        """ Given a memory array converts it to a more expressive dict
        [[1875, 14]] -> [{'size': 1875, 'days': 14}] """
        return [{'size': memory[0], 'days': memory[1]} for memory in data]

    @staticmethod
    def prepare_csv_row(row):
        """ Prepares one quota to be exported in a csv row """
        return [
            row.get('name'),
            row.get('guid'),
            str(row.get('cost')),
            str(row.get('created_at')),
        ]

    def details(self):
        """ Displays Quota in dict format """
        return {
            'guid': self.guid,
            'name': self.name,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at)
        }

    def data_details(self, start_date=None, end_date=None):
        """ Displays Quota in dict format with data details """
        memory_data = self.foreign_key_preparer(
            model=QuotaDataResource, start_date=start_date, end_date=end_date)
        services = self.foreign_key_preparer(
            model=ServiceResource, start_date=start_date, end_date=end_date)
        return {
            'guid': self.guid,
            'name': self.name,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'memory': memory_data,
            'services': services
        }

    def data_aggregates(self, start_date=None, end_date=None):
        """ Displays Quota in dict format with data details """
        memory_data = QuotaDataResource.aggregate(
            quota_guid=self.guid, start_date=start_date, end_date=end_date)
        services = ServiceResource.aggregate(
            quota_guid=self.guid, start_date=start_date, end_date=end_date)
        return {
            'guid': self.guid,
            'name': self.name,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'memory': self.prepare_memory_data(memory_data),
            'services': services,
            'cost': self.get_mem_cost(memory_data)
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
    def list_all(cls, start_date=None, end_date=None):
        """ Lists all of the Quota data (This endpoint will be
            refactored later) """
        quotas = cls.query.order_by(cls.guid).all()
        return [
            quota.data_aggregates(start_date=start_date, end_date=end_date)
            for quota in quotas
        ]

    @classmethod
    def generate_cvs(cls, start_date=None, end_date=None):
        """ Return a csv version of the data starting with the header row """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'quota_name', 'quota_guid', 'quota_cost', 'quota_created_date'
        ])
        for row in cls.list_all(start_date=start_date, end_date=end_date):
            writer.writerow(cls.prepare_csv_row(row))
        return output.getvalue()
