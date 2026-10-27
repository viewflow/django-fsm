"""Backward-compatible ``FSMField``, ported from django-fsm.

Reuses the ``Transition``/``TransitionDescriptor``/``TransitionBoundMethod``
core in :mod:`django_fsm.base` -- the field adapter supplies a
storage location (the model instance's own attribute slot) instead of the
``State.propname``-mangled slot a plain :class:`~django_fsm.State` uses,
so a value survives Django's normal field machinery (``pre_save``,
filtering, serialization) as-is.
"""

from __future__ import annotations

import inspect
from functools import partial, partialmethod
from typing import Any, List, Optional, TYPE_CHECKING

from django.db import models
from django.db.models.query_utils import DeferredAttribute

from .base import (
    DEFAULT,
    State,
    StateValue,
    Transition,
    TransitionBoundMethod,
    TransitionDescriptor,
    TransitionMethod,
    TransitionNotAllowed,
)
from .typing import Condition, Permission
from .signals import post_transition, pre_transition

if TYPE_CHECKING:
    # These mixins use Django's APIs but must stay plain mixins at runtime.
    from django.db.models import Field as _FieldBase, Model as _ModelBase
else:
    _FieldBase = _ModelBase = object


class NonInitialStateOnCreate(TransitionNotAllowed):
    """Raised creating a new row through ``FSMField(enforce_initial=True)``
    with a value other than the field's declared default.

    :ivar field: the FSM model field involved.
    :ivar value: the rejected value.
    """

    def __init__(self, field: "FSMFieldMixin", value: Any):
        self.field = field
        self.value = value
        super().__init__(
            f"Cannot create {field.model.__name__}.{field.name} as {value!r};"
            f" new rows must start at the declared initial state"
            f" {field.get_default()!r}"
        )


class ConcurrentTransition(Exception):
    """The persisted state changed after this model observed it."""


class _FSMFieldState(State):
    """A ``State`` whose storage is the owning field's own attribute slot on
    the model instance, instead of a plain ``State``'s private, name-mangled
    ``propname`` -- so the value lives exactly where Django's own field
    machinery expects it (``pre_save``, ``filter()``, serialization).

    Bound to the field, not a fixed attribute name, since ``FSMField.attname``
    and ``FSMField.get_default()`` are only valid after ``contribute_to_class``
    runs -- which happens *after* the class body's ``@field.transition(...)``
    decorators already needed a working ``State`` to register against.
    """

    def __init__(self, field: "FSMFieldMixin"):
        super().__init__(states=None, default=None)
        self._field = field

    @property
    def propname(self) -> str:
        return self._field.attname

    def get(self, instance: Any) -> Any:
        value = DeferredAttribute(self._field).__get__(instance)
        if isinstance(instance, ConcurrentTransitionMixin):
            instance._fsm_initial_states.setdefault(self.propname, value)
        return value

    def set(self, instance: object, value: StateValue) -> None:
        self._field.set_state(instance, value)


class _FSMTransition(Transition):
    def __init__(self, *args, on_error=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_error = on_error

    @property
    def name(self):
        return self.func.__name__

    @property
    def method(self):
        return self.func


class _FSMTransitionInfo(_FSMTransition):
    """Legacy metadata values without changing the engine's sentinels."""

    def __init__(self, item):
        super().__init__(
            item.func,
            "*" if item.source is State.ANY else item.source,
            None if item.target is DEFAULT else item.target,
            item._label,
            item.conditions,
            item.permission,
            item.custom,
            on_error=item.on_error,
        )

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, Transition):
            return self.name == other.func.__name__
        return NotImplemented

    def __hash__(self):
        return hash(self.name)


