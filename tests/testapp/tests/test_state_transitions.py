from django.test import TestCase

from testapp.models import Insect, Caterpillar, Butterfly


class TestStateProxy(TestCase):
    def test_initial_proxy_set_succeed(self):
        insect = Insect()
        self.assertTrue(isinstance(insect, Caterpillar))

    def test_transition_proxy_set_succeed(self):
        insect = Insect()
        insect.cocoon()
        self.assertTrue(isinstance(insect, Butterfly))

    def test_load_proxy_set(self):
        Insect.objects.create(state=Insect.STATE.CATERPILLAR)
        Insect.objects.create(state=Insect.STATE.BUTTERFLY)

        insects = Insect.objects.all()
        self.assertEqual(set([Caterpillar, Butterfly]), set(insect.__class__ for insect in insects))
