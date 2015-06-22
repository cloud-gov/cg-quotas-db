import os
from subprocess import call

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from quotas import app, db
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
    test_command = "nosetests --cover-package=cloudfoundry "
    test_command += "--cover-package=models --cover-package=quotas "
    test_command += "--cover-package=scripts --with-coverage"
    call([test_command], shell=True)

@manager.command
def build():
    """ Calls out to npm and ensures that the front end is built """
    build_command = "cd ./static && npm install && npm run build"
    call([build_command], shell=True)

if __name__ == '__main__':
    manager.run()
