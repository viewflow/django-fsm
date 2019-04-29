from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_fsm import FSMField, FSMKeyField, transition, RETURN_VALUE, GET_STATE, ConcurrentTransitionMixin


class Application(models.Model):
    """
    Student application need to be approved by dept chair and dean.
    Test workflow
    """
    state = FSMField(default='new')

    @transition(field=state, source='new', target='draft')
    def draft(self):
        pass

    @transition(field=state, source=['new', 'draft'], target='dept')
    def to_approvement(self):
        pass

    @transition(field=state, source='dept', target='dean')
    def dept_approved(self):
        pass

    @transition(field=state, source='dept', target='new')
    def dept_rejected(self):
        pass

    @transition(field=state, source='dean', target='done')
    def dean_approved(self):
        pass

    @transition(field=state, source='dean', target='dept')
    def dean_rejected(self):
        pass


class FKApplication(models.Model):
    """
    Student application need to be approved by dept chair and dean.
    Test workflow for FSMKeyField
    """
    state = FSMKeyField('testapp.DbState', default='new', on_delete=models.PROTECT)

    @transition(field=state, source='new', target='draft')
    def draft(self):
        pass

    @transition(field=state, source=['new', 'draft'], target='dept')
    def to_approvement(self):
        pass

    @transition(field=state, source='dept', target='dean')
    def dept_approved(self):
        pass

    @transition(field=state, source='dept', target='new')
    def dept_rejected(self):
        pass

    @transition(field=state, source='dean', target='done')
    def dean_approved(self):
        pass

    @transition(field=state, source='dean', target='dept')
    def dean_rejected(self):
        pass


class DbState(models.Model):
    '''
    States in DB
    '''
    id = models.CharField(primary_key=True, max_length=50)

    label = models.CharField(max_length=255)

    def __unicode__(self):
        return self.label


class BlogPost(models.Model):
    """
    Test workflow
    """
    state = FSMField(default='new', protected=True)

    def can_restore(self, user):
        return user.is_superuser or user.is_staff

    @transition(field=state, source='new', target='published',
                on_error='failed', permission='testapp.can_publish_post')
    def publish(self):
        pass

    @transition(field=state, source='published')
    def notify_all(self):
        pass

    @transition(field=state, source='published', target='hidden', on_error='failed',)
    def hide(self):
        pass

    @transition(
        field=state,
        source='new',
        target='removed',
        on_error='failed',
        permission=lambda self, u: u.has_perm('testapp.can_remove_post'))
    def remove(self):
        raise Exception('No rights to delete %s' % self)

    @transition(field=state, source='new', target='restored',
                on_error='failed', permission=can_restore)
    def restore(self):
        pass

    @transition(field=state, source=['published', 'hidden'], target='stolen')
    def steal(self):
        pass

    @transition(field=state, source='*', target='moderated')
    def moderate(self):
        pass

    class Meta:
        permissions = [
            ('can_publish_post', 'Can publish post'),
            ('can_remove_post', 'Can remove post'),
        ]


class BlogPostWithCustomData(models.Model):
    state = FSMField(default='new')

    @transition(field=state, source='new', target='published', conditions=[],
                custom={'label': 'Publish', 'type': '*'})
    def publish(self):
        pass

    @transition(field=state, source='published', target='destroyed',
                custom=dict(label="Destroy", type='manual'))
    def destroy(self):
        pass

    @transition(field=state, source='published', target='review',
                custom=dict(label="Periodic review", type='automated'))
    def review(self):
        pass


class ExceptionalBlogPost(models.Model):
    state = FSMField(default='new')

    @transition(field=state, source='new', target='published', on_error='crashed')
    def publish(self):
        raise Exception('Upss')

    @transition(field=state, source='new', target='deleted')
    def delete(self):
        raise Exception('Upss')


class LockedBlogPost(ConcurrentTransitionMixin, models.Model):
    state = FSMField(default='new', protected=True)
    text = models.CharField(max_length=50)

    @transition(field=state, source='new', target='published')
    def publish(self):
        pass

    @transition(field=state, source='published', target='removed')
    def remove(self):
        pass


class ExtendedBlogPost(LockedBlogPost):
    review_state = FSMField(default='waiting', protected=True)
    notes = models.CharField(max_length=50)

    @transition(field=review_state, source='waiting', target='rejected')
    def reject(self):
        pass


class WorkflowMixin(object):
    @transition(field='state', source="*", target='draft')
    def draft(self):
        pass

    @transition(field='state', source="draft", target='published')
    def publish(self):
        pass


class MixinSupportTestModel(WorkflowMixin, models.Model):
    state = FSMField(default="new")


class Ticket(models.Model):
    pass


class Task(models.Model):
    class STATE:
        NEW = 'new'
        DONE = 'done'

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    causality = GenericForeignKey('content_type', 'object_id')
    state = FSMField(default=STATE.NEW)

    @transition(field=state, source=STATE.NEW, target=STATE.DONE)
    def do(self):
        pass


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


class TestModel(models.Model):
    counter = models.IntegerField(default=0)
    signal_counter = models.IntegerField(default=0)
    state = FSMField(default="SUBMITTED_BY_USER")

    @transition(field=state, source="SUBMITTED_BY_USER", target="REVIEW_USER")
    @transition(field=state, source="SUBMITTED_BY_ADMIN", target="REVIEW_ADMIN")
    @transition(field=state, source="SUBMITTED_BY_ANONYMOUS", target="REVIEW_ANONYMOUS")
    def review(self):
        self.counter += 1


class ObjectPermissionTestModel(models.Model):
    state = FSMField(default="new")

    @transition(field=state, source='new', target='published',
                on_error='failed', permission='testapp.can_publish_objectpermissiontestmodel')
    def publish(self):
        pass

    class Meta:
        permissions = [
            ('can_publish_objectpermissiontestmodel', 'Can publish ObjectPermissionTestModel'),
        ]


class Insect(models.Model):
    class STATE:
        CATERPILLAR = 'CTR'
        BUTTERFLY = 'BTF'

    STATE_CHOICES = ((STATE.CATERPILLAR, 'Caterpillar', 'Caterpillar'),
                     (STATE.BUTTERFLY, 'Butterfly', 'Butterfly'))

    state = FSMField(default=STATE.CATERPILLAR, state_choices=STATE_CHOICES)

    @transition(field=state, source=STATE.CATERPILLAR, target=STATE.BUTTERFLY)
    def cocoon(self):
        pass

    def fly(self):
        raise NotImplementedError

    def crawl(self):
        raise NotImplementedError


class Caterpillar(Insect):
    def crawl(self):
        """
        Do crawl
        """

    class Meta:
        proxy = True


class Butterfly(Insect):
    def fly(self):
        """
        Do fly
        """

    class Meta:
        proxy = True


class BlogPostWithStringField(models.Model):
    state = FSMField(default='new')

    @transition(field='state', source='new', target='published', conditions=[])
    def publish(self):
        pass

    @transition(field='state', source='published', target='destroyed')
    def destroy(self):
        pass

    @transition(field='state', source='published', target='review')
    def review(self):
        pass


class TestExceptTargetTransitionShortcut(models.Model):
    state = FSMField(default='new')

    @transition(field=state, source='new', target='published')
    def publish(self):
        pass

    @transition(field=state, source='+', target='removed')
    def remove(self):
        pass
