from django.test import TestCase

from testapp.models import BlogPostWithStringField


class StringFieldTestCase(TestCase):
    def setUp(self):
        self.model = BlogPostWithStringField()

    def test_initial_state(self):
        self.assertEqual(self.model.state, 'new')
        self.model.publish()
        self.assertEqual(self.model.state, 'published')
