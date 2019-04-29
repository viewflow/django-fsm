from django.test import TestCase

from django_fsm.signals import pre_transition, post_transition
from testapp.models import MultiResultTest


class Test(TestCase):
    def test_return_state_succeed(self):
        instance = MultiResultTest()
        instance.publish(is_public=True)
        self.assertEqual(instance.state, 'published')

    def test_get_state_succeed(self):
        instance = MultiResultTest(state='for_moderators')
        instance.moderate(allowed=False)
        self.assertEqual(instance.state, 'rejected')


class TestSignals(TestCase):
    def setUp(self):
        self.pre_transition_called = False
        self.post_transition_called = False
        pre_transition.connect(self.on_pre_transition, sender=MultiResultTest)
        post_transition.connect(self.on_post_transition, sender=MultiResultTest)

    def on_pre_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, source)
        self.pre_transition_called = True

    def on_post_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, target)
        self.post_transition_called = True

    def test_signals_called_with_get_state(self):
        instance = MultiResultTest(state='for_moderators')
        instance.moderate(allowed=False)
        self.assertTrue(self.pre_transition_called)
        self.assertTrue(self.post_transition_called)

    def test_signals_called_with_return_value(self):
        instance = MultiResultTest()
        instance.publish(is_public=True)
        self.assertTrue(self.pre_transition_called)
        self.assertTrue(self.post_transition_called)
