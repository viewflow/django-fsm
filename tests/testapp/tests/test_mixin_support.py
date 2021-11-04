from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition


class WorkflowMixin(object):
    @transition(field="state", source="*", target="draft")
    def draft(self):
        pass

    @transition(field="state", source="draft", target="published")
    def publish(self):
        pass

    class Meta:
        app_label = "testapp"


class MixinSupportTestModel(WorkflowMixin, models.Model):
    state = FSMField(default="new")


class Test(TestCase):
    def test_usecase(self):
        model = MixinSupportTestModel()

        model.draft()
        self.assertEqual(model.state, "draft")

        model.publish()
        self.assertEqual(model.state, "published")
