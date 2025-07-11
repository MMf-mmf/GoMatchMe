# """
# ASGI config for project project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
# """

# import os
# import sys
# from pathlib import Path



# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application

# from chats_app import routing
# from chats_app.middleware import TokenAuthMiddleware


# # If DJANGO_SETTINGS_MODULE is unset, default to the local settings
# BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.local")

# django_asgi_app = get_asgi_application()



# application = ProtocolTypeRouter(
#     {
#         "http": django_asgi_app,
#         "websocket": TokenAuthMiddleware(URLRouter(routing.websocket_urlpatterns)),
#     }
# )