import os
import json


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY', "None")
    USERNAME = os.environ.get('SECRET_USERNAME', 'admin')
    PASSWORD = os.environ.get('SECRET_PASSWORD', 'admin')
    # Database
    CF_SERVICES = os.getenv('VCAP_SERVICES')
    if CF_SERVICES:
        CF_SERVICES = json.loads(CF_SERVICES)
        SQLALCHEMY_DATABASE_URI = CF_SERVICES['rds'][0]['credentials']['uri']
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
