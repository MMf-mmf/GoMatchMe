# some used docker commands

to build and run the docker image
- docker compose up
(use the --build flag to build with no cach data)
to run commands in the docker container
- docker compose exec web python /code/manage.py migrate