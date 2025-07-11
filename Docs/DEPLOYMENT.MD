### SETPS NEEDED THAT WEHRE NOT IN VID
- git clone https://<token>@github.com/username/repo.git
- pip install uvicorn



# connecting with aws lightsail instance with ssh
- download the ssh key from the instance page in aws
- once privet ssh key is downloaded make the file read only
```chmod 600 new.pem```
- download the ssh client for vscode
- click on ssh client add add the remote host
```ssh -i /Users/mf/Documents/new_temp_instence.pem ubuntu@3.86.145.115```

Note: the ubuntu@ should be the static ip for the instance if there is one,

- when creating a new key in aws first download the key then create a public key from the private key
```ssh-keygen -y -f new.pem > new.pub```
- if needed the pub key can be added/deleted by going to the authorized_keys file
```nano ~/.ssh/authorized_keys```
- for more reading on creating new key paris 
    ```https://lightsail.aws.amazon.com/ls/docs/en_us/articles/amazon-lightsail-remove-ssh-key-on-instance#add-public-key-to-instance```



## article used to set up Postgres database
- https://towardsdatascience.com/creating-and-connecting-a-postgresql-database-with-amazons-relational-database-service-rds-dcc9db0cd37f


- current nginx config file

```
limit_req_zone $binary_remote_addr zone=ratelimit_zone:10m rate=2r/s;
limit_req_status 429;

upstream gunicorn_server {
  server 127.0.0.1:8000 fail_timeout=0;
}

server {
  listen 80 default_server;
  listen [::]:80 default_server;
  # Rate limiting config
  limit_req zone=ratelimit_zone burst=8 delay=4;
  return 307 https://$host$request_uri;
  if ($host !~* ^(shidduchme.com|staging-shidduchme.com)$ ) {
    return 444;
  }

  location /static/ {
    autoindex on;
    alias /home/ubuntu/PLATEIAS/staticfiles/;
  }
}

server {
  server_name shidduchme.com www.shidduchme.com;
  client_max_body_size 4G;
  access_log /home/ubuntu/logs/nginx-access.log;
  error_log /home/ubuntu/logs/nginx-error.log;

  # line to be edited by sed command in mgt cmd
  set $maintenance off; # edithere
  # SSL configuration
  # ssl_protocols TLSv1.2 TLSv1.3; # duplicated in /etc/letsencrypt/options-ssl-nginx.conf
  # location /ws/ {
  #   proxy_http_version 1.1;
  #   proxy_set_header Upgrade $http_upgrade;
  #   proxy_set_header Connection "upgrade";
  #   proxy_redirect off;
  #   proxy_pass http://ws_server;
  # }

  # Rate limiting configuration
  limit_req zone=ratelimit_zone burst=8 delay=4;

  location / {
    if ($maintenance = on) {
      return 503;
    }
    proxy_read_timeout 3600;
    # an HTTP header important enough to have its own Wikipedia entry:
    #   http://en.wikipedia.org/wiki/X-Forwarded-For
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;


    # enable this if and only if you use HTTPS, this helps Rack
    # set the proper protocol for doing redirects:
    # proxy_set_header X-Forwarded-Proto https;

    # pass the Host: header from the client right along so redirects
    # can be set properly within the Rack application
    proxy_set_header Host $http_host;
    proxy_set_header    X-Forwarded-Proto $scheme;
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
  location /static/ {
    autoindex on;
    alias /home/ubuntu/PLATEIAS/staticfiles/;
  }
}

```


- the current start_gunicorn.bash
```
#!/bin/bash

NAME="PLATEIAS"  # Name of the application
DJANGODIR=/home/ubuntu/PLATEIAS  # Django project directory
DJANGOENVDIR=/home/ubuntu/env  # Django project env
# SOCKFILE=/home/ubuntu/env/run/gunicorn.sock  # communicate using this unix socket
#   --bind=unix:$SOCKFILE \ # instead of bind=0.0.0:8000
USER=ubuntu  # the user to run as
GROUP=ubuntu  # the group to run as
NUM_WORKERS=$((2 * $(nproc) + 1))  # Dynamically calculate based on CPU cores, 
DJANGO_WSGI_MODULE=project.wsgi  # WSGI module name
TIMEOUT=10000 # Workers silent for more than this many seconds are killed and restarted.

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source /home/ubuntu/env/bin/activate
source /home/ubuntu/PLATEIAS/.env
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
  --bind=0.0.0.0:8000 \
  --log-level=debug \
  --timeout $TIMEOUT
```