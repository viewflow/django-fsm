# -*- coding: utf-8 -*-
"""
State tracking functionality for django models
"""
from django_fsm.db.fields.fsmfield import (  # NOQA
    FSMField, FSMKeyField, FSMIntegerField,
    TransitionNotAllowed,
    transition,
    can_proceed)

