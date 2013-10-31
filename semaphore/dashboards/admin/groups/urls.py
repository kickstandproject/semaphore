# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf.urls.defaults import patterns  # noqa
from django.conf.urls.defaults import url  # noqa

from semaphore.dashboards.admin.groups import views


urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<group_id>[^/]+)/update/$',
        views.UpdateView.as_view(), name='update'),
    url(r'^(?P<group_id>[^/]+)/manage_members/$',
        views.ManageMembersView.as_view(), name='manage_members'),
    url(r'^(?P<group_id>[^/]+)/add_members/$',
        views.NonMembersView.as_view(), name='add_members'),
)
