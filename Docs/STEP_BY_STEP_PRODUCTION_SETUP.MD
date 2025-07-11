## STEP BY STEP SET UP GUIDE TO SET UP A PRODUCTION SERVER IN DJANGO ON A UBUNTU SERVER 
UPDATE THE NEW SERVER TO THE LATEST VERSIONS
-  sudo apt-get update

UPGRADE THE PACKAGES
- sudo apt-get upgrade

CHECK THE PYTHON VERSION
-  python3 --version

UPGRADE PYTHON TO THE LATEST VERSION
- sudo add-apt-repository ppa:deadsnakes/ppa
- sudo apt-get update
- sudo apt-get install python3.12
- sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
- python3 --version
- https://cloudbytes.dev/snippets/upgrade-python-to-latest-version-on-ubuntu-linux

INSTALL THE PYTHON VENV PACKAGE
- sudo apt-get install python3-venv

CREATE A DIRECTORY FOR THE PROJECT
- mkdir webapp

NAVIGATE TO THE DIRECTORYsudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
- cd webapp

CREATE THE VIRTUAL ENVIROMENT
- python3 -m venv myenv 

ACTIVATE THE VIRTUAL ENVIROMENT
- source myenv/bin/activate

UPDATE PIP
- pip install -U pip

CLONE THE GITHUB REPO (make sure not to include the branch just point directly to the repo such as git ''' clone https://aZQo8QL8pWg42BBt@github.com/MMf-mmf/PLATEIAS.git  ''') 
VID LINK ON HOW TO OBTAIN A TOKEN ( https://www.youtube.com/watch?v=iLrywUfs7yU )
- git clone https://<token>@github.com/username/repo.git

PIP INSTALL THE REQUIREMENTS FROM THE PROJECTS .TXT FILE ( make sure that gunicorn and othere needed packages are in the requirements file)
- pip install -r project/requirements/production.txt

INSTALL NGINX
- sudo apt-get install -y nginx

CREATE A start_gunicorn.bash file in the webapp directory
- touch start_gunicorn.bash

- add the below code to the start_gunicorn.bash file
```
#!/bin/bash

NAME="dbr"  # Name of the application
DJANGODIR=/home/ubuntu/webapp/dbr/proj  # Django project directory
DJANGOENVDIR=/home/ubuntu/webapp/dbrenv  # Django project env
SOCKFILE=/home/ubuntu/webapp/dbrenv/run/gunicorn.sock  # communicate using this unix socket
USER=ubuntu  # the user to run as
GROUP=ubuntu  # the group to run as
NUM_WORKERS=8  # how many worker processes should Gunicorn spawn (2 * lsCPUs + 1)
DJANGO_WSGI_MODULE=proj.wsgi  # WSGI module name
TIMEOUT=30000 # Workers silent for more than this many seconds are killed and restarted.

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source /home/ubuntu/webapp/dbrenv/bin/activate
source /home/ubuntu/webapp/dbr/proj/.env
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ${DJANGOENVDIR}/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --timeout $TIMEOUT

```


MAKE THE start_gunicorn.bash FILE EXECUTABLE
- chmod +x start_gunicorn.bash


CREATE THE  push_updates.bash FILE
- touch push_updates.bash
- add the below code to the push_updates.bash file
```
# cd webapp/dbr/proj/
# git pull
source /home/ubuntu/webapp/dbrenv/bin/activate
pip install --upgrade -r requirements/prod.txt
export DJANGO_SETTINGS_MODULE=proj.settings.prod
source /home/ubuntu/webapp/dbr/proj/.env
python manage.py collectstatic --noinput
python manage.py migrate
sudo supervisorctl restart gunicorn
sudo supervisorctl restart huey
```
CREATE THE .env FILE
- touch .env

INTALL SUPERVISOR
- sudo apt-get install supervisor

NOW ALLOW SUPERVISOR TO RUN IN THE BACKGROUND
NAVIGATE TO THE SUPERVISOR DIRECTORY
- cd /etc/supervisor/conf.d

CREATE THE SUPERVISOR CONFIG FILE
- sudo touch gunicorn.conf
- add the below gunicorn config
```
; ================================
;  gunicorn supervisor
; ================================

[program:gunicorn]
command = /home/ubuntu/webapp/start_gunicorn.bash  ; Command to start app
user = ubuntu   ; User to run as
redirect_stderr = true
stdout_logfile = /home/ubuntu/webapp/logs/gunicorn/access.log  ; Where to write access log messages
stderr_logfile = /home/ubuntu/webapp/logs/gunicorn/error.log  ; Where to write error log messages
stdout_logfile_maxbytes = 50MB
stderr_logfile_maxbytes = 50MB
stdout_logfile_backups = 10
stderr_logfile_backups = 10
environment = LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8  ; Set UTF-8 as default encoding
```

NAVIGATE TO THE WEBAPP DIRECTORY AND CREATE THE LOGS DIRECTORY WITH THE ACCESS AND ERROR LOGS FILES
- sudo mkdir -p logs/gunicorn

CONFIRM THE SUPERVISOR CONFIG IS OK
- sudo supervisorctl reread

ADD THE GUNICORN TO SUPERVISOR
- sudo supervisorctl update

CHECK THE STATUS OF THE SUPERVISOR (should see  RUNNING  as part of the response, if the gunicorn file was set up correctly (gunicorn  RUNNING   pid 58538, uptime 0:00:19))
- sudo supervisorctl status

NAVIGATE TO THE NGINX DIRECTORY
- cd /etc/nginx
EDIT THE NGINX CONFIG FILE TO BE THE ROOT USER, (the first line for the config file)
- sudo nano nginx.conf
```user root;```
NOW CONFIGURE THE NGINX CONFIG FILE IN THE SITE-AVAILABLE DIRECTORY
- cd sites-available
- sudo touch dbr.conf
- add the below config to the dbr.conf file (edit the project name as needed)
```
# rate limiting config
limit_req_zone $binary_remote_addr zone=ratelimit_zone:10m rate=2r/s;
limit_req_status 429;


upstream ws_server {
  server unix:/home/ubuntu/webapp/dbrenv/run/daphne.sock fail_timeout=0;
}

upstream gunicorn_server {
  # fail_timeout=0 means we always retry an upstream even if it failed
  # to return a good HTTP response (in case the Unicorn master nukes a
  # single worker for timing out).
  server unix:/home/ubuntu/webapp/dbrenv/run/gunicorn.sock fail_timeout=0;
}

server {
  listen 80 default_server;
  listen [::]:80 default_server;
  return             307 https://$host$request_uri;
  # Rate limiting config
  limit_req zone=ratelimit_zone burst=8 delay=4;

  if ($host !~* ^(dbr.palletfly.com|vendor.palletfly.com|hello.palletfly.com)$ ) {
    return 444;
  }

}

server {
  server_name dbr.palletfly.com vendor.palletfly.com hello.palletfly.com;
  client_max_body_size 4G;
  access_log /home/ubuntu/webapp/logs/nginx-access.log;
  error_log /home/ubuntu/webapp/logs/nginx-error.log;

  # line to be edited by sed command in mgt cmd
  set $maintenance off; # edithere

  location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_redirect off;
    proxy_pass http://ws_server;
  }

  location / {
    if ($maintenance = on) {
      return 503;
    }

    # an HTTP header important enough to have its own Wikipedia entry:
    #   http://en.wikipedia.org/wiki/X-Forwarded-For
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;


  
    proxy_set_header    X-Forwarded-Proto $scheme;

    # pass the Host: header from the client right along so redirects
    # can be set properly within the Rack application
        proxy_set_header Host $http_host;

    # we don't want nginx trying to do something clever with
    # redirects, we set the Host: header above already.
    proxy_redirect off;

    # set "proxy_buffering off" *only* for Rainbows! when doing
    # Comet/long-poll stuff.  It's also safe to set if you're
    # using only serving fast clients with Unicorn + nginx.
    # Otherwise you _want_ nginx to buffer responses to slow
    # clients, really.
    # proxy_buffering off;

    # Try to serve static files from nginx, no point in making an
    # *application* server like Unicorn/Rainbows! serve static files.
    if (!-f $request_filename) {
        proxy_pass http://gunicorn_server;
        break;
    }
  }


}
```

TEST TO SEE IF THE NGINX CONFIG FILE IS OK
- sudo nginx -t
CREATE A SYMLINK TO THE SITES-ENABLED DIRECTORY
- sudo ln -s /etc/nginx/sites-available/shidduchMe.conf /etc/nginx/sites-enabled/
INTALL CERTBOT FOR SSL CERTIFICATES
- sudo snap install --classic certbot
-  sudo certbot --nginx --rsa-key-size 4096 --no-redirect
NOW RESTART NGINX
- sudo systemctl restart nginx



### SETPS NEEDED THAT WEHRE NOT IN VID
- pip install uvicorn


## to connect ssh from your local terminal
- ssh -i /Users/mf/Documents/LightsailDefaultKey-us-east-1.pem ubuntu@184.72.252.150


### you might need to access the link a github account again if it gets disconnected use
- git remote set-url origin https://<token>@github.com/MMF-mmf/PLATEIAS