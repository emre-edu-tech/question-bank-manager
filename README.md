# Question Bank Manager

## Project Deployment to Plesk VPS (with nginx as Web Server, Phusion Passenger as Application Server)
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

7. After a new update run the following command to restart the application server

```bash
git pull
touch tmp/restart.txt
```