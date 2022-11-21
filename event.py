from __future__ import annotations
from functools import total_ordering

import heapq
from enum import Enum

from op import Operator
from job import Job
from machine import Machine

class EventException:
    pass


class EventType(Enum):
    HARVEST_ARRIVAL = 0
    HARVEST_DEPARTURE = 1
    START_HARVEST_SETUP = 2
    END_HARVEST_SETUP = 3
    START_HARVESTING = 4
    END_HARVESTING = 5

    PROCESS_ARRIVAL = 6
    PROCESS_DEPARTURE = 7
    START_PROCESS_SETUP = 8
    END_PROCESS_SETUP = 9
    START_PROCESSING = 10
    END_PROCESSING = 11

    COLLECT = 12

    QC_ARRIVAL = 13
    QC_DEPARTURE = 14
    START_QC = 15
    END_QC = 16


@total_ordering
class Event:
    """
    Event_type includes arrival, harvest, process, finish
    Event is defined as a point on the timeline.
    """

    def __init__(self, event_type: EventType, time: float):
        self.event_type = event_type
        self.time = time

        self.machine = None
        self.operator = None
        self.job = None

    def __str__(self) -> str:
        return f"Event {self.event_type} at {self.time}\n" \
            f"\tMachine: {self.machine}\n" \
            f"\tOperator: {self.operator}\n" \
            f"\tJob: {self.job}\n"

    # This is not a good hash function, but we only need a hash to ensure that
    # events can be ordered (EventQueue requires this)
    def __hash__(self):
        return hash(str(self))

    def __lt__(self: Event, other: Event):
        return self.time < other.time

    def __eq__(self: Event, other: Event):
        return self.time == other.time

    def set_machine(self, machine: Machine) -> Event:
        self.machine = machine
        return self

    def set_operator(self, operator: Operator) -> Event:
        self.operator = operator
        return self

    def set_job(self, job: Job) -> Event:
        self.job = job
        return self


# Priority queue for events
class EventQueue:
    def __init__(self):
        self.__buf = []

    def push(self, e: Event) -> EventQueue:
        heapq.heappush(self.__buf, (e.time, e))
        return self

    def pop(self) -> Event:
        popped = heapq.heappop(self.__buf)
        return popped[1]

    def empty(self) -> bool:
        return len(self.__buf) == 0
