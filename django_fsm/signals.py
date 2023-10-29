from __future__ import annotations

from django.dispatch import Signal

pre_transition = Signal()
post_transition = Signal()
