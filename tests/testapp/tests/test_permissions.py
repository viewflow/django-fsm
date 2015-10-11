from django.contrib.auth.models import User, Permission
from django.test import TestCase


from django_fsm import has_transition_perm
from testapp.models import BlogPost


class PermissionFSMFieldTest(TestCase):
    def setUp(self):
        self.model = BlogPost()
        self.unpriviledged = User.objects.create(username='unpriviledged')
        self.priviledged = User.objects.create(username='priviledged')

        self.priviledged.user_permissions.add(
            Permission.objects.get_by_natural_key('can_publish_post', 'testapp', 'blogpost'))
        self.priviledged.user_permissions.add(
            Permission.objects.get_by_natural_key('can_remove_post', 'testapp', 'blogpost'))

    def test_proviledged_access_succed(self):
        self.assertTrue(has_transition_perm(self.model.publish, self.priviledged))
        self.assertTrue(has_transition_perm(self.model.remove, self.priviledged))

        transitions = self.model.get_available_user_state_transitions(self.priviledged)
        self.assertEquals(set(['publish', 'remove', 'moderate']),
                          set(transition.name for transition in transitions))

    def test_unpriviledged_access_prohibited(self):
        self.assertFalse(has_transition_perm(self.model.publish, self.unpriviledged))
        self.assertFalse(has_transition_perm(self.model.remove, self.unpriviledged))

        transitions = self.model.get_available_user_state_transitions(self.unpriviledged)
        self.assertEquals(set(['moderate']),
                          set(transition.name for transition in transitions))
