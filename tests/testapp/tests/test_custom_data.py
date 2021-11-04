from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition


class BlogPostWithCustomData(models.Model):
    state = FSMField(default="new")

    @transition(field=state, source="new", target="published", conditions=[], custom={"label": "Publish", "type": "*"})
    def publish(self):
        pass

    @transition(field=state, source="published", target="destroyed", custom=dict(label="Destroy", type="manual"))
    def destroy(self):
        pass

    @transition(field=state, source="published", target="review", custom=dict(label="Periodic review", type="automated"))
    def review(self):
        pass

    class Meta:
        app_label = "testapp"


class CustomTransitionDataTest(TestCase):
    def setUp(self):
        self.model = BlogPostWithCustomData()

    def test_initial_state(self):
        self.assertEqual(self.model.state, "new")
        transitions = list(self.model.get_available_state_transitions())
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0].target, "published")
        self.assertDictEqual(transitions[0].custom, {"label": "Publish", "type": "*"})

    def test_all_transitions_have_custom_data(self):
        transitions = self.model.get_all_state_transitions()
        for t in transitions:
            self.assertIsNotNone(t.custom["label"])
            self.assertIsNotNone(t.custom["type"])
