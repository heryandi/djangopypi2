import logging
import urlparse
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.static import serve as static_serve
from django.contrib import admin
from django.contrib.auth.views import logout
admin.autodiscover()

log = logging.getLogger(__name__)

def static_urls():
    '''Returns urls for for static file serving from this server. In case
    the STATIC_URL points to an absolute server, we don't serve static
    files from this server.
    '''
    parsed_url = urlparse.urlparse(settings.STATIC_URL)
    if parsed_url.netloc:
        log.debug('Cannot serve STATIC files since settings.STATIC_URL points outside this server.')
        return patterns('')
    return patterns('',
                    url(r'^' + settings.STATIC_URL.strip('/') + r'/(?P<path>.*)$',
                        static_serve, dict(document_root=settings.STATIC_ROOT)),
                    url(r'^' + settings.MEDIA_URL.strip('/') + r'/(?P<path>.*)$',
                        static_serve, dict(document_root=settings.MEDIA_ROOT)),
                    )

urlpatterns = patterns('',
    url(r'^' + (settings.USER_SETTINGS['WEB_ROOT'].strip('/') + r'/'      ).lstrip('/'), include('djangopypi2.urls')),
    url(r'^' + (settings.USER_SETTINGS['WEB_ROOT'].strip('/') + r'/admin/').lstrip('/'), include(admin.site.urls)),
    url(r'^' + (settings.USER_SETTINGS['WEB_ROOT'].strip('/') + r'/accounts/').lstrip('/'), include('allauth.urls')),
) + static_urls()
