# -*- coding: utf-8 -*-
"""
State tracking functionality for django models
"""
from django_fsm.db.fields.fsmfield import FSMField, FSMKeyField, \
    transition, can_proceed

