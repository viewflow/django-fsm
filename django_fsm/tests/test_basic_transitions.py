from django.db import models
from django.test import TestCase

from django_fsm import FSMField, TransitionNotAllowed, transition, can_proceed, Transition
from django_fsm.signals import pre_transition, post_transition


class BlogPost(models.Model):
    state = FSMField(default="new")

    @transition(field=state, source="new", target="published")
    def publish(self):
        pass

    @transition(source="published", field=state)
    def notify_all(self):
        pass

    @transition(source="published", target="hidden", field=state)
    def hide(self):
        pass

    @transition(source="new", target="removed", field=state)
    def remove(self):
        raise Exception("Upss")

    @transition(source=["published", "hidden"], target="stolen", field=state)
    def steal(self):
        pass

    @transition(source="*", target="moderated", field=state)
    def moderate(self):
        pass

    @transition(source="+", target="blocked", field=state)
    def block(self):
        pass

    @transition(source="*", target="", field=state)
    def empty(self):
        pass


class FSMFieldTest(TestCase):
    def setUp(self):
        self.model = BlogPost()

    def test_initial_state_instantiated(self):
        self.assertEqual(self.model.state, "new")

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, "published")

        self.assertTrue(can_proceed(self.model.hide))
        self.model.hide()
        self.assertEqual(self.model.state, "hidden")

    def test_unknown_transition_fails(self):
        self.assertFalse(can_proceed(self.model.hide))
        self.assertRaises(TransitionNotAllowed, self.model.hide)

    def test_state_non_changed_after_fail(self):
        self.assertTrue(can_proceed(self.model.remove))
        self.assertRaises(Exception, self.model.remove)
        self.assertEqual(self.model.state, "new")

    def test_allowed_null_transition_should_succeed(self):
        self.model.publish()
        self.model.notify_all()
        self.assertEqual(self.model.state, "published")

    def test_unknown_null_transition_should_fail(self):
        self.assertRaises(TransitionNotAllowed, self.model.notify_all)
        self.assertEqual(self.model.state, "new")

    def test_multiple_source_support_path_1_works(self):
        self.model.publish()
        self.model.steal()
        self.assertEqual(self.model.state, "stolen")

    def test_multiple_source_support_path_2_works(self):
        self.model.publish()
        self.model.hide()
        self.model.steal()
        self.assertEqual(self.model.state, "stolen")

    def test_star_shortcut_succeed(self):
        self.assertTrue(can_proceed(self.model.moderate))
        self.model.moderate()
        self.assertEqual(self.model.state, "moderated")

    def test_plus_shortcut_succeeds_for_other_source(self):
        """Tests that the '+' shortcut succeeds for a source
        other than the target.
        """
        self.assertTrue(can_proceed(self.model.block))
        self.model.block()
        self.assertEqual(self.model.state, "blocked")

    def test_plus_shortcut_fails_for_same_source(self):
        """Tests that the '+' shortcut fails if the source
        equals the target.
        """
        self.model.block()
        self.assertFalse(can_proceed(self.model.block))
        self.assertRaises(TransitionNotAllowed, self.model.block)

    def test_empty_string_target(self):
        self.model.empty()
        self.assertEqual(self.model.state, "")


class StateSignalsTests(TestCase):
    def setUp(self):
        self.model = BlogPost()
        self.pre_transition_called = False
        self.post_transition_called = False
        pre_transition.connect(self.on_pre_transition, sender=BlogPost)
        post_transition.connect(self.on_post_transition, sender=BlogPost)

    def on_pre_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, source)
        self.pre_transition_called = True

    def on_post_transition(self, sender, instance, name, source, target, **kwargs):
        self.assertEqual(instance.state, target)
        self.post_transition_called = True

    def test_signals_called_on_valid_transition(self):
        self.model.publish()
        self.assertTrue(self.pre_transition_called)
        self.assertTrue(self.post_transition_called)

    def test_signals_not_called_on_invalid_transition(self):
        self.assertRaises(TransitionNotAllowed, self.model.hide)
        self.assertFalse(self.pre_transition_called)
        self.assertFalse(self.post_transition_called)


class TestFieldTransitionsInspect(TestCase):
    def setUp(self):
        self.model = BlogPost()

    def test_in_operator_for_available_transitions(self):
        # store the generator in a list, so we can reuse the generator and do multiple asserts
        transitions = list(self.model.get_available_state_transitions())

        self.assertIn("publish", transitions)
        self.assertNotIn("xyz", transitions)

        # inline method for faking the name of the transition
        def publish():
            pass

        obj = Transition(
            method=publish,
            source="",
            target="",
            on_error="",
            conditions="",
            permission="",
            custom="",
        )

        self.assertTrue(obj in transitions)

    def test_available_conditions_from_new(self):
        transitions = self.model.get_available_state_transitions()
        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set([("*", "moderated"), ("new", "published"), ("new", "removed"), ("*", ""), ("+", "blocked")])
        self.assertEqual(actual, expected)

    def test_available_conditions_from_published(self):
        self.model.publish()
        transitions = self.model.get_available_state_transitions()
        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set(
            [
                ("*", "moderated"),
                ("published", None),
                ("published", "hidden"),
                ("published", "stolen"),
                ("*", ""),
                ("+", "blocked"),
            ]
        )
        self.assertEqual(actual, expected)

    def test_available_conditions_from_hidden(self):
        self.model.publish()
        self.model.hide()
        transitions = self.model.get_available_state_transitions()
        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set([("*", "moderated"), ("hidden", "stolen"), ("*", ""), ("+", "blocked")])
        self.assertEqual(actual, expected)

    def test_available_conditions_from_stolen(self):
        self.model.publish()
        self.model.steal()
        transitions = self.model.get_available_state_transitions()
        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set([("*", "moderated"), ("*", ""), ("+", "blocked")])
        self.assertEqual(actual, expected)

    def test_available_conditions_from_blocked(self):
        self.model.block()
        transitions = self.model.get_available_state_transitions()
        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set([("*", "moderated"), ("*", "")])
        self.assertEqual(actual, expected)

    def test_available_conditions_from_empty(self):
        self.model.empty()
        transitions = self.model.get_available_state_transitions()
        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set([("*", "moderated"), ("*", ""), ("+", "blocked")])
        self.assertEqual(actual, expected)

    def test_all_conditions(self):
        transitions = self.model.get_all_state_transitions()

        actual = set((transition.source, transition.target) for transition in transitions)
        expected = set(
            [
                ("*", "moderated"),
                ("new", "published"),
                ("new", "removed"),
                ("published", None),
                ("published", "hidden"),
                ("published", "stolen"),
                ("hidden", "stolen"),
                ("*", ""),
                ("+", "blocked"),
            ]
        )
        self.assertEqual(actual, expected)