class _FSMTransitionBoundMethod(TransitionBoundMethod):
    class Wrapper(TransitionBoundMethod.Wrapper):
        parent: Any
        transition: Any

        def begin(self):
            self.pre_sent = False
            try:
                super().begin()
            except Exception as exception:
                if self.pre_sent:
                    self.abort(exception)
                raise

        def before_transition(self):
            # Reading a deferred source state may already select its proxy.
            self.initial_class = type(self.parent._instance)
            self.signal_kwargs = {
                "sender": self.initial_class,
                "instance": self.parent._instance,
                "name": self.transition.name,
                "field": self.parent._state._field,
                "source": self.initial_state,
                "target": (
                    None
                    if self.transition.target is DEFAULT
                    else self.transition.target
                ),
                "method_args": self.caller_args,
                "method_kwargs": self.caller_kwargs,
            }
            pre_transition.send(**self.signal_kwargs)
            self.pre_sent = True

        def abort(self, exception=None):
            self.parent._instance.__class__ = self.initial_class
            super().abort(exception)
            if (
                isinstance(exception, Exception)
                and self.transition.on_error is not None
            ):
                self.parent._state.set(self.parent._instance, self.transition.on_error)
                self.signal_kwargs.update(
                    target=self.transition.on_error, exception=exception
                )
                post_transition.send(**self.signal_kwargs)

        def commit(self, result):
            try:
                super().commit(result)
            except BaseException as exception:
                self.abort(exception)
                raise
            self.signal_kwargs["target"] = (
                None if self.target_state is DEFAULT else self.target_state
            )
            post_transition.send(**self.signal_kwargs)


class _FSMTransitionDescriptor(TransitionDescriptor):
    """Resolve the model field on binding, including inherited mixin methods."""

    def __init__(self, field, func):
        super().__init__(None, func)
        self._field = field

    def __get__(self, instance: Any, owner: Any = None) -> Any:
        if owner is None:
            owner = type(instance)
        name = self._field if isinstance(self._field, str) else self._field.name
        field = owner._meta.get_field(name)
        if not isinstance(field, FSMFieldMixin):
            raise TypeError(f"{owner.__name__}.{name} is not an FSM field")
        if instance is None:
            return TransitionMethod(field._state, self._func, self, owner)
        return _FSMTransitionBoundMethod(field._state, self._func, self, instance)

    def get_transition(self, source_state):
        result = super().get_transition(source_state)
        if result is None:
            result = self._transitions.get("+")
            if result is not None and result.target == source_state:
                return None
        return result


def _has_django_permission(permission, instance, user):
    return user.has_perm(permission, instance) or user.has_perm(permission)


def _field_transition(
    field, source, target, label, conditions, permission, custom, on_error
):
    if target is None:
        raise ValueError(
            "target=None is ambiguous with 'no target'. Omit the target"
            " argument entirely for a transition that doesn't change state."
        )
    if isinstance(permission, str):
        permission = partial(_has_django_permission, permission)

    def decorate(func):
        if isinstance(func, _FSMTransitionDescriptor):
            descriptor = func
            previous = descriptor._field
            previous_name = previous if isinstance(previous, str) else previous.name
            field_name = field if isinstance(field, str) else field.name
            if previous is not field and (
                previous_name is None or previous_name != field_name
            ):
                raise ValueError("Stacked transitions must use the same FSM field")
        else:
            descriptor = _FSMTransitionDescriptor(field, func)
        sources = source if isinstance(source, (list, tuple, set)) else [source]
        for value in sources:
            descriptor.add_transition(
                _FSMTransition(
                    descriptor._func,
                    value,
                    target,
                    label,
                    conditions,
                    permission,
                    custom,
                    on_error=on_error,
                )
            )
        return descriptor

    return decorate


def get_all_FIELD_transitions(instance, field):
    return field.get_all_transitions(type(instance))


def get_available_FIELD_transitions(instance, field):
    for method in field._get_transition_methods(type(instance)):
        bound = getattr(instance, method.slug)
        if bound.can_proceed():
            yield _FSMTransitionInfo(
                method._descriptor.get_transition(field.get_state(instance))
            )


