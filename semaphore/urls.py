import horizon

from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^$', 'semaphore.views.splash', name='splash'),
    url(r'^auth/', include('openstack_auth.urls')),
    url(r'', include(horizon.urls))
)
