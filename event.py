from __future__ import annotations

from heapq import heapq
from enum import Enum

from job import Job
from machine import Machine
from operator import Operator


class EventException:
    pass


class EventType(Enum):
    PROCESS_ARRIVAL = 'Process_Arrival'
    HARVEST_ARRIVAL = 'Harvest_Arrival'
    QC_ARRIVAL = 'QC_Arrival'

    PROCESS_DEPARTURE = 'Departure'
    HARVEST_DEPARTURE = 'Departure'
    QC_DEPARTURE = 'Departure'

    START_SETUP = 'Start_Setup'
    END_SETUP = 'End_Setup'

    START_HARVESTING = 'Start_Harvesting'
    END_HARVESTING = 'End_Harvesting'

    START_PROCESSING = 'Start_Processing'
    END_PROCESSING = 'End_Processing'

    START_QC = 'Start_QC'
    END_QC = 'End_QC'

    COLLECT = 'Collect'


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

        self.in_rework = False

    def __str__(self) -> str:
        return f"Event {self.event_type}  at {self.time}"

    def machine(self, machine: Machine) -> Event:
        self.machine = machine
        return self

    def operator(self, operator: Operator) -> Event:
        self.operator = operator
        return self

    def job(self, job: Job) -> Event:
        self.job = job
        return self


# Priority queue for events
class EventQueue:
    def __init__(self):
        self.__buf = []

    def push(self, e: Event):
        heapq.heappush(self.__buf, (e.time, e))

    def pop(self):
        popped = heapq.heappop(self.__buf)
        return popped[1]

    def empty(self):
        return len(self.__buf) == 0
