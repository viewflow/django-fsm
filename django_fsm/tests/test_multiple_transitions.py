from django.db import models
from django.test import TestCase

from django_fsm import FSMField, TransitionNotAllowed, transition, can_proceed
from django_fsm.signals import pre_transition, post_transition


class BlogPost(models.Model):
    state = FSMField(default='new')
    state2 = FSMField(default='new2')

    @transition(field=state, source='new', target='published')
    @transition(field=state2, source='new2', target='published2')
    def publish(self):
        pass

    @transition(field=state, source='published', target='hidden')
    @transition(field=state2, source='published2', target='hidden2')
    def hide(self):
        pass


class FSMMultpleTransitionTest(TestCase):
    def setUp(self):
        self.model = BlogPost()

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, 'published')
        self.assertEqual(self.model.state2, 'published2')

    def test_unknown_transition_fails_all_conditions_unmet(self):
        self.assertFalse(can_proceed(self.model.hide))
        self.assertRaises(TransitionNotAllowed, self.model.hide)

    def test_unknown_transition_fails_partial_conditions_unmet(self):
        self.model.state = 'published'
        self.assertFalse(can_proceed(self.model.hide))
        self.assertRaises(TransitionNotAllowed, self.model.hide)