from django.db import models
from django.test import TestCase

from django_fsm import FSMField, transition


class PropagateAccessModel(models.Model):
    status = FSMField(default='new', propagate=True)

    @transition(field=status, source='new', target='published', on_error='error')
    def publish(self):
        raise Exception

    class Meta:
        app_label = 'django_fsm'


class NoPropagateAccessModel(models.Model):
    status = FSMField(default='new', propagate=False)

    @transition(field=status, source='new', target='published', on_error='error')
    def publish(self):
        raise Exception

    class Meta:
        app_label = 'django_fsm'


class TestPropagateModels(TestCase):
    def test_propagate(self):
        instance = PropagateAccessModel()
        self.assertEqual(instance.status, 'new')
        self.assertRaises(Exception, instance.publish())

        instance = NoPropagateAccessModel()
        self.assertEqual(instance.status, 'new')
        self.assertNone(instance.publish())
