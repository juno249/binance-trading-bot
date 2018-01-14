import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_core.settings")

from django.core.wsgi import get_wsgi_application
from channels.asgi import get_channel_layer

application = get_wsgi_application()
channel_layer = get_channel_layer()
