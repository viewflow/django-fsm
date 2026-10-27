"""Signals emitted by FSM model fields; plain State transitions do not emit them."""

from django.dispatch import Signal


pre_transition = Signal()
post_transition = Signal()
