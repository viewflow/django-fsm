from django.db import models
from django_fsm import FSMField, FSMKeyField, transition


class Application(models.Model):
    """
    Student application need to be approved by dept chair and dean.
    Test workflow
    """

    state = FSMField(default="new")

    @transition(field=state, source="new", target="draft")
    def draft(self):
        pass

    @transition(field=state, source=["new", "draft"], target="dept")
    def to_approvement(self):
        pass

    @transition(field=state, source="dept", target="dean")
    def dept_approved(self):
        pass

    @transition(field=state, source="dept", target="new")
    def dept_rejected(self):
        pass

    @transition(field=state, source="dean", target="done")
    def dean_approved(self):
        pass

    @transition(field=state, source="dean", target="dept")
    def dean_rejected(self):
        pass


class FKApplication(models.Model):
    """
    Student application need to be approved by dept chair and dean.
    Test workflow for FSMKeyField
    """

    state = FSMKeyField("testapp.DbState", default="new", on_delete=models.CASCADE)

    @transition(field=state, source="new", target="draft")
    def draft(self):
        pass

    @transition(field=state, source=["new", "draft"], target="dept")
    def to_approvement(self):
        pass

    @transition(field=state, source="dept", target="dean")
    def dept_approved(self):
        pass

    @transition(field=state, source="dept", target="new")
    def dept_rejected(self):
        pass

    @transition(field=state, source="dean", target="done")
    def dean_approved(self):
        pass

    @transition(field=state, source="dean", target="dept")
    def dean_rejected(self):
        pass


class DbState(models.Model):
    """
    States in DB
    """

    id = models.CharField(primary_key=True, max_length=50)

    label = models.CharField(max_length=255)

    def __unicode__(self):
        return self.label


class BlogPost(models.Model):
    """
    Test workflow
    """

    state = FSMField(default="new", protected=True)

    def can_restore(self, user):
        return user.is_superuser or user.is_staff

    @transition(field=state, source="new", target="published", on_error="failed", permission="testapp.can_publish_post")
    def publish(self):
        pass

    @transition(field=state, source="published")
    def notify_all(self):
        pass

    @transition(
        field=state,
        source="published",
        target="hidden",
        on_error="failed",
    )
    def hide(self):
        pass

    @transition(
        field=state,
        source="new",
        target="removed",
        on_error="failed",
        permission=lambda self, u: u.has_perm("testapp.can_remove_post"),
    )
    def remove(self):
        raise Exception("No rights to delete %s" % self)

    @transition(field=state, source="new", target="restored", on_error="failed", permission=can_restore)
    def restore(self):
        pass

    @transition(field=state, source=["published", "hidden"], target="stolen")
    def steal(self):
        pass

    @transition(field=state, source="*", target="moderated")
    def moderate(self):
        pass

    class Meta:
        permissions = [
            ("can_publish_post", "Can publish post"),
            ("can_remove_post", "Can remove post"),
        ]
