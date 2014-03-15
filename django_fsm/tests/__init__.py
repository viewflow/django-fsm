# -*- coding: utf-8 -*-
# pylint: disable=C0111, C0103, R0904

from django.test import TestCase
from django.db import models

"""
from django_fsm.signals import pre_transition, post_transition
from django_fsm.db.fields import FSMField, FSMKeyField, FSMIntegerField, \
    TransitionNotAllowed, transition, can_proceed


class DBState(models.Model):
    id = models.CharField(primary_key=True, max_length=50)

    label = models.CharField(max_length=255)

    def __unicode__(self):
        return self.label

FK_AVAILABLE_STATES = (('new', '_NEW_'),
                      ('published', '_PUBLISHED_'),
                      ('hidden', '_HIDDEN_'),
                      ('removed', '_REMOVED_'),
                      ('stolen', '_STOLEN_'),
                      ('moderated', '_MODERATED_'),
                     )

class FKBlogPost(models.Model):

    state = FSMKeyField(DBState, default='new', protected=True)

    @transition(source='new',
                target='published',
                field='state')
    def publish(self):
        pass

    @transition(source='published',
                field='state')
    def notify_all(self):
        pass

    @transition(source='published',
                target='hidden',
                field='state')
    def hide(self):
        pass

    @transition(source='new',
                target='removed',
                field='state')
    def remove(self):
        raise Exception('No rights to delete %s' % self)

    @transition(source=['published',
                        'hidden'],
                target='stolen',
                field='state')
    def steal(self):
        pass

    @transition(source='*',
                target='moderated',
                field='state')
    def moderate(self):
        pass


class FSMKeyFieldTest(TestCase):
    def setUp(self):
        self.model = FKBlogPost()
        self.STATES = {}
        # Populate dbstate items
        for item in FK_AVAILABLE_STATES:
            state = DBState(pk=item[0], label=item[1])
            state.save()
            self.STATES[item[0]] = state

    def test_initial_state_instatiated(self):
        self.assertEqual(self.model.state, 'new',)

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, 'published')

        self.assertTrue(can_proceed(self.model.hide))
        self.model.hide()
        self.assertEqual(self.model.state, 'hidden')

    def test_unknow_transition_fails(self):
        self.assertFalse(can_proceed(self.model.hide))
        self.assertRaises(TransitionNotAllowed, self.model.hide)

    def test_state_non_changed_after_fail(self):
        self.assertTrue(can_proceed(self.model.remove))
        self.assertRaises(Exception, self.model.remove)
        self.assertEqual(self.model.state, 'new')

    def test_allowed_null_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.model.notify_all()
        self.assertEqual(self.model.state, 'published')

    def test_unknow_null_transition_should_fail(self):
        self.assertRaises(TransitionNotAllowed, self.model.notify_all)
        self.assertEqual(self.model.state, 'new')


    def test_mutiple_source_support_path_1_works(self):
        self.model.publish()
        self.model.steal()
        self.assertEqual(self.model.state, 'stolen')

    def test_mutiple_source_support_path_2_works(self):
        self.model.publish()
        self.model.hide()
        self.model.steal()
        self.assertEqual(self.model.state, 'stolen')

    def test_star_shortcut_succeed(self):
        self.assertTrue(can_proceed(self.model.moderate))
        self.model.moderate()
        self.assertEqual(self.model.state, 'moderated')


class BlogPostStatus(models.Model):
    name = models.CharField(max_length=10, unique=True)
    objects = models.Manager()

    @transition(source='new', target='published')
    def publish(self):
        pass


class BlogPostWithFKState(models.Model):
    status = FSMKeyField(BlogPostStatus, default=lambda: BlogPostStatus.objects.get(name="new"))

    @transition(source='new', target='published')
    def publish(self):
        pass

    @transition(source='published', target='hidden', save=True)
    def hide(self):
        pass


class BlogPostWithFKStateTest(TestCase):
    def setUp(self):
        self.model = BlogPost()
        BlogPostStatus.objects.create(name="new")
        BlogPostStatus.objects.create(name="published")
        BlogPostStatus.objects.create(name="hidden")

    def test_known_transition_should_succeed(self):
        self.model.publish()
        self.assertEqual(self.model.state, 'published')

        self.model.hide()
        self.assertEqual(self.model.state, 'hidden')

    def test_unknow_transition_fails(self):
        self.assertRaises(TransitionNotAllowed, self.model.hide)



class BlogPostStateEnum(object):
    NEW = 10
    PUBLISHED = 20
    HIDDEN = 30


class BlogPostWithIntegerField(models.Model):
    state = FSMIntegerField(default=BlogPostStateEnum.NEW)

    @transition(source=BlogPostStateEnum.NEW, target=BlogPostStateEnum.PUBLISHED)
    def publish(self):
        pass

    @transition(source=BlogPostStateEnum.PUBLISHED, target=BlogPostStateEnum.HIDDEN, save=True)
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



"""

## 2.0 Tests
