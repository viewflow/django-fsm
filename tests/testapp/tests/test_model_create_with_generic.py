try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    # Django 1.6
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition


class Ticket(models.Model):
    class Meta:
        app_label = "testapp"


class Task(models.Model):
    class STATE:
        NEW = "new"
        DONE = "done"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    causality = GenericForeignKey("content_type", "object_id")
    state = FSMField(default=STATE.NEW)

    @transition(field=state, source=STATE.NEW, target=STATE.DONE)
    def do(self):
        pass

    class Meta:
        app_label = "testapp"


class Test(TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create()

    def test_model_objects_create(self):
        """Check a model with state field can be created
        if one of the other fields is a property or a virtual field.
        """
        Task.objects.create(causality=self.ticket)
