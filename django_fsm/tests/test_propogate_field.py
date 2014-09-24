from django.db import models
from django.test import TestCase

from django_fsm import FSMField, transition


class PropogateAccessModel(models.Model):
    status = FSMField(default='new', propogate=False)

    @transition(field=status, source='new', target='published',
                on_error='error')
    def publish(self):
        raise Exception

    class Meta:
        app_label = 'django_fsm'


class NoPropogateAccessModel(models.Model):
    status = FSMField(default='new', propogate=False)

    @transition(field=status, source='new', target='published',
                on_error='error')
    def publish(self):
        raise Exception

    class Meta:
        app_label = 'django_fsm'

class TestPropogateModels(TestCase):
    def test_propogate(self):
        instance = NoPropogateAccessModel()
        self.assertEqual(instance.status, 'new')
        self.assertNone(instance.publish())

        instance = PropogateAccessModel()
        self.assertEqual(instance.status, 'new')
        self.assertRaises(Exception, instance.publish())
