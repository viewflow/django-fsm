from django.db import models
from django.test import TestCase

from django_fsm import FSMField, transition, can_proceed


class BaseAbstractModel(models.Model):
    state = FSMField(default="new")

    class Meta:
        abstract = True

    @transition(field=state, source="new", target="published")
    def publish(self):
        pass


class AnotherFromAbstractModel(BaseAbstractModel):
    """
    This class exists to trigger a regression when multiple concrete classes
    inherit from a shared abstract class (example: BaseAbstractModel).
    Don't try to remove it.
    """
    @transition(field="state", source="published", target="sticked")
    def stick(self):
        pass


class InheritedFromAbstractModel(BaseAbstractModel):
    @transition(field="state", source="published", target="sticked")
    def stick(self):
        pass


class TestinheritedModel(TestCase):
    def setUp(self):
        self.model = InheritedFromAbstractModel()

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, "published")

        self.assertTrue(can_proceed(self.model.stick))
        self.model.stick()
        self.assertEqual(self.model.state, "sticked")

    def test_field_available_transitions_works(self):
        self.model.publish()
        self.assertEqual(self.model.state, "published")
        transitions = self.model.get_available_state_transitions()
        self.assertEqual(["sticked"], [data.target for data in transitions])

    def test_field_all_transitions_works(self):
        transitions = self.model.get_all_state_transitions()
        self.assertEqual(
            set([("new", "published"), ("published", "sticked")]), set((data.source, data.target) for data in transitions)
        )
