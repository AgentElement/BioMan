from util import Queueable
from enum import Enum
from job import Job, HarvestJob, ProcessJob, JobState
from operator import Operator, HarvestOperator, ProcessOperator


class MachineError(Exception):
    pass


class MachineState(Enum):
    IDLE = 0
    SETUP = 1
    ACTIVE = 2
    BUSY = 3
    DONE = 4


class Machine(Queueable):
    def __init__(self):
        self.state = MachineState.IDLE
        self.operator = None
        self.job = None

    def start_setup(self, job: Job, operator: Operator):
        self.state = MachineState.SETUP
        self.operator = operator.make_busy(True)
        self.job = job.set_state(JobState.SETUP)
        return self

    def end_setup(self):
        if (self.state != MachineState.SETUP
                or self.operator is None
                or self.job is None):
            raise MachineError

        self.state = MachineState.ACTIVE
        self.job.set_state(JobState.IDLE)
        self.operator.make_busy(False)
        return self

    def start_work(self):
        if (self.state != MachineState.SETUP
                or self.operator is None
                or self.job is None):
            raise MachineError

        self.state = MachineState.BUSY
        self.job.set_state(JobState.BUSY)
        return self

    def end_work(self):
        if (self.state != MachineState.BUSY
                or self.operator is None
                or self.job is None):
            raise MachineError

        self.state = MachineState.DONE
        self.job.set_state(JobState.IDLE)
        return self

    def clear(self):
        self.state = MachineState.IDLE
        self.operator = None
        self.job = None


class HarvestMachine(Machine):
    def __init__(self):
        super().__init__()

    def start_setup(self, job: HarvestJob, operator: HarvestOperator):
        super().start_setup(job, operator)
        return self


class ProcessMachine(Machine):
    def __init__(self):
        super().__init__()

    def start_setup(self, job: ProcessJob, operator: ProcessOperator):
        super().start_setup(job, operator)
        return self


class QCMachine(Machine):
    def __init__(self):
        super().__init__()
