#-*- coding: utf-8 -*-
# pylint: disable=C0111, C0103, R0904

from django.test import TestCase
from django.db import models

from django_fsm.signals import pre_transition, post_transition
from django_fsm.db.fields import FSMField, FSMKeyField, \
    TransitionNotAllowed, transition, can_proceed

class BlogPost(models.Model):
    state = FSMField(default='new')

    @transition(source='new', target='published')
    def publish(self):
        pass

    @transition(source='published')
    def notify_all(self):
        pass

    @transition(source='published', target='hidden')
    def hide(self):
        pass

    @transition(source='new', target='removed')
    def remove(self):
        raise Exception('No rights to delete %s' % self)

    @transition(source=['published','hidden'], target='stolen')
    def steal(self):
        pass

    @transition(source='*', target='moderated')
    def moderate(self):
        pass


class FSMFieldTest(TestCase):
    def setUp(self):
        self.model = BlogPost()

    def test_initial_state_instatiated(self):
        self.assertEqual(self.model.state, 'new')

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


class InvalidModel(models.Model):
    state = FSMField(default='new')
    action = FSMField(default='no')

    @transition(source='new', target='no')
    def validate(self):
        pass


class InvalidModelTest(TestCase):
    def test_two_fsmfields_in_one_model_not_allowed(self):
        model = InvalidModel()
        self.assertRaises(TypeError, model.validate)


class Document(models.Model):
    status = FSMField(default='new')

    @transition(source='new', target='published')
    def publish(self):
        pass


class DocumentTest(TestCase):
    def test_any_state_field_name_allowed(self):
        model = Document()
        model.publish()
        self.assertEqual(model.status, 'published')


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


def condition_func(instance):
    return True


class BlogPostWithConditions(models.Model):
    state = FSMField(default='new')

    def model_condition(self):
        return True

    def unmet_condition(self):
        return False

    @transition(source='new', target='published', conditions=[condition_func, model_condition])
    def publish(self):
        pass

    @transition(source='published', target='destroyed', conditions=[condition_func, unmet_condition])
    def destroy(self):
        pass


class ConditionalTest(TestCase):
    def setUp(self):
        self.model = BlogPostWithConditions()

    def test_initial_staet(self):
        self.assertEqual(self.model.state, 'new')

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, 'published')

    def test_unmet_condition(self):
        self.model.publish()
        self.assertEqual(self.model.state, 'published')
        self.assertFalse(can_proceed(self.model.destroy))
        self.assertRaises(TransitionNotAllowed, self.model.destroy)


class BlogPostWithExplicitState(models.Model):
    state = FSMField(default='new')
    approvement = FSMField(default='new')

    @transition(field=state, source='new', target='published')
    def publish(self):
        pass

    @transition(field=approvement, source='new', target='approved')
    def approve(self):
        pass

    @transition(field=approvement, source='new', target='declined')
    def decline(self):
        pass


class ExplicitFSMFieldTest(TestCase):
    def setUp(self):
        self.model = BlogPostWithExplicitState()

    def test_initial_state_instatiated(self):
        self.assertEqual(self.model.state, 'new')
        self.assertEqual(self.model.approvement, 'new')
        self.assertEqual([t[0] for t in self.model.get_available_state_transitions()], ['published'])
        self.assertEqual([t[0] for t in self.model.get_available_approvement_transitions()], ['approved', 'declined'])

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, 'published')
        self.assertEqual(self.model.approvement, 'new')
        self.assertEqual(self.model.get_available_state_transitions(), [])
        self.assertEqual([t[0] for t in self.model.get_available_approvement_transitions()], 
                         ['approved', 'declined'])


class StateSignalsTests(TestCase):
    def setUp(self):
        self.model = BlogPost()
        self.pre_transition_called = False
        self.post_transition_called = False
        pre_transition.connect(self.on_pre_transition, sender=BlogPost)
        post_transition.connect(self.on_post_transition, sender=BlogPost)

    def on_pre_transition(self, sender, instance, name, source, target, **kwargs):        
        self.assertEqual(instance.state, source)
        self.pre_transition_called = True

    def on_post_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, target)
        self.post_transition_called = True

    def test_signals_called_on_valid_transition(self):
        self.model.publish()
        self.assertTrue(self.pre_transition_called)
        self.assertTrue(self.post_transition_called)

    def test_signals_not_called_on_invalid_transition(self):
        self.assertRaises(TransitionNotAllowed, self.model.hide)
        self.assertFalse(self.pre_transition_called)
        self.assertFalse(self.post_transition_called)


class ProtectedAccessModel(models.Model):
    status = FSMField(default='new', protected=True)

    @transition(source='new', target='published')
    def publish(self):
        pass


class TestDirectAccessModels(TestCase):
    def test_no_direct_access(self):
        instance = ProtectedAccessModel()
        self.assertEqual(instance.status, 'new')

        def try_change():
            instance.status = 'change'

        self.assertRaises(AttributeError, try_change)

        instance.publish()
        instance.save()
        self.assertEqual(instance.status, 'published')
