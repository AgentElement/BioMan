from __future__ import annotations

import numpy as np

from util import Queueable
from enum import Enum
from job import Job, HarvestJob, ProcessJob, JobStatus
from operator import Operator, HarvestOperator, ProcessOperator


class MachineError(Exception):
    pass


class MachineState(Enum):
    IDLE = 0
    SETUP = 1
    ACTIVE = 2
    BUSY = 3
    DONE = 4


# TODO: set job statuses in machines
class Machine(Queueable):
    def __init__(self, id: int):
        self.state = MachineState.IDLE
        self.operator: Operator = None
        self.job: Job = None
        self.id = id

    def __str__(self) -> str:
        return f"Machine {self.id} in state {self.state.name}"

    def initialize(self, operator: Operator) -> Machine:
        if operator.job is None:
            raise MachineError

        self.operator = operator
        self.job = operator.job
        return self

    def start_setup(self) -> Machine:
        if (self.state != MachineState.IDLE
                or self.operator is None
                or self.job is None):
            raise MachineError

        self.state = MachineState.SETUP
        self.operator.make_busy(True)
        return self

    def end_setup(self) -> Machine:
        if (self.state != MachineState.SETUP
                or self.operator is None
                or self.job is None):
            raise MachineError

        self.state = MachineState.ACTIVE
        self.operator.make_busy(False)
        self.operator = None
        return self

    def start_work(self) -> Machine:
        if (self.state != MachineState.SETUP
                or self.job is None):
            raise MachineError

        self.state = MachineState.BUSY
        return self

    def end_work(self) -> Machine:
        if (self.state != MachineState.BUSY
                or self.job is None):
            raise MachineError

        self.state = MachineState.DONE
        return self

    def clear(self) -> Machine:
        self.state = MachineState.IDLE
        self.operator = None
        self.job = None
        return self


class HarvestMachine(Machine):
    def __init__(self):
        super().__init__()

    def initialize(self, operator: HarvestOperator) -> HarvestMachine:
        super().initialize(operator)
        return self

    def start_setup(self) -> HarvestMachine:
        super().start_setup(self.operator)
        return self
    

class ProcessMachine(Machine):
    def __init__(self):
        super().__init__()

    def initialize(self, operator: ProcessOperator) -> ProcessMachine:
        super().initialize(operator)
        return self

    def start_setup(self, operator: ProcessOperator) -> ProcessMachine:
        super().start_setup(operator)
        return self


class QCMachine:
    def __init__(self):
        super().__init__()

    def quality_policy(self) -> bool:
        return np.random.uniform(0, 1) > 0.95
