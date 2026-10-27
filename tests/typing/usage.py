"""Consumer examples checked by both mypy and pyright."""

from typing import Any

from django.db import models
from django_fsm import (
    ConcurrentTransition,
    ConcurrentTransitionMixin,
    FSMField,
    FSMIntegerField,
    FSMKeyField,
    FSMModelMixin,
    GET_STATE,
    RETURN_VALUE,
    State,
    can_proceed,
    chart,
    has_transition_perm,
    this,
    transition,
)
from django_fsm.signals import post_transition


class Stage(models.TextChoices):
    NEW = "new", "New"
    DONE = "done", "Done"


class Review:
    state = State(Stage, default=Stage.NEW)

    @state.transition(
        source=Stage.NEW,
        target=Stage.DONE,
        conditions=[this.ready],
        permission=this.can_publish,
    )
    def publish(self) -> str:
        return str(self.state)

    def ready(self) -> bool:
        return True

    def can_publish(self, user: Any) -> bool:
        return bool(user)

    @state.on_success()
    def changed(self, method: Any, source: Any, target: Any) -> None:
        pass


class StoredStage(models.Model):
    name: Any = models.CharField(max_length=50)


class Job(FSMModelMixin, ConcurrentTransitionMixin, models.Model):
    status = FSMField(default="new", protected=True)
    phase = FSMIntegerField(default=0)
    key = FSMKeyField(StoredStage, null=True, on_delete=models.PROTECT)

    @transition(
        field=status, source="new", target="running", permission="app.start_job"
    )
    def start(self, value: int = 0) -> int:
        return value

    @transition(field="status", source="running", target="done", on_error="failed")
    def finish(self) -> None:
        pass

    @phase.transition(
        source=0, target=RETURN_VALUE(1, 2), conditions=[lambda job: bool(job.pk)]
    )
    def advance(self, value: int) -> int:
        return value

    @phase.transition(
        source=1, target=GET_STATE(lambda job, value: value, states=[0, 2])
    )
    def select(self, value: int) -> None:
        pass


def use(review: Review, job: Job, user: Any) -> None:
    if review.publish.can_proceed() and review.publish.has_perm(user):
        review.publish()
    chart(Review.state)
    if can_proceed(job.start) and has_transition_perm(job.start, user):
        job.start(1)
    for item in job.get_available_status_transitions():
        print(item.name, item.target)
    try:
        job.save(update_fields=["status"])
    except ConcurrentTransition:
        job.refresh_from_db(fields=["phase"])


def receiver(
    sender: Any, instance: Job, source: Any, target: Any, **kwargs: Any
) -> None:
    pass


post_transition.connect(receiver, sender=Job)
