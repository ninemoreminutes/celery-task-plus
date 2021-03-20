# Test Project
from . import initialize
initialize()

# Django
from django.core.wsgi import get_wsgi_application  # noqa


application = get_wsgi_application()
