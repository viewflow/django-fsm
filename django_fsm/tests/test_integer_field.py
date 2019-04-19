from django.db import models
from django.test import TestCase
from django_fsm import FSMIntegerField, TransitionNotAllowed, transition


class BlogPostStateEnum(object):
    NEW = 10
    PUBLISHED = 20
    HIDDEN = 30


class BlogPostWithIntegerField(models.Model):
    state = FSMIntegerField(default=BlogPostStateEnum.NEW)

    @transition(field=state, source=BlogPostStateEnum.NEW, target=BlogPostStateEnum.PUBLISHED)
    def publish(self):
        pass

    @transition(field=state, source=BlogPostStateEnum.PUBLISHED, target=BlogPostStateEnum.HIDDEN)
    def hide(self):
        pass


class BlogPostWithIntegerFieldTest(TestCase):
    def setUp(self):
        self.model = BlogPostWithIntegerField()

    def test_known_transition_should_succeed(self):
        self.model.publish()
        self.assertEqual(self.model.state, BlogPostStateEnum.PUBLISHED)

        self.model.hide()
        self.assertEqual(self.model.state, BlogPostStateEnum.HIDDEN)

    def test_unknow_transition_fails(self):
        self.assertRaises(TransitionNotAllowed, self.model.hide)
