## COMMONLY USED COMMANDS

to run server

- python3 manage.py runserver --settings=project.settings.local

set in environment for macOS

- export DJANGO_SETTINGS_MODULE="project.settings.local"
  set in environment for windows
- set DJANGO_SETTINGS_MODULE=project.settings.local
  set in PowerShell
- $env:DJANGO_SETTINGS_MODULE="project.settings.local"
  check environment
- echo $env:DJANGO_SETTINGS_MODULE
 
### CHANGE THE COMMAND RUN
- export DJANGO_SETTINGS_MODULE=project.settings.local ; python3 manage.py runserver                     
---

## tailwind

install tailwind

- npm install -D tailwindcss
- npx tailwindcss init
- run tailwind on set up
- npm run tailwind-watch
- npm run tailwind-build
## Compile React code / webpack
- npm run dev

## Docker
- docker run -it --rm --name redis -p 6379:6379 redis  # run redis
## redis
 check if redis is running
- redis-cli ping (should return "PONG" if running)

## deployment
IN THE WSGI AND ASGI FILES CHANGE THE SETTINGS FROM LOCAL TO !!!PRODUCTION!!!

## STRIPE
#### run webhook routing in development run the following commands in a new terminal window
if not already installed 
   - brew install stripe/stripe-cli/stripe
if not already logged in (will stay logged in for 90 days) from last login
   - stripe login
- stripe listen --forward-to http://127.0.0.1:8000/payments/stripe_webhooks/
<!-- Result Test Credit Card CVC Expiry date
Successful payment 4242 4242 4242 4242 Any 3 digits Any future date
Failed payment 4000 0000 0000 0002 Any 3 digits Any future date
Number: for indices/subscription that will fail when charged
4000 0000 0000 0341.
4000 0025 0000 3155 Any 3 digits Any future dat -->
## links for deployment
- https://www.youtube.com/watch?v=d7HU_jdzz7A
  - https://github.com/LondonAppDeveloper/tutorial-django-aws-lightsail
- https://django.how/resources/django-deployment-aws-lightsail/




## Links used during development
https://lightsail.aws.amazon.com/ls/docs/en_us/articles/amazon-lightsail-install-software
https://github.com/99designs/aws-vault
https://lightsail.aws.amazon.com/ls/docs/en_us/articles/amazon-lightsail-ssh-using-terminal



## email servers
- https://app.mailgun.com/dashboard?tab=send
we set up our domain with mailgun and have a free account which means we must first add the email we want to send to in order to send the emails.
and the account is running on the sandbox domain when we go to a paid plan we can use the real domain as sender and send to however we want.



## Stripe

### Non coding configuration
- when we create a Production stripe account we need to create 5 products
    the names and descriptions should be the same 
   - Bounty Payment (One Time)
   - Bounty Payment (Recurring)
   - Suggestion Payment
   - Donation Payment
   - Pledge Fulfillment (Match Made!)



  
  # other services in use
  <!-- rabbitmq, run it locally with the following command
  - docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13.7-management -->
  - https://docs.celeryq.dev/en/latest/getting-started/backends-and-brokers/redis.html#broker-redis
  celery 
  - celery -A project worker -l info
  manage celery with flower
  - celery -A project flower
  add authentication to flower
  - celery -A project flower --basic-auth=UsernameHere:PasswordHere