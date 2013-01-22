# -*- coding: utf-8 -*-
# pylint: disable=W0212, R0904
"""
State tracking functionality for django models
"""
import sys
import warnings
from collections import defaultdict
from functools import wraps
from django.db import models
from django.utils.functional import curry
from django_fsm.signals import pre_transition, post_transition


PY3K = sys.version_info[0] == 3


# South support; see http://south.aeracode.org/docs/tutorial/part4.html#simple-inheritance
try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r"^django_fsm\.db\.fields\.fsmfield\.FSMField"])
    add_introspection_rules([], [r"^django_fsm\.db\.fields\.fsmfield\.FSMKeyField"])


class TransitionNotAllowed(Exception):
    """Raise when a transition is not allowed"""


class FSMMeta(object):
    """
    Models methods transitions meta information
    """
    def __init__(self, field=None):
        self.field = field
        self.transitions = defaultdict()
        self.conditions  = defaultdict()

    def add_transition(self, source, target, conditions=[]):
        if source in self.transitions:
            raise AssertionError('Duplicate transition for %s state' % source)

        self.transitions[source] = target
        self.conditions[source] = conditions


    def _get_state_field(self, instance):
        """
        Lookup for FSMField in django model instance
        """
        if not self.field:
            fields = [field for field in instance._meta.fields
                      if isinstance(field, FSMField) or isinstance(field, FSMKeyField)]
            found = len(fields)
            if found == 0:
                raise TypeError("No FSMField found in model")
            elif found > 1:
                raise TypeError("More than one FSMField found in model")
            self.field = fields[0]
        return self.field

    def current_state(self, instance):
        """
        Return current state of Django model
        """
        field_name = self._get_state_field(instance).name
        return getattr(instance, field_name)

    def next_state(self, instance):
        curr_state = self.current_state(instance)

        result = None
        try:
            result = self.transitions[curr_state]
        except KeyError:
            result = self.transitions['*']
        return result

    def has_transition(self, instance):
        """
        Lookup if any transition exists from current model state
        """
        return self.current_state(instance) in self.transitions or '*' in self.transitions

    def conditions_met(self, instance):
        """
        Check if all conditions has been met
        """
        state = self.current_state(instance)
        if state not in self.conditions:
           state = '*'
 
        if all(map(lambda f: f(instance), self.conditions[state])):
                return True
        return False

    def to_next_state(self, instance):
        """
        Switch to next state
        """
        field_name = self._get_state_field(instance).name
        state = self.next_state(instance)

        if state:
            instance.__dict__[field_name] = state


def transition(field=None, source='*', target=None, save=False, conditions=[]):
    """
    Method decorator for mark allowed transition

    Set target to None if current state need to be validated and not
    changed after function call
    """
    if field is None:
        warnings.warn("Non explicit field transition support going to be removed", DeprecationWarning, stacklevel=2)
    
    # pylint: disable=C0111
    def inner_transition(func):        
        if not hasattr(func, '_django_fsm'):
            setattr(func, '_django_fsm', FSMMeta(field=field))

            @wraps(func)
            def _change_state(instance, *args, **kwargs):
                meta = func._django_fsm
                if not (meta.has_transition(instance) and  meta.conditions_met(instance)):
                    raise TransitionNotAllowed("Can't switch from state '%s' using method '%s'" % (meta.current_state(instance), func.__name__))

                source_state = meta.current_state(instance)

                pre_transition.send(
                    sender = instance.__class__,
                    instance = instance,
                    name = func.__name__,
                    source = source_state,
                    target = meta.next_state(instance))
 	
                result = func(instance, *args, **kwargs)

                meta.to_next_state(instance)
                if save:
                    instance.save()

                post_transition.send(
                    sender = instance.__class__,
                    instance = instance,
                    name = func.__name__,
                    source = source_state,
                    target = meta.current_state(instance))
                return result
        else:
            _change_state = func

        if isinstance(source, (list, tuple)):
            for state in source:
                func._django_fsm.add_transition(state, target, conditions)
        else:
            func._django_fsm.add_transition(source, target, conditions)

        if field:
            field.transitions.append(_change_state)
        return _change_state

    return inner_transition


def can_proceed(bound_method):
    """
    Returns True if model in state allows to call bound_method
    """
    if not hasattr(bound_method, '_django_fsm'):
        raise TypeError('%s method is not transition' % bound_method.im_func.__name__)

    meta = bound_method._django_fsm
    if not PY3K:
        im_self = getattr(bound_method, 'im_self', None)
    else:
        im_self = getattr(bound_method, '__self__', None)
    return meta.has_transition(im_self) and meta.conditions_met(im_self)


def get_available_FIELD_transitions(instance, field):
    curr_state = getattr(instance, field.name)
    result = []
    for transition in field.transitions:
        meta = transition._django_fsm
        if meta.has_transition(instance) and meta.conditions_met(instance):
            try:
                result.append((meta.transitions[curr_state], transition))
            except KeyError:
                result.append((meta.transitions['*'], transition))
    return result


class FSMFieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')
        return obj.__dict__[self.field.name]

    def __set__(self, instance, value):
        if self.field.protected and self.field.name in instance.__dict__:
            raise AttributeError('Direct %s modification is not allowed' % self.field.name)
        instance.__dict__[self.field.name] = self.field.to_python(value)


class FSMField(models.Field):
    """
    State Machine support for Django model

    """
    descriptor_class = FSMFieldDescriptor

    def __init__(self, *args, **kwargs):
        self.protected = kwargs.pop('protected', False)
        kwargs.setdefault('max_length', 50)
        super(FSMField, self).__init__(*args, **kwargs)
        self.transitions = []

    def contribute_to_class(self, cls, name):
        super(FSMField,self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))
        if self.transitions:
            setattr(cls, 'get_available_%s_transitions' % self.name, curry(get_available_FIELD_transitions, field=self))

    def get_internal_type(self):
        return 'CharField'


class FSMKeyField(models.ForeignKey):
    """
    State Machine support for Django model

    """
