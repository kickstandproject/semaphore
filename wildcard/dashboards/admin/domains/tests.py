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


from django.core.urlresolvers import reverse  # noqa
from django import http

from mox import IgnoreArg  # noqa
from mox import IsA  # noqa

from horizon.workflows import views

from wildcard import api
from wildcard.test import helpers as test

from wildcard.dashboards.admin.domains import constants
from wildcard.dashboards.admin.domains import workflows


DOMAINS_INDEX_URL = reverse(constants.DOMAINS_INDEX_URL)
DOMAIN_CREATE_URL = reverse(constants.DOMAINS_CREATE_URL)
DOMAIN_UPDATE_URL = reverse(constants.DOMAINS_UPDATE_URL, args=[1])
GROUP_ROLE_PREFIX = constants.DOMAIN_GROUP_MEMBER_SLUG + "_role_"


class DomainsViewTests(test.BaseAdminViewTests):
    @test.create_stubs({api.keystone: ('domain_list',)})
    def test_index(self):
        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())

        self.mox.ReplayAll()

        res = self.client.get(DOMAINS_INDEX_URL)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertContains(res, 'Create Domain')
        self.assertContains(res, 'Edit')
        self.assertContains(res, 'Delete Domain')

    @test.create_stubs({api.keystone: ('domain_list',
                                       'keystone_can_edit_domain')})
    def test_index_with_keystone_can_edit_domain_false(self):
        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())
        api.keystone.keystone_can_edit_domain() \
            .MultipleTimes().AndReturn(False)

        self.mox.ReplayAll()

        res = self.client.get(DOMAINS_INDEX_URL)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertNotContains(res, 'Create Domain')
        self.assertNotContains(res, 'Edit')
        self.assertNotContains(res, 'Delete Domain')

    @test.create_stubs({api.keystone: ('domain_list',
                                       'domain_delete')})
    def test_delete_domain(self):
        domain = self.domains.get(id="2")

        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())
        api.keystone.domain_delete(IgnoreArg(), domain.id)

        self.mox.ReplayAll()

        formData = {'action': 'domains__delete__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_list', )})
    def test_delete_with_enabled_domain(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())

        self.mox.ReplayAll()

        formData = {'action': 'domains__delete__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
        self.assertMessageCount(error=2)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'domain_list', )})
    def test_set_clear_domain_context(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_get(IgnoreArg(), domain.id).AndReturn(domain)
        api.keystone.domain_get(IgnoreArg(), domain.id).AndReturn(domain)

        api.keystone.domain_list(IgnoreArg()).AndReturn(self.domains.list())

        self.mox.ReplayAll()

        formData = {'action': 'domains__set_domain_context__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, [domain, ])
        self.assertContains(res, "<em>test_domain:</em>")

        formData = {'action': 'domains__clear_domain_context__%s' % domain.id}
        res = self.client.post(DOMAINS_INDEX_URL, formData)

        self.assertTemplateUsed(res, constants.DOMAINS_INDEX_VIEW_TEMPLATE)
        self.assertItemsEqual(res.context['table'].data, self.domains.list())
        self.assertNotContains(res, "<em>test_domain:</em>")


class CreateDomainWorkflowTests(test.BaseAdminViewTests):
    def _get_domain_info(self, domain):
        domain_info = {"name": domain.name,
                       "description": domain.description,
                       "enabled": domain.enabled}
        return domain_info

    def _get_workflow_data(self, domain):
        domain_info = self._get_domain_info(domain)
        return domain_info

    def test_add_domain_get(self):
        url = reverse('horizon:admin:domains:create')
        res = self.client.get(url)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.CreateDomain.name)

        self.assertQuerysetEqual(workflow.steps,
                                 ['<CreateDomainInfo: create_domain>', ])

    @test.create_stubs({api.keystone: ('domain_create', )})
    def test_add_domain_post(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_create(IsA(http.HttpRequest),
                                   description=domain.description,
                                   enabled=domain.enabled,
                                   name=domain.name).AndReturn(domain)

        self.mox.ReplayAll()

        workflow_data = self._get_workflow_data(domain)

        res = self.client.post(DOMAIN_CREATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)


class UpdateDomainWorkflowTests(test.BaseAdminViewTests):
    def _get_domain_info(self, domain):
        domain_info = {"domain_id": domain.id,
                       "name": domain.name,
                       "description": domain.description,
                       "enabled": domain.enabled}
        return domain_info

    def _get_workflow_data(self, domain):
        domain_info = self._get_domain_info(domain)
        return domain_info

    def _get_all_groups(self, domain_id):
        if not domain_id:
            groups = self.groups.list()
        else:
            groups = [group for group in self.groups.list()
                      if group.domain_id == domain_id]
        return groups

    def _get_domain_groups(self, domain_id):
        # all domain groups have role assignments
        return self._get_all_groups(domain_id)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'get_default_role',
                                       'role_list',
                                       'group_list',
                                       'roles_for_group')})
    def test_update_domain_get(self):
        default_role = self.roles.first()
        domain = self.domains.get(id="1")
        groups = self._get_all_groups(domain.id)
        roles = self.roles.list()

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain.id) \
            .AndReturn(groups)

        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         domain=domain.id) \
                .AndReturn(roles)

        self.mox.ReplayAll()

        res = self.client.get(DOMAIN_UPDATE_URL)

        self.assertTemplateUsed(res, views.WorkflowView.template_name)

        workflow = res.context['workflow']
        self.assertEqual(res.context['workflow'].name,
                         workflows.UpdateDomain.name)

        step = workflow.get_step("update_domain")
        self.assertEqual(step.action.initial['name'], domain.name)
        self.assertEqual(step.action.initial['description'],
                         domain.description)
        self.assertQuerysetEqual(
            workflow.steps, [
                '<UpdateDomainInfo: update_domain>',
                '<UpdateDomainGroups: update_group_members>'])

    @test.create_stubs({api.keystone: ('domain_get',
                                       'domain_update',
                                       'get_default_role',
                                       'role_list',
                                       'group_list',
                                       'roles_for_group',
                                       'remove_group_role',
                                       'add_group_role',)})
    def test_update_domain_post(self):
        default_role = self.roles.first()
        domain = self.domains.get(id="1")
        test_description = 'updated description'
        groups = self._get_all_groups(domain.id)
        domain_groups = self._get_domain_groups(domain.id)
        roles = self.roles.list()

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain.id) \
            .AndReturn(groups)

        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         domain=domain.id) \
                .AndReturn(roles)

        workflow_data = self._get_workflow_data(domain)
        # update some fields
        workflow_data['description'] = test_description

        # Group assignment form data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['2']  # member role

        # handle
        api.keystone.domain_update(IsA(http.HttpRequest),
                                   description=test_description,
                                   domain_id=domain.id,
                                   enabled=domain.enabled,
                                   name=domain.name).AndReturn(None)

        # Group assignments
        api.keystone.group_list(IsA(http.HttpRequest),
                                domain=domain.id).AndReturn(domain_groups)

        # admin group - try to remove all roles on current domain
        api.keystone.roles_for_group(
            IsA(http.HttpRequest), group='1', domain=domain.id
        ).AndReturn(roles)
        for role in roles:
            api.keystone.remove_group_role(IsA(http.HttpRequest),
                                           role=role.id,
                                           group='1',
                                           domain=domain.id)

        # member group 1 - has role 1, will remove it
        api.keystone.roles_for_group(
            IsA(http.HttpRequest), group='2', domain=domain.id
        ).AndReturn((roles[0],))
        # remove role 1
        api.keystone.remove_group_role(IsA(http.HttpRequest),
                                       role='1',
                                       group='2',
                                       domain=domain.id)
        # add role 2
        api.keystone.add_group_role(IsA(http.HttpRequest),
                                    role='2',
                                    group='2',
                                    domain=domain.id)

        # member group 3 - has role 2
        api.keystone.roles_for_group(
            IsA(http.HttpRequest), group='3', domain=domain.id
        ).AndReturn((roles[1],))
        # remove role 2
        api.keystone.remove_group_role(IsA(http.HttpRequest),
                                       role='2',
                                       group='3',
                                       domain=domain.id)
        # add role 1
        api.keystone.add_group_role(IsA(http.HttpRequest),
                                    role='1',
                                    group='3',
                                    domain=domain.id)

        self.mox.ReplayAll()

        res = self.client.post(DOMAIN_UPDATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_get',)})
    def test_update_domain_get_error(self):
        domain = self.domains.get(id="1")

        api.keystone.domain_get(IsA(http.HttpRequest), domain.id) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        res = self.client.get(DOMAIN_UPDATE_URL)

        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)

    @test.create_stubs({api.keystone: ('domain_get',
                                       'domain_update',
                                       'get_default_role',
                                       'role_list',
                                       'group_list',
                                       'roles_for_group')})
    def test_update_domain_post_error(self):
        default_role = self.roles.first()
        domain = self.domains.get(id="1")
        test_description = 'updated description'
        groups = self._get_all_groups(domain.id)
        roles = self.roles.list()

        api.keystone.domain_get(IsA(http.HttpRequest), '1').AndReturn(domain)
        api.keystone.get_default_role(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(default_role)
        api.keystone.role_list(IsA(http.HttpRequest)) \
            .MultipleTimes().AndReturn(roles)
        api.keystone.group_list(IsA(http.HttpRequest), domain=domain.id) \
            .AndReturn(groups)

        for group in groups:
            api.keystone.roles_for_group(IsA(http.HttpRequest),
                                         group=group.id,
                                         domain=domain.id) \
                .AndReturn(roles)

        workflow_data = self._get_workflow_data(domain)
        # update some fields
        workflow_data['description'] = test_description

        # Group assignment form data
        workflow_data[GROUP_ROLE_PREFIX + "1"] = ['3']  # admin role
        workflow_data[GROUP_ROLE_PREFIX + "2"] = ['2']  # member role

        # handle
        api.keystone.domain_update(IsA(http.HttpRequest),
                                   description=test_description,
                                   domain_id=domain.id,
                                   enabled=domain.enabled,
                                   name=domain.name) \
            .AndRaise(self.exceptions.keystone)

        self.mox.ReplayAll()

        res = self.client.post(DOMAIN_UPDATE_URL, workflow_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, DOMAINS_INDEX_URL)
