from django.test import TestCase

from testapp.models import Ticket, Task


class Test(TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create()

    def test_model_objects_create(self):
        """Check a model with state field can be created
        if one of the other fields is a property or a virtual field.
        """
        Task.objects.create(causality=self.ticket)
