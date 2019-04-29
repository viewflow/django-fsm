from django.test import TestCase

from testapp.models import MixinSupportTestModel


class Test(TestCase):
    def test_usecase(self):
        model = MixinSupportTestModel()

        model.draft()
        self.assertEqual(model.state, 'draft')

        model.publish()
        self.assertEqual(model.state, 'published')
