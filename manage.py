import os
from subprocess import call

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from quotas_app import app, db
from scripts import load_data
app.config.from_object(os.environ['APP_SETTINGS'])

manager = Manager(app)

# Migration Commands
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def update_database():
    "Updates database with quotas"
    load_data()


@manager.command
def tests():
    """ Run tests """
    test_command = "nosetests --cover-package=CloudFoundry "
    test_command += "--cover-package=models --cover-package=quotas_app "
    test_command += "--cover-package=scripts --with-coverage"
    call([test_command], shell=True)

if __name__ == '__main__':
    manager.run()
