from __future__ import annotations

from util import Queueable
from job import Job


# An operator is a Queueable that can be busy working a machine.
# That's literally it
class Operator(Queueable):
    def __init__(self, id):
        super().__init__()
        self.__busy = False
        self.job: Job = None
        self.id = id

    def __str__(self):
        return f"Operator {self.id}"

    def make_busy(self, busy: bool) -> Operator:
        self.__busy = busy
        return self

    def clear(self) -> Operator:
        self.make_busy(False)
        self.job = None
        return self


class HarvestOperator(Queueable):
    def __init__(self):
        super().__init__()


class ProcessOperator(Queueable):
    def __init__(self):
        super().__init__()
