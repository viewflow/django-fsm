from django.db import models
from django.test import TestCase
from django_fsm import FSMField, transition, RETURN_VALUE, GET_STATE


class MultiResultTest(models.Model):
    state = FSMField(default='new')

    @transition(
        field=state,
        source='new',
        target=RETURN_VALUE('for_moderators', 'published'))
    def publish(self, is_public=False):
        return 'published' if is_public else 'for_moderators'

    @transition(
        field=state,
        source='for_moderators',
        target=GET_STATE(
            lambda self, allowed: 'published' if allowed else 'rejected',
            states=['published', 'rejected']
        )
    )
    def moderate(self, allowed):
        pass

    class Meta:
        app_label = 'testapp'


class Test(TestCase):
    def test_return_state_succeed(self):
        instance = MultiResultTest()
        instance.publish(is_public=True)
        self.assertEqual(instance.state, 'published')

    def test_get_state_succeed(self):
        instance = MultiResultTest(state='for_moderators')
        instance.moderate(allowed=False)
        self.assertEqual(instance.state, 'rejected')
