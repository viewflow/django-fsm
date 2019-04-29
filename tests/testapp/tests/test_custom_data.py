from django.test import TestCase

from testapp.models import BlogPostWithCustomData


class CustomTransitionDataTest(TestCase):
    def setUp(self):
        self.model = BlogPostWithCustomData()

    def test_initial_state(self):
        self.assertEqual(self.model.state, 'new')
        transitions = list(self.model.get_available_state_transitions())
        self.assertEquals(len(transitions), 1)
        self.assertEqual(transitions[0].target, 'published')
        self.assertDictEqual(transitions[0].custom, {'label': 'Publish', 'type': '*'})

    def test_all_transitions_have_custom_data(self):
        transitions = self.model.get_all_state_transitions()
        for t in transitions:
            self.assertIsNotNone(t.custom['label'])
            self.assertIsNotNone(t.custom['type'])
