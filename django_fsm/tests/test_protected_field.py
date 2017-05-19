import django

from django.db import models
from django.test import TestCase
try:
    from django.utils import unittest  # for python2.6
except ImportError:
    import unittest

from django_fsm import FSMField, transition


class ProtectedAccessModel(models.Model):
    status = FSMField(default='new', protected=True)
    another_fsm_field = FSMField(default='new', protected=True)

    @transition(field=status, source='new', target='published')
    def publish(self):
        pass

    class Meta:
        app_label = 'django_fsm'


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

    @unittest.skipIf(django.VERSION < (1, 8), "Django introduced refresh_from_db in 1.8")
    def test_refresh_from_db(self):
        instance = ProtectedAccessModel()
        self.assertEqual(instance.status, 'new')
        instance.save()
        ProtectedAccessModel.objects.all().update(status='change')

        instance.refresh_from_db()
        # instance = ProtectedAccessModel.objects.all().get(pk=instance.pk)
        self.assertEqual(instance.status, 'change')
