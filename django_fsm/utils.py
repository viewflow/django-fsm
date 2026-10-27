"""Sentinel objects shared by Django FSM and Viewflow."""

from typing import Any


class MARKER(object):
    def __init__(self, marker: str):
        self.marker = marker

    def __iter__(self):
        return iter(())

    def __repr__(self):
        return self.marker

    def __lt__(self, other) -> bool:
        return self.marker < str(other)


DEFAULT: Any = MARKER("DEFAULT")
