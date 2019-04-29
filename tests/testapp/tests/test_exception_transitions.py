from django.test import TestCase

from django_fsm import can_proceed
from django_fsm.signals import post_transition
from testapp.models import ExceptionalBlogPost


class FSMFieldExceptionTest(TestCase):
    def setUp(self):
        self.model = ExceptionalBlogPost()
        post_transition.connect(self.on_post_transition, sender=ExceptionalBlogPost)
        self.post_transition_data = None

    def on_post_transition(self, **kwargs):
        self.post_transition_data = kwargs

    def test_state_changed_after_fail(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.assertRaises(Exception, self.model.publish)
        self.assertEqual(self.model.state, 'crashed')
        self.assertEqual(self.post_transition_data['target'], 'crashed')
        self.assertTrue('exception' in self.post_transition_data)

    def test_state_not_changed_after_fail(self):
        self.assertTrue(can_proceed(self.model.delete))
        self.assertRaises(Exception, self.model.delete)
        self.assertEqual(self.model.state, 'new')
        self.assertIsNone(self.post_transition_data)
