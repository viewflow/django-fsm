from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition
from django_fsm.signals import post_transition


class TestModel(models.Model):
    counter = models.IntegerField(default=0)
    signal_counter = models.IntegerField(default=0)
    state = FSMField(default="SUBMITTED_BY_USER")

    @transition(field=state, source="SUBMITTED_BY_USER", target="REVIEW_USER")
    @transition(field=state, source="SUBMITTED_BY_ADMIN", target="REVIEW_ADMIN")
    @transition(field=state, source="SUBMITTED_BY_ANONYMOUS", target="REVIEW_ANONYMOUS")
    def review(self):
        self.counter += 1

    class Meta:
        app_label = "testapp"


def count_calls(sender, instance, name, source, target, **kwargs):
    instance.signal_counter += 1


post_transition.connect(count_calls, sender=TestModel)


class TestStateProxy(TestCase):
    def test_transition_method_called_once(self):
        model = TestModel()
        model.review()
        self.assertEqual(1, model.counter)
        self.assertEqual(1, model.signal_counter)
