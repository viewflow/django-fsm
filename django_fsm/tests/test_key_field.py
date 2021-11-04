from django.db import models
from django.test import TestCase
from django_fsm import FSMKeyField, TransitionNotAllowed, transition, can_proceed


FK_AVAILABLE_STATES = (
    ("New", "_NEW_"),
    ("Published", "_PUBLISHED_"),
    ("Hidden", "_HIDDEN_"),
    ("Removed", "_REMOVED_"),
    ("Stolen", "_STOLEN_"),
    ("Moderated", "_MODERATED_"),
)


class DBState(models.Model):
    id = models.CharField(primary_key=True, max_length=50)

    label = models.CharField(max_length=255)

    def __unicode__(self):
        return self.label

    class Meta:
        app_label = "django_fsm"


class FKBlogPost(models.Model):
    state = FSMKeyField(DBState, default="new", protected=True, on_delete=models.CASCADE)

    @transition(field=state, source="new", target="published")
    def publish(self):
        pass

    @transition(field=state, source="published")
    def notify_all(self):
        pass

    @transition(field=state, source="published", target="hidden")
    def hide(self):
        pass

    @transition(field=state, source="new", target="removed")
    def remove(self):
        raise Exception("Upss")

    @transition(field=state, source=["published", "hidden"], target="stolen")
    def steal(self):
        pass

    @transition(field=state, source="*", target="moderated")
    def moderate(self):
        pass

    class Meta:
        app_label = "django_fsm"


class FSMKeyFieldTest(TestCase):
    def setUp(self):
        for item in FK_AVAILABLE_STATES:
            DBState.objects.create(pk=item[0], label=item[1])
        self.model = FKBlogPost()

    def test_initial_state_instatiated(self):
        self.assertEqual(
            self.model.state,
            "new",
        )

    def test_known_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.assertEqual(self.model.state, "published")

        self.assertTrue(can_proceed(self.model.hide))
        self.model.hide()
        self.assertEqual(self.model.state, "hidden")

    def test_unknow_transition_fails(self):
        self.assertFalse(can_proceed(self.model.hide))
        self.assertRaises(TransitionNotAllowed, self.model.hide)

    def test_state_non_changed_after_fail(self):
        self.assertTrue(can_proceed(self.model.remove))
        self.assertRaises(Exception, self.model.remove)
        self.assertEqual(self.model.state, "new")

    def test_allowed_null_transition_should_succeed(self):
        self.assertTrue(can_proceed(self.model.publish))
        self.model.publish()
        self.model.notify_all()
        self.assertEqual(self.model.state, "published")

    def test_unknow_null_transition_should_fail(self):
        self.assertRaises(TransitionNotAllowed, self.model.notify_all)
        self.assertEqual(self.model.state, "new")

    def test_mutiple_source_support_path_1_works(self):
        self.model.publish()
        self.model.steal()
        self.assertEqual(self.model.state, "stolen")

    def test_mutiple_source_support_path_2_works(self):
        self.model.publish()
        self.model.hide()
        self.model.steal()
        self.assertEqual(self.model.state, "stolen")

    def test_star_shortcut_succeed(self):
        self.assertTrue(can_proceed(self.model.moderate))
        self.model.moderate()
        self.assertEqual(self.model.state, "moderated")


"""
TODO FIX it
class BlogPostStatus(models.Model):
    name = models.CharField(max_length=10, unique=True)
    objects = models.Manager()

    class Meta:
        app_label = 'django_fsm'


class BlogPostWithFKState(models.Model):
    status = FSMKeyField(BlogPostStatus, default=lambda: BlogPostStatus.objects.get(name="new"))

    @transition(field=status, source='new', target='published')
    def publish(self):
        pass

    @transition(field=status, source='published', target='hidden')
    def hide(self):
        pass


class BlogPostWithFKStateTest(TestCase):
    def setUp(self):
        BlogPostStatus.objects.create(name="new")
        BlogPostStatus.objects.create(name="published")
        BlogPostStatus.objects.create(name="hidden")
        self.model = BlogPostWithFKState()

    def test_known_transition_should_succeed(self):
        self.model.publish()
        self.assertEqual(self.model.state, 'published')

        self.model.hide()
        self.assertEqual(self.model.state, 'hidden')

    def test_unknow_transition_fails(self):
        self.assertRaises(TransitionNotAllowed, self.model.hide)
"""
