# Question Bank Manager

## 1. Creating a Python Virtual Environment

```python
python -m venv venv
```

or

```python
python -m venv venv
```

## 2. Activate Virtual Environment

```bash
venv/Scripts/Activate.ps1
```

or

```bash
source venv/bin/acivate
```

## 3. Install Required Python Packages
Inside an activated virtual environment, run the following command:

```bash
pip install -r requirements.txt
```

## 4. Generating a SECRET_KEY

The app reads `SECRET_KEY` from the environment (local `.env` file) and refuses to
start if it is missing. Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then paste the printed value as `SECRET_KEY=<value>` in your local `.env` file
(`.env.example` intentionally keeps the `SECRET_KEY=change-me` placeholder).

Production needs its own separately-generated key — never reuse the local dev key
on the server.

## DATABASE MIGRATION

1. **Commands to run on the other local servers and remote server**

*With the virtual environment activated*

```bash
export FLASK_APP=app.py
flask db upgrade
```

**Important Note**: Setting `export FLASK_APP=app.py` explicitly is mandatory here if you do not want to create `.fleskenv` file on the server. To be on the safe side while running flask commands, you can create a .flaskenv file special for remote server just to run the flask commands on remote server. Then you do not need to run `export FLASK_APP=app.py` command.

```bash
touch .flaskenv
```

That flask command creates `instance/app.db` on the server with **all four tables**.

2. **Seeding is optional**. Do it only if you want the sample database information that has been locally generated on remote website (perhaps for testing). Note that there is a guard that refuses `seed-db` command to run on a non-empty database.

```bash
flask seed-db
```

## DEPLOYMENT

### Project Deployment to Plesk VPS (with nginx as Web Server, Phusion Passenger as Application Server)

1. `wsgi.py` file content

```python
import sys
import os

# Set the project root directory
project_home = os.path.dirname(__file__)
sys.path.insert(0, project_home)

# Set Python interpreter to your venv
INTERP = os.path.join(project_home, "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Import the app factory and create the application instance
from app import create_app

application = create_app()
```

2. `Domain > Hosting & DNS > Apache & nginx > Disable Proxy Mode`
3. `Domain > Hosting & DNS > Apache & nginx > Additional nginx Directives`

```text
passenger_enabled on;
passenger_app_type wsgi;
passenger_startup_file wsgi.py;
passenger_app_root /var/www/vhosts/example.com/subdomain.example.com;
passenger_python /var/www/vhosts/example.com/subdomain.example.com/venv/bin/python;
```

4. On remote server run the following command to create virtual environment. (Mandatory not to mess with the system python)

```bash
python -m venv venv
```

5. Activate the virtual environment.

```bash
source venv/bin/activate
```

6. With the virtual environment activated, run the following command to install the necessary Python packages. (Necessary packages are listed in `requirements.txt` file)

```bash
pip install -r requirements.txt
```

7. After a new update (for example there is an update on local dev environment) run the following command on remote server to restart the application server

```bash
git pull
touch tmp/restart.txt
```