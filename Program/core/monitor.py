# core/monitor.py
"""
Monitor encapsulates all non-GUI behaviour.
It might talk to sensors, databases or REST APIs.
Just serves random demo data for now.
"""
from __future__ import annotations
import random


class Monitor:
    def __init__(self) -> None:
        self._calls = 0  # how many times get_data() was requested

    # --------------------------------------------------------
    def get_data(self) -> list[int]:
        """Return five random integers between 1 and 10."""
        self._calls += 1
        return [random.randint(1, 10) for _ in range(5)]

    # --------------------------------------------------------
    def call_count(self) -> int:
        """Return how many times data has been requested."""
        return self._calls
