"""Django FSM: standalone state machines and Django model state fields."""

from .base import (
    InvalidTargetState,
    NoTransition,
    Transition,
    TransitionConditionsUnmet,
    TransitionNotAllowed,
    State,
)
from .chart import chart
from .fields import (
    ConcurrentTransition,
    ConcurrentTransitionMixin,
    FSMField,
    FSMFieldMixin,
    FSMIntegerField,
    FSMKeyField,
    FSMModelMixin,
    GET_STATE,
    NonInitialStateOnCreate,
    RETURN_VALUE,
    can_proceed,
    has_transition_perm,
    transition,
)
from .this_object import this


__all__ = (
    "TransitionNotAllowed",
    "NoTransition",
    "TransitionConditionsUnmet",
    "InvalidTargetState",
    "State",
    "this",
    "chart",
    "Transition",
    "FSMField",
    "FSMFieldMixin",
    "FSMIntegerField",
    "FSMKeyField",
    "FSMModelMixin",
    "ConcurrentTransition",
    "ConcurrentTransitionMixin",
    "RETURN_VALUE",
    "GET_STATE",
    "NonInitialStateOnCreate",
    "transition",
    "can_proceed",
    "has_transition_perm",
)


__version__ = "5.0.0"


def __getattr__(name):
    if name == "FlowAdminMixin":
        from .admin import FlowAdminMixin

        return FlowAdminMixin
    if name == "FlowViewsMixin":
        from .viewset import FlowViewsMixin

        return FlowViewsMixin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