def get_available_user_FIELD_transitions(instance, user, field):
    for item in get_available_FIELD_transitions(instance, field):
        if item.has_perm(instance, user):
            yield item


class FSMFieldMixin(_FieldBase):
    """State stored in a Django column, with optional assignment protection.

    ``protected=True`` blocks reassignment after initialization. Transitions
    write through the state adapter instead. ``enforce_initial=True`` checks
    inserted rows against the field default, including ``bulk_create()``.
    Raw SQL and fixture loading bypass that check. Both options default to
    False and are preserved by field cloning and migrations.
    """

    def __init__(
        self,
        *args: Any,
        protected: bool = False,
        enforce_initial: bool = False,
        state_choices=None,
        **kwargs: Any,
    ):
        self.protected = protected
        self.enforce_initial = enforce_initial
        self.state_choices = tuple(state_choices) if state_choices is not None else None
        self.state_proxy = {}
        if self.state_choices is not None:
            if kwargs.get("choices") is not None:
                raise ValueError("Use either choices or state_choices, not both")
            kwargs["choices"] = [
                (state, label) for state, label, _ in self.state_choices
            ]
            self.state_proxy = {state: proxy for state, _, proxy in self.state_choices}
        self._state = _FSMFieldState(self)
        super().__init__(*args, **kwargs)

    def __deepcopy__(self, memo: dict) -> Any:
        field = super().__deepcopy__(memo)
        field._state = _FSMFieldState(field)
        return field

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.protected:
            kwargs["protected"] = True
        if self.enforce_initial:
            kwargs["enforce_initial"] = True
        if self.state_choices is not None:
            kwargs.pop("choices", None)
            kwargs["state_choices"] = self.state_choices
        return name, path, args, kwargs

    def contribute_to_class(
        self, cls: type, name: str, private_only: bool = False, **kwargs: Any
    ) -> None:
        super().contribute_to_class(cls, name, private_only=private_only, **kwargs)
        setattr(cls, self.attname, self)
        for prefix, helper in (
            ("get_all", get_all_FIELD_transitions),
            ("get_available", get_available_FIELD_transitions),
            ("get_available_user", get_available_user_FIELD_transitions),
        ):
            setattr(
                cls, f"{prefix}_{name}_transitions", partialmethod(helper, field=self)
            )

    def get_state(self, instance):
        return self._state.get(instance)

    def set_state(self, instance: Any, value: Any) -> None:
        if (
            isinstance(instance, ConcurrentTransitionMixin)
            and not instance._state.adding
            and not getattr(instance, "_fsm_refreshing", False)
            and self.attname not in instance._fsm_initial_states
        ):
            self.get_state(instance)
        self.set_proxy(instance, value)
        storage: Any = instance.__dict__
        storage[self.attname] = value

    def set_proxy(self, instance, value):
        if value not in self.state_proxy:
            return
        reference = self.state_proxy[value]
        if "." in reference:
            app_label, model_name = reference.split(".", 1)
        else:
            app_label, model_name = self.model._meta.app_label, reference
        proxy = instance._meta.apps.get_model(app_label, model_name)
        if (
            not proxy._meta.proxy
            or proxy._meta.concrete_model is not instance._meta.concrete_model
        ):
            raise ValueError(
                f"{reference} must be a proxy of {instance._meta.concrete_model.__name__}"
            )
        instance.__class__ = proxy

    def _get_transition_methods(self, owner):
        for _, method in inspect.getmembers(
            owner, lambda attr: isinstance(attr, TransitionMethod)
        ):
            if getattr(method._state, "_field", None) is self:
                yield method

    def get_all_transitions(self, owner):
        for method in self._get_transition_methods(owner):
            for item in method.get_transitions():
                yield _FSMTransitionInfo(item)

    def __get__(self, instance: Optional[object], owner: Optional[type] = None) -> Any:
        if instance is None:
            return self
        return self._state.get(instance)

    def __set__(self, instance: object, value: StateValue) -> None:
        if self.protected and self.attname in instance.__dict__:
            raise AttributeError(
                f"Direct assignment to '{self.attname}' is not allowed;"
                " use a transition method instead"
            )
        self.set_state(instance, value)

    def pre_save(self, model_instance: models.Model, add: bool) -> Any:
        value = super().pre_save(model_instance, add)
        if self.enforce_initial and add and value != self.get_default():
            raise NonInitialStateOnCreate(self, value)
        return value

    def transition(
        self,
        source: StateValue,
        target: Optional[StateValue] = DEFAULT,
        label: Optional[str] = None,
        conditions: Optional[List[Condition]] = None,
        permission: Optional[Permission | str] = DEFAULT,
        custom: Optional[Any] = None,
        on_error: Optional[StateValue] = None,
    ) -> Any:
        return _field_transition(
            self, source, target, label, conditions, permission, custom, on_error
        )


