from django.db import models
from django.test import TestCase

from django_fsm import FSMField, transition, can_proceed


class BaseModel(models.Model):
    state = FSMField(default='new')

    @transition(field=state, source='new', target='published')
    def publish(self):
        pass


class InheritedModel(BaseModel):
    @transition(field='state', source='published', target='sticked')
    def stick(self):
        pass

    class Meta:
        proxy = True


class TestinheritedModel(TestCase):
    def setUp(self):
        self.model = InheritedModel()

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, 'published')

        self.assertTrue(can_proceed(self.model.stick))
        self.model.stick()
        self.assertEqual(self.model.state, 'sticked')

    def test_field_available_transitions_works(self):
        self.model.publish()
        self.assertEqual(self.model.state, 'published')
        transitions = self.model.get_available_state_transitions()

        self.assertEqual(1, len(transitions))
        self.assertIn('sticked', [target for target, _ in transitions])
