from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition, can_proceed


class TestExceptTargetTransitionShortcut(models.Model):
    state = FSMField(default="new")

    @transition(field=state, source="new", target="published")
    def publish(self):
        pass

    @transition(field=state, source="+", target="removed")
    def remove(self):
        pass

    class Meta:
        app_label = "testapp"


class Test(TestCase):
    def setUp(self):
        self.model = TestExceptTargetTransitionShortcut()

    def test_usecase(self):
        self.assertEqual(self.model.state, "new")
        self.assertTrue(can_proceed(self.model.remove))
        self.model.remove()

        self.assertEqual(self.model.state, "removed")
        self.assertFalse(can_proceed(self.model.remove))
