# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import wraps
from django.db import models

class FSMMeta(object):
    def __init__(self):
        self.transitions = defaultdict()

    def get_state_field(self, instance):
        fields = [field for field in instance._meta.fields if isinstance(field, FSMField)]
        found = len(fields)
        if found == 0:
            raise TypeError("No FSMField found in model")
        elif found > 1:
            raise TypeError("More than one FSMField found in model, please specify field name in transition decorator")
        return fields[0]
        
    def current_state(self, instance):
        field_name = self.get_state_field(instance).name
        return getattr(instance, field_name)
        
    def has_transition(self, instance):
        return self.transitions.has_key(self.current_state(instance))

    def to_next_state(self, instance):
        field_name = self.get_state_field(instance).name
        curr_state = getattr(instance, field_name)
        setattr(instance, field_name, self.transitions[curr_state])


def transition(source='*', target=None, save=False):
    def inner_transition(func):
        if not hasattr(func, '_django_fsm'):
            setattr(func, '_django_fsm', FSMMeta())

        func._django_fsm.transitions[source] = target

        @wraps(func)
        def _change_state(instance, *args, **kwargs):            
            meta = func._django_fsm
            if not meta.has_transition(instance):
                raise NotImplementedError("Can't switch from state '%s' using method '%s'" % (meta.current_state(instance), func.func_name))
            
            func(instance, *args, **kwargs)

            meta.to_next_state(instance)
            if save:
                instance.save()
        
        return _change_state
    
    if not target:
        raise ValueError("Result state not specified")
    
    return inner_transition



class FSMField(models.Field):
    """
    Enabels State Machine support for Django model

    """
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, initial_state = None, *args, **kwargs):
        kwargs['max_length'] = 50
        super(FSMField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'CharField'

