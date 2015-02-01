from django.contrib.auth.models import User, Permission
from django.test.utils import override_settings
from django.conf import settings

from guardian.shortcuts import assign_perm, remove_perm

from django_fsm import has_transition_perm
from testapp.models import BlogPost
from .test_permissions import PermissionFSMFieldTest


@override_settings(AUTHENTICATION_BACKENDS=settings.GUARDIAN_SETTING)
class ObjectPermissionFSMFieldTest(PermissionFSMFieldTest):
    def setUp(self):
        super(ObjectPermissionFSMFieldTest, self).setUp()
        self.obj_model = BlogPost.objects.create()
        self.object_only_privileged = User.objects.create(username='object_only_privileged')
        assign_perm('can_publish_post', self.object_only_privileged, self.obj_model)

    def test_object_only_access_success(self):
        self.assertTrue(has_transition_perm(self.obj_model.publish, self.object_only_privileged))

    def test_object_only_other_access_prohibited(self):
        self.assertFalse(has_transition_perm(self.model.publish, self.object_only_privileged))
