"""
ASGI config for main project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/
"""

import os

import django
from .wsgi import *
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

import notification.routing
import knowledge_management_system.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

django.setup()

application = get_asgi_application()

application = ProtocolTypeRouter({
    'http': application,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            # Add your ASGI url_patterns here
            notification.routing.websocket_urlpatterns +
            knowledge_management_system.routing.websocket_urlpatterns
        )
    ),
})
