from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.test.utils import override_settings

from django_fsm import has_transition_perm
from testapp.models import ObjectPermissionTestModel


@override_settings(
    AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',))
class ObjectPermissionFSMFieldTest(TestCase):
    def setUp(self):
        super(ObjectPermissionFSMFieldTest, self).setUp()
        self.model = ObjectPermissionTestModel.objects.create()

        self.unprivileged = User.objects.create(username='unpriviledged')
        self.privileged = User.objects.create(username='object_only_privileged')
        permission = Permission.objects.get(
            codename='can_publish_objectpermissiontestmodel',
        )
        self.privileged.user_permissions.add(permission)

    def test_object_only_access_success(self):
        self.assertTrue(has_transition_perm(self.model.publish, self.privileged))
        self.model.publish()

    def test_object_only_other_access_prohibited(self):
        self.assertFalse(has_transition_perm(self.model.publish, self.unprivileged))
