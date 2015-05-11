# Quota Database App
Stores Cloud Foundry quotas in database.

## Setup
This project was desgined to work with Python 3

### Install Requirements
```bash
pip install -r requirements.txt
```

### Dev Env Setup
```bash
export APP_SETTINGS="config.DevelopmentConfig"
export DATABASE_URL="sqlite:///dev.db"
export CF_URL="<<Cloud Foundry URL>>"
export CF_USERNAME="<<Username>>"
export CF_PASSWORD="<<Password>>"
export SECRET_KEY="<<Secret Key>>"
```

### Database setup
```bash
# Initalize Database
python manage.py db init
# Migrate Database
python manage.py db migrate
# Apply Migrations
python manage.py db upgrade
# Load Database
python manage.py update_database
```

### Start app
```bash
python manage.py runserver
```
