# Quota Database App
There are two distinct components that form the basis of this repository. At some point in the future we might split them out, for now they are going to stay together.

0. Flask API for storing Cloud Foundry quotas data
0. Backbone app for front end views

## Setup the Flask API
This project was designed to work with Python 3

### Install Requirements
```
pip install -r requirements.txt
```

### Dev Env Setup
```
export APP_SETTINGS="config.DevelopmentConfig"
export DATABASE_URL="sqlite:///dev.db"
export CF_API_URL="<<Cloud Foundry API URL>>"
export CF_UAA_URL="<<Cloud Foundry UAA URL>>"
export CF_USERNAME="<<Username>>"
export CF_PASSWORD="<<Password>>"
export SECRET_KEY="<<Secret Key>>"
```

### Database setup
```
# Initalize Database
python manage.py db init
# Migrate Database
python manage.py db migrate
# Apply Migrations
python manage.py db upgrade
# Load Database
python manage.py update_database
```

### Testing
Install the dev requirements

```
pip install -r requirements-dev.txt
```

Run the tests

```
python manage.py tests
```

### Building the front end

```
# Have npm install dependencies and build front end
python manage.py build
```

### Start app for dev

```
export APP_SETTINGS="config.DevelopmentConfig"
python manage.py build
python manage.py runserver
```

### Cloud Foundry
```
cf push
```

### Authentication
This app uses HTTP Basic Authentication. Passwords can be set using the `SECRET_USERNAME` and `SECRET_PASSWORD` env variables. The default username and password for testing are:
password: `admin`
username: `admin`

## Getting started with front end development
This is a browserify built app and uses Backbone as its basic framework. It lives within the `static` directory at the project root.

### Install Requirements
This is Javascript land, so you can just run `npm install` from within the project root directory.

### Start app for dev
You should be able to start the build process with `npm start`. If you want to build once and not re-trigger builds on file changes then you can use `npm run build`. This can be useful for deployment.

Once you've got both the python app running and you've set up `npm start` to rebuild on file changes, you can just go to [http://127.0.0.1:5000](http://127.0.0.1:5000)


## API

#### Quotas
- List quotas: `/api/quotas/`
- Individual quota details: `/api/quotas/:guid/`

##### Parameters
`since` and `until` - define the range for collected memory and services stats. The format for these arguments is `YYYY-MM-DD`.
If the `until` parameter is not present the date will default to the current date UTC.

Examples
- ex. `/api/quotas/?since=2013-01-01`
- ex. `/api/quotas/:guid/?since=2013-01-01&until=2014-01-01`
