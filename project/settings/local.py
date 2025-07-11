from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "mendel.localhost", "172.20.10.12"]
# the email must be a verified with sendgrid for it to work
CORS_ALLOW_ALL_ORIGINS = True
# SECRET_KEY is loaded from environment variables below

THIRD_PARTY_APPS += [
    "debug_toolbar",
]
INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS
# STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY_TEST')
# STRIPE_API_VERSION = '2022-11-15'
# STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET_TEST')
# STRIPE_BOUNTY_PRODUCT_ID = env('STRIPE_BOUNTY_PRODUCT_ID_TEST')
# STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID = env('STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID_TEST')


SECRET_KEY = env("DJANGO_SECRET_KEY")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY_TEST")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET_TEST")
STRIPE_BOUNTY_PRODUCT_ID = env("STRIPE_BOUNTY_PRODUCT_ID")
STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID = env("STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID")
BOUNTY_SUBSCRIPTION_PRICE_ID = env("BOUNTY_SUBSCRIPTION_PRICE_ID_TEST")
# BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID = env("BOUNTY_ONE_TIME_SUBSCRIPTION_PRICE_ID_TEST")

SUGGESTION_PRODUCT_ID = env("SUGGESTION_PRODUCT_ID")
STRIPE_ONE_DOLLAR_SUGGESTION_PRICE_ID = env("STRIPE_ONE_DOLLAR_SUGGESTION_PRICE_ID")
STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID = env("STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID")
STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID = env("STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID")
DONATION_SUBSCRIPTION_PRODUCT_ID = env("DONATION_SUBSCRIPTION_PRODUCT_ID")
DONATION_ONE_TIME_SUBSCRIPTION_PRICE_ID = env("DONATION_ONE_TIME_SUBSCRIPTION_PRICE_ID")
MAIL_GUN_API_KEY = env("MAIL_GUN_API_KEY")
REDIS_HOST = env("REDIS_HOST")

# Check if the environment variables are set
if (
    not SECRET_KEY
    or not STRIPE_SECRET_KEY
    or not AWS_ACCESS_KEY_ID
    or not AWS_SECRET_ACCESS_KEY
    or not AWS_STORAGE_BUCKET_NAME
    or not AWS_S3_REGION_NAME
    or not STRIPE_BOUNTY_PRODUCT_ID
    or not STRIPE_BOUNTY_ONE_TIME_BOUNTY_PRODUCT_ID
    or not SUGGESTION_PRODUCT_ID
    or not STRIPE_ONE_DOLLAR_SUGGESTION_PRICE_ID
    or not STRIPE_FIVE_DOLLAR_SUGGESTION_PRICE_ID
    or not STRIPE_FIFTEEN_DOLLAR_SUGGESTION_PRICE_ID
    or not DONATION_SUBSCRIPTION_PRODUCT_ID
    or not MAIL_GUN_API_KEY
    or not REDIS_HOST
):
    raise ValueError("Please set all the required environment variables.")

ANYMAIL = {
    "MAILGUN_API_KEY": MAIL_GUN_API_KEY,
    # "MAILGUN_SENDER_DOMAIN": "sandbox845a9e9e62a74900b337f34fe506fa41.mailgun.org",
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
# Dynamic NPM binary path detection
import subprocess

try:
    # Use subprocess to find the npm binary path
    npm_bin_path_result = subprocess.run(["which", "npm"], capture_output=True, text=True)

    # Check if the command was successful
    if npm_bin_path_result.returncode == 0:
        NPM_BIN_PATH = npm_bin_path_result.stdout.strip()
    else:
        raise EnvironmentError("npm binary could not be found. Please ensure npm is installed and in your PATH.")
except Exception as e:
    # Fallback to common npm locations
    import os

    common_npm_paths = [
        "/usr/local/bin/npm",
        "/usr/bin/npm",
        "/opt/homebrew/bin/npm",
    ]

    NPM_BIN_PATH = None
    for path in common_npm_paths:
        if os.path.exists(path):
            NPM_BIN_PATH = path
            break

    if not NPM_BIN_PATH:
        raise EnvironmentError(
            f"npm binary could not be found. Please ensure npm is installed and in your PATH. Error: {e}"
        )

INTERNAL_IPS = [
    "127.0.0.1",
    "mendel.localhost",
]

MIDDLEWARE = [
    "django_hosts.middleware.HostsRequestMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
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
# LOCAL DATABASE
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DEVELOPMENT_DATABASE_NAME"),
        "USER": env("DEVELOPMENT_DATABASE_USER"),
        "PASSWORD": env("DEVELOPMENT_DATABASE_PASSWORD"),
    }
}


DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    # 'debug_toolbar.panels.history.HistoryPanel',
    # 'debug_toolbar.panels.versions.VersionsPanel',
    # 'debug_toolbar.panels.timer.TimerPanel',
    # 'debug_toolbar.panels.settings.SettingsPanel',
    # 'debug_toolbar.panels.headers.HeadersPanel',
    # 'debug_toolbar.panels.signals.SignalsPanel',
    # 'debug_toolbar.panels.redirects.RedirectsPanel',
    # 'debug_toolbar.panels.profiling.ProfilingPanel',
]
# HOSTED_STAGING_DATABASE
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get("STAGING_DATABASE_NAME"),
#         'USER': os.environ.get("STAGING_DATABASE_USER"),
#         'PASSWORD': os.environ.get("STAGING_DATABASE_PASSWORD"),
#         'HOST': os.environ.get("STAGING_DATABASE_HOST"),
#         'PORT': 5432,
#         # 'CONN_MAX_AGE': None,
#     }
# }

# PRODUCTION DATABASE
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ.get("DATABASE_NAME"),
#         "USER": os.environ.get("DATABASE_USER"),
#         "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
#         "HOST": os.environ.get("DATABASE_HOST"),
#         "PORT": 5432,
#     }
# }
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME_LOCAL')

SITE_ID = 1

# adjust values for testing
TIER_1_SUGGESTION_DURATION = 333  # 5
TIER_2_SUGGESTION_DURATION = 333  # 8
TIER_3_SUGGESTION_DURATION = 333  # 12
