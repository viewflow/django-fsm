from django.db import models
from django.test import TestCase
from django_fsm import FSMField, TransitionNotAllowed, transition, can_proceed


def condition_func(instance):
    return True


class BlogPostWithConditions(models.Model):
    state = FSMField(default="new")

    def model_condition(self):
        return True

    def unmet_condition(self):
        return False

    @transition(field=state, source="new", target="published", conditions=[condition_func, model_condition])
    def publish(self):
        pass

    @transition(field=state, source="published", target="destroyed", conditions=[condition_func, unmet_condition])
    def destroy(self):
        pass


class ConditionalTest(TestCase):
    def setUp(self):
        self.model = BlogPostWithConditions()

    def test_initial_staet(self):
        self.assertEqual(self.model.state, "new")

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, "published")

    def test_unmet_condition(self):
        self.model.publish()
        self.assertEqual(self.model.state, "published")
        self.assertFalse(can_proceed(self.model.destroy))
        self.assertRaises(TransitionNotAllowed, self.model.destroy)

        self.assertTrue(can_proceed(self.model.destroy, check_conditions=False))
