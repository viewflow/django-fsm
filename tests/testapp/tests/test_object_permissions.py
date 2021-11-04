from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings

from guardian.shortcuts import assign_perm

from django_fsm import FSMField, transition, has_transition_perm


class ObjectPermissionTestModel(models.Model):
    state = FSMField(default="new")

    @transition(
        field=state,
        source="new",
        target="published",
        on_error="failed",
        permission="testapp.can_publish_objectpermissiontestmodel",
    )
    def publish(self):
        pass

    class Meta:
        app_label = "testapp"

        permissions = [
            ("can_publish_objectpermissiontestmodel", "Can publish ObjectPermissionTestModel"),
        ]


@override_settings(
    AUTHENTICATION_BACKENDS=("django.contrib.auth.backends.ModelBackend", "guardian.backends.ObjectPermissionBackend")
)
class ObjectPermissionFSMFieldTest(TestCase):
    def setUp(self):
        super(ObjectPermissionFSMFieldTest, self).setUp()
        self.model = ObjectPermissionTestModel.objects.create()

        self.unprivileged = User.objects.create(username="unpriviledged")
        self.privileged = User.objects.create(username="object_only_privileged")
        assign_perm("can_publish_objectpermissiontestmodel", self.privileged, self.model)

    def test_object_only_access_success(self):
        self.assertTrue(has_transition_perm(self.model.publish, self.privileged))
        self.model.publish()

    def test_object_only_other_access_prohibited(self):
        self.assertFalse(has_transition_perm(self.model.publish, self.unprivileged))
