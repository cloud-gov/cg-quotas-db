import os

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from quotas import app, db
from scripts import load_quotas
app.config.from_object(os.environ['APP_SETTINGS'])

manager = Manager(app)

# Migration Commands
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def update_database():
    "Updates database with quotas"
    load_quotas()

if __name__ == '__main__':
    manager.run()
