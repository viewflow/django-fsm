# -*- coding: utf-8 -*-
try:
  from django.db.models.signals import ModelSignal as Signal
except ImportError:
  # Django 1.6 compat
  from django.dispatch import Signal
  
pre_transition = Signal(providing_args=['instance', 'name', 'source', 'target'])
post_transition = Signal(providing_args=['instance', 'name', 'source', 'target', 'exception'])
