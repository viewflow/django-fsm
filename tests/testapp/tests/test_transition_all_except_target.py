from django.test import TestCase

from django_fsm import can_proceed
from testapp.models import TestExceptTargetTransitionShortcut


class Test(TestCase):
    def setUp(self):
        self.model = TestExceptTargetTransitionShortcut()

    def test_usecase(self):
        self.assertEqual(self.model.state, 'new')
        self.assertTrue(can_proceed(self.model.remove))
        self.model.remove()

        self.assertEqual(self.model.state, 'removed')
        self.assertFalse(can_proceed(self.model.remove))
