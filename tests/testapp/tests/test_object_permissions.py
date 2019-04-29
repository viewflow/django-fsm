from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from guardian.shortcuts import assign_perm

from django_fsm import has_transition_perm
from testapp.models import ObjectPermissionTestModel


@override_settings(
    AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',
                             'guardian.backends.ObjectPermissionBackend'))
class ObjectPermissionFSMFieldTest(TestCase):
    def setUp(self):
        super(ObjectPermissionFSMFieldTest, self).setUp()
        self.model = ObjectPermissionTestModel.objects.create()

        self.unprivileged = User.objects.create(username='unpriviledged')
        self.privileged = User.objects.create(username='object_only_privileged')
        assign_perm('can_publish_objectpermissiontestmodel', self.privileged, self.model)

    def test_object_only_access_success(self):
        self.assertTrue(has_transition_perm(self.model.publish, self.privileged))
        self.model.publish()

    def test_object_only_other_access_prohibited(self):
        self.assertFalse(has_transition_perm(self.model.publish, self.unprivileged))
