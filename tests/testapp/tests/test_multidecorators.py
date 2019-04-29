from django.test import TestCase

from django_fsm.signals import post_transition
from testapp.models import TestModel


def count_calls(sender, instance, name, source, target, **kwargs):
    instance.signal_counter += 1


post_transition.connect(count_calls, sender=TestModel)


class TestStateProxy(TestCase):
    def test_transition_method_called_once(self):
        model = TestModel()
        model.review()
        self.assertEqual(1, model.counter)
        self.assertEqual(1, model.signal_counter)
