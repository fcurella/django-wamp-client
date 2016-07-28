from django.conf import settings


WAMP_CONNECTION = getattr(settings, 'WAMP_CONNECTION', {})
