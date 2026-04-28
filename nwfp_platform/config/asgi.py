"""
ASGI config for Bhutan NWFP Digital Marketplace & Management Platform.

It exposes the ASGI callable as a module-level variable named ``application``.

Currently configured for standard HTTP only.  If WebSocket support is added
in the future (e.g. via Django Channels), update this file to route the
``websocket`` protocol to the appropriate ASGI application.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_asgi_application()
