from .base import *
import os


DEBUG = False
SITE_ID = 1

ALLOWED_HOSTS = ["shidduchme.com", "www.shidduchme.com", "mendel.shidduchme.com", "www.mendel.shidduchme.com"]
#  "localhost", "0.0.0.0", "127.0.0.1", 'mendel.localhost'


INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True


# CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672//' # this is the default only changed if needed
# TODO: ADD BACK IN WHEN S3 BUCKET IS CONFIGURED
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME_LOCAL')


SECRET_KEY = env("DJANGO_SECRET_KEY")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY_PRODUCTION")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET_PRODUCTION")
STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID = env("STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID_PRODUCTION")
STRIPE_BOUNTY_PRODUCT_ID = env("STRIPE_BOUNTY_PRODUCT_ID_PRODUCTION")
SUGGESTION_PRODUCT_ID = env("SUGGESTION_PRODUCT_ID_PRODUCTION")
BOUNTY_SUBSCRIPTION_PRICE_ID = env("BOUNTY_SUBSCRIPTION_PRICE_ID_PRODUCTION")
BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID = env("BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID_PRODUCTION")
# STRIPE_ONE_DOLLAR_SUGGESTION_PRICE_ID = env("STRIPE_ONE_DOLLAR_SUGGESTION_PRICE_ID_PRODUCTION")
STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID = env("STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID_PRODUCTION")
STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID = env("STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID_PRODUCTION")
DONATION_SUBSCRIPTION_PRODUCT_ID = env("DONATION_SUBSCRIPTION_PRODUCT_ID_PRODUCTION")
DONATION_ONE_TIME_SUBSCRIPTION_PRICE_ID = env("DONATION_ONE_TIME_SUBSCRIPTION_PRICE_ID_PRODUCTION")

MAIL_GUN_API_KEY = env("MAIL_GUN_API_KEY")
REDIS_HOST = env("REDIS_HOST")


TIER_1_SUGGESTION_DURATION = 5  # 5
TIER_2_SUGGESTION_DURATION = 8  # 8
TIER_3_SUGGESTION_DURATION = 12  # 12
# Check if the environment variables are set
if (
    not BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID
    or not BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID
    or not SECRET_KEY
    or not STRIPE_SECRET_KEY
    or not AWS_ACCESS_KEY_ID
    or not AWS_SECRET_ACCESS_KEY
    or not AWS_STORAGE_BUCKET_NAME
    or not AWS_S3_REGION_NAME
    or not STRIPE_BOUNTY_PRODUCT_ID
    or not STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID
    or not SUGGESTION_PRODUCT_ID
    or not STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID
    or not STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID
    or not DONATION_SUBSCRIPTION_PRODUCT_ID
    or not MAIL_GUN_API_KEY
    or not REDIS_HOST
):
    raise ValueError("Please set all the required environment variables.")

MIDDLEWARE = [
    "django_hosts.middleware.HostsRequestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    # 'simple_history.middleware.HistoryRequestMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware
    "accounts_app.middleware.ProfileCompletionMiddleware",  # make sure the users profile is complete
    # must be last
    "django_hosts.middleware.HostsResponseMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME"),
        "USER": os.environ.get("DATABASE_USER"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
        "HOST": os.environ.get("DATABASE_HOST"),
        "PORT": 5432,
    }
}
# print("--------------------------")
# print("DATABASES", DATABASES)
# print("--------------------------")
ANYMAIL = {
    "MAILGUN_API_KEY": MAIL_GUN_API_KEY,
    "MAILGUN_SENDER_DOMAIN": "shidduchme.com",
}


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, env.int("REDIS_PORT"))],
        },
    },
}


# Sentry configuration
SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