class FSMField(FSMFieldMixin, models.CharField):
    """A char state column with Viewflow transitions; max_length defaults to 50."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 50)
        super().__init__(*args, **kwargs)


class FSMIntegerField(FSMFieldMixin, models.IntegerField):
    """An integer state column with the same transition API as FSMField."""


class FSMKeyField(FSMFieldMixin, models.ForeignKey):
    """A foreign key whose model attribute exposes the state key, not an object."""

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        super().contribute_to_class(cls, name, private_only=private_only, **kwargs)
        setattr(cls, self.name, self)

    def set_state(self, instance, value):
        if isinstance(value, models.Model):
            if not isinstance(value, self.remote_field.model):
                raise ValueError(
                    f"Expected an instance of {self.remote_field.model.__name__}"
                )
            value = getattr(value, self.target_field.attname)
            if value is None:
                raise ValueError("Cannot assign an unsaved state object")
        value = self.target_field.to_python(value)
        super().set_state(instance, value)

    def set_cached_value(self, instance, value):
        # There is no forward object accessor: both name and attname return
        # the key. A related-object cache would make Model.save() treat that
        # scalar as a model instance after select_related().
        pass


class FSMModelMixin(_ModelBase):
    """Refresh non-deferred, unprotected fields by default, as in django-fsm."""

    if TYPE_CHECKING:

        def __getattr__(self, name: str) -> Any:
            """Field-name-specific helpers are attached to models dynamically."""
            raise AttributeError(name)

    def refresh_from_db(
        self,
        using: Any = None,
        fields: Any = None,
        from_queryset: Any = None,
        **kwargs: Any,
    ) -> Any:
        if not fields:
            deferred = self.get_deferred_fields()
            fields = [
                field.attname
                for field in self._meta.concrete_fields
                if field.attname not in deferred
                and not (isinstance(field, FSMFieldMixin) and field.protected)
            ]
        if from_queryset is not None:
            kwargs["from_queryset"] = from_queryset
        return super().refresh_from_db(using=using, fields=fields, **kwargs)


class ConcurrentTransitionMixin(_ModelBase):
    """Compare observed FSM states in the UPDATE predicate before saving.

    Save in a transaction to roll back other database changes on conflict.
    Only state columns are compared; this is not a general model version.
    """

    def __init__(self, *args, **kwargs):
        self._fsm_initial_states = {}
        super().__init__(*args, **kwargs)
        self._update_initial_state()

    if TYPE_CHECKING:

        def __getattr__(self, name: str) -> Any:
            """Field-name-specific helpers are attached to models dynamically."""
            raise AttributeError(name)

    @property
    def state_fields(self):
        return tuple(
            field
            for field in self._meta.concrete_fields
            if isinstance(field, FSMFieldMixin)
        )

    def _update_initial_state(self, fields=None):
        for field in self.state_fields:
            if (
                fields is not None
                and field.name not in fields
                and field.attname not in fields
            ):
                continue
            if field.attname in self.__dict__:
                self._fsm_initial_states[field.attname] = self.__dict__[field.attname]

    def _do_update(
        self,
        base_qs,
        using,
        pk_val,
        values,
        update_fields,
        forced_update,
        *args,
        **kwargs,
    ):
        state_fields = [
            field for field in self.state_fields if field.model == base_qs.model
        ]
        missing = [
            field.attname
            for field in state_fields
            if field.attname not in self._fsm_initial_states
        ]
        if missing:
            # Deferred states that have never been observed acquire a baseline
            # at save time. Read them together without loading model attributes.
            initial = base_qs.using(using).filter(pk=pk_val).values(*missing).first()
            if initial is not None:
                self._fsm_initial_states.update(initial)
        state_filter = {
            field.attname: self._fsm_initial_states[field.attname]
            for field in state_fields
            if field.attname in self._fsm_initial_states
        }
        updated = super()._do_update(
            base_qs.filter(**state_filter),
            using,
            pk_val,
            values,
            update_fields,
            forced_update,
            *args,
            **kwargs,
        )
        if not updated and base_qs.using(using).filter(pk=pk_val).exists():
            raise ConcurrentTransition(
                "Cannot save object: its state has changed since it was observed"
            )
        return updated

    def refresh_from_db(
        self,
        using: Any = None,
        fields: Any = None,
        from_queryset: Any = None,
        **kwargs: Any,
    ) -> Any:
        if fields is None:
            refreshed = set(self.__dict__)
            if isinstance(self, FSMModelMixin):
                refreshed.difference_update(
                    field.attname for field in self.state_fields if field.protected
                )
        else:
            fields = frozenset(fields)
            refreshed = fields
        previous = getattr(self, "_fsm_refreshing", False)
        self._fsm_refreshing = True
        if from_queryset is not None:
            kwargs["from_queryset"] = from_queryset
        try:
            result = super().refresh_from_db(using=using, fields=fields, **kwargs)
        finally:
            self._fsm_refreshing = previous
        self._update_initial_state(refreshed)
        return result

    def save(self, *args, **kwargs):
        # Django 5.2 still accepts update_fields as the fourth positional
        # argument; newer Django versions accept it only as a keyword.
        fields = args[3] if len(args) > 3 else kwargs.get("update_fields")
        if fields is not None:
            fields = frozenset(fields)
            if len(args) > 3:
                args = (*args[:3], fields, *args[4:])
            else:
                kwargs["update_fields"] = fields
        elif not self._state.adding:
            fields = set(self.__dict__)
        result = super().save(*args, **kwargs)
        self._update_initial_state(fields)
        return result


RETURN_VALUE = State.RETURN_VALUE
GET_STATE = State.GET_STATE


def transition(
    field: FSMFieldMixin | str,
    source: StateValue = "*",
    target: Optional[StateValue] = DEFAULT,
    on_error: Optional[StateValue] = None,
    conditions: Optional[List[Condition]] = None,
    permission: Optional[Permission | str] = None,
    custom: Optional[Any] = None,
    *,
    label: Optional[str] = None,
) -> Any:
    """django-fsm-compatible decorator: ``@transition(field=state, source=..., target=...)``.

    Supports field objects or names, wildcard sources and Django permission
    names. Transition execution follows Viewflow semantics.
    """
    if isinstance(source, (list, tuple, set)):
        source = [State.ANY if value == "*" else value for value in source]
    elif source == "*":
        source = State.ANY
    if target is None:
        target = DEFAULT
    return _field_transition(
        field, source, target, label, conditions, permission, custom, on_error
    )


def can_proceed(
    bound_method: TransitionBoundMethod, check_conditions: bool = True
) -> bool:
    """Check the source state and, optionally, the transition's conditions."""
    return bound_method.can_proceed(check_conditions=check_conditions)


def has_transition_perm(bound_method: TransitionBoundMethod, user: Any) -> bool:
    """Check the source state, conditions and the user's permission."""
    return bound_method.can_proceed() and bound_method.has_perm(user)
