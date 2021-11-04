from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition


class BlogPostWithStringField(models.Model):
    state = FSMField(default="new")

    @transition(field="state", source="new", target="published", conditions=[])
    def publish(self):
        pass

    @transition(field="state", source="published", target="destroyed")
    def destroy(self):
        pass

    @transition(field="state", source="published", target="review")
    def review(self):
        pass

    class Meta:
        app_label = "testapp"


class StringFieldTestCase(TestCase):
    def setUp(self):
        self.model = BlogPostWithStringField()

    def test_initial_state(self):
        self.assertEqual(self.model.state, "new")
        self.model.publish()
        self.assertEqual(self.model.state, "published")
