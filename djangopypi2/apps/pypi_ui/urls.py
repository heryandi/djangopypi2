from urlparse import urljoin
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^favicon\.ico$', lambda request: HttpResponseRedirect(urljoin(settings.STATIC_URL, 'favicon.ico'))),
    url(r'^guide/$', TemplateView.as_view(template_name="pypi_ui/guide.html"), name='djangopypi2-guide'),
)
