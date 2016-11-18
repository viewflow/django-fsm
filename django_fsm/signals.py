# -*- coding: utf-8 -*-
from django.db.models.signals import ModelSignal

pre_transition = ModelSignal(providing_args=['instance', 'name', 'source', 'target'])
post_transition = ModelSignal(providing_args=['instance', 'name', 'source', 'target', 'exception'])
