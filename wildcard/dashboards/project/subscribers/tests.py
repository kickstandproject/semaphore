# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django import http

from mox import IsA

from wildcard import api
from wildcard.dashboards.project.subscribers import forms
from wildcard.dashboards.project.subscribers import tables
from wildcard.test import helpers as test


INDEX_URL = reverse('horizon:project:subscribers:index')
CREATE_URL = reverse('horizon:project:subscribers:create')
UPDATE_URL = reverse('horizon:project:subscribers:update', args=[1])


def extract_data(subscriber):
    fields = [
        'username',
        'password',
        'domain_id',
        'email_address',
        'rpid',
    ]
    return {f: getattr(subscriber, f) for f in fields}


class SubscriberTests(test.TestCase):

    @test.create_stubs({api.ripcord: ('subscriber_list', 'domain_list')})
    def test_index(self):
        api.ripcord.subscriber_list(
            IsA(http.HttpRequest)
        ).AndReturn(self.subscribers.list())
        api.ripcord.domain_list(
            IsA(http.HttpRequest)
        ).AndReturn(self.project_domains.list())
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/subscribers/index.html')
        subscribers = res.context['subscribers_table'].data
        self.assertItemsEqual(subscribers, self.subscribers.list())

    def _test_create_successful(self, subscriber, create_args, post_data):
        api.ripcord.domain_list(
            IsA(http.HttpRequest)
        ).AndReturn(self.project_domains.list())
        api.ripcord.subscriber_create(
            IsA(http.HttpRequest),
            **create_args
        ).AndReturn(subscriber)
        self.mox.ReplayAll()

        post_data['method'] = 'CreateSubscriberForm'
        res = self.client.post(CREATE_URL, post_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    def _test_update_successful(self, subscriber, update_args, post_data):
        api.ripcord.subscriber_get(
            IsA(http.HttpRequest),
            subscriber.uuid,
        ).AndReturn(subscriber)
        api.ripcord.domain_list(
            IsA(http.HttpRequest)
        ).AndReturn(self.project_domains.list())
        api.ripcord.subscriber_update(
            IsA(http.HttpRequest),
            subscriber.uuid,
            **update_args
        ).AndReturn(None)
        self.mox.ReplayAll()

        post_data['method'] = 'UpdateSubscriberForm'
        res = self.client.post(UPDATE_URL, post_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.ripcord: ('subscriber_create', 'domain_list')})
    def test_create(self):
        subscriber = self.subscribers.get(uuid='1')
        post_data = extract_data(subscriber)
        self._test_create_successful(
            subscriber,
            extract_data(subscriber),
            post_data,
        )

    @test.create_stubs({
        api.ripcord: ('subscriber_get', 'subscriber_update', 'domain_list'),
    })
    def test_update(self):
        subscriber = self.subscribers.get(uuid='1')
        post_data = extract_data(subscriber)
        post_data['uuid'] = subscriber.uuid
        self._test_update_successful(
            subscriber,
            extract_data(subscriber),
            post_data,
        )

    @test.create_stubs({api.ripcord: ('subscriber_delete', 'subscriber_list')})
    def test_delete(self):
        uuid = '1'
        api.ripcord.subscriber_delete(
            IsA(http.HttpRequest),
            uuid,
        )
        api.ripcord.subscriber_list(
            IsA(http.HttpRequest),
        ).AndReturn(self.subscribers.list())
        self.mox.ReplayAll()

        form_data = {'action': 'subscribers__delete__%s' % uuid}
        res = self.client.post(INDEX_URL, form_data)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.ripcord: ('subscriber_update', 'subscriber_list')})
    def test_enable_subscriber(self):
        subscriber = self.subscribers.get(uuid='1')
        subscriber.disabled = True

        api.ripcord.subscriber_list(
            IsA(http.HttpRequest),
        ).AndReturn(self.subscribers.list())
        api.ripcord.subscriber_update(
            IsA(http.HttpRequest),
            subscriber.uuid,
            disabled=False
        ).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'action': 'subscribers__toggle__%s' % subscriber.uuid}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.ripcord: ('subscriber_update', 'subscriber_list')})
    def test_disable_subscriber(self):
        subscriber = self.subscribers.get(uuid="1")
        subscriber.disabled = False

        api.ripcord.subscriber_list(
            IsA(http.HttpRequest),
        ).AndReturn(self.subscribers.list())
        api.ripcord.subscriber_update(
            IsA(http.HttpRequest),
            subscriber.uuid,
            disabled=True
        ).AndReturn(None)

        self.mox.ReplayAll()

        formData = {'action': 'subscribers__toggle__%s' % subscriber.uuid}
        res = self.client.post(INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_object_display(self):
        subscriber = self.subscribers.get(uuid="1")
        table = tables.SubscribersTable(self.request, [subscriber])
        object_display = table.get_object_display(subscriber)
        self.assertEquals(object_display, subscriber.username)


class TextInputWithGenerator(test.TestCase):

    def test_render(self):
        w = forms.TextInputWithGenerator()
        self.assertHTMLEqual(
            w.render('test', 'test123'),
            '<div class="input-with-button">'
            '<input name="test" type="text" value="test123" />'
            '<a class="btn pull-right" data-chars="%s" data-length="%s">'
            'Generate</a>'
            '</div>' % (
                settings.KICKSTAND_RANDOM_PASSWORD_CHARS,
                settings.KICKSTAND_RANDOM_PASSWORD_LENGTH
            )
        )
