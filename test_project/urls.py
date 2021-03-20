# Python
import re

# Django
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
]

if 'django.contrib.staticfiles' in settings.INSTALLED_APPS and settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    pattern = r'^{}(?P<path>.*)$'.format(re.escape(settings.MEDIA_URL.lstrip('/')))
    kwargs = dict(document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(pattern, serve, kwargs=kwargs),
    ]

if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path(r'__debug__/', include(debug_toolbar.urls)),
    ]
