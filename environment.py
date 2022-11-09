import numpy as np

from util import BusyQueue, Queue
from config import Config
from job import Job, Patient
from machine import HarvestMachine, ProcessMachine, QCMachine
from operator import HarvestOperator, ProcessOperator
from event import Event, EventQueue, EventType, EventException


class Environment:
    def __init__(self, config: Config):
        self.clock = 0
        self.job_gen_count = 0
        self.config = config

        self.pending_events = EventQueue()
        self.initial_job_queue = None
        self.populate_initial_events_and_jobs()

        self.events = []

        self.harvest_machine_queue = BusyQueue(
            [HarvestMachine() for _ in range(config.harvest_machine_count)]
        )

        self.process_machine_queue = BusyQueue(
            [ProcessMachine() for _ in range(config.harvest_machine_count)]
        )

        self.harvest_operator_queue = BusyQueue(
            [HarvestOperator() for _ in range(config.harvest_operator_count)]
        )

        self.process_operator_queue = BusyQueue(
            [ProcessOperator() for _ in range(config.process_operator_count)]
        )

        # When a job is ready to transition to another machine/operator pair,
        # then it is placed in one of these queues.
        self.harvested_job_queue = Queue()
        self.processed_job_queue = Queue()
        self.done_job_queue = Queue()

        self.harvest_operator_job_queue = Queue()
        self.process_operator_job_queue = Queue()

    def get_next_event(self):
        next_event = self.pending_events.pop()
        if self.clock < next_event.time:
            self.clock = next_event.clock
        return next_event

    def populate_initial_events_and_jobs(self):
        jobs = [Job(Patient.random())
                for _ in range(self.config.patient_count)]
        self.initial_job_queue = Queue(jobs)
        elapsed_arrival_time = 0
        for job in jobs:
            if elapsed_arrival_time > self.config.simulation_time:
                break
            job.enter_system(elapsed_arrival_time)
            event = Event(EventType.HARVEST_ARRIVAL,
                          elapsed_arrival_time).job(job)
            self.pending_events.push(event)
            elapsed_arrival_time += np.random.randint(2, 5)

    def simulate(self):
        while self.clock <= self.config.simulation_time \
                or self.pending_events.empty():
            event = self.get_next_event()
            self.process_event(event)
            self.events.append(event)

    def process_event(self, event: Event):
        {
            EventType.PROCESS_ARRIVAL: lambda e: self.process_arrival(e),
            EventType.HARVEST_ARRIVAL: lambda e: self.harvest_arrival(e),
            EventType.QC_ARRIVAL: lambda e: self.qc_arrival(e),

            EventType.PROCESS_DEPARTURE: lambda e: self.process_departure(e),
            EventType.HARVEST_DEPARTURE: lambda e: self.harvest_departure(e),
            EventType.QC_DEPARTURE: lambda e: self.qc_departure(e),

            EventType.START_SETUP: lambda e: self.start_setup(e),
            EventType.END_SETUP: lambda e: self.end_setup(e),

            EventType.START_HARVESTING: lambda e: self.start_harvesting(e),
            EventType.END_HARVESTING: lambda e: self.end_harvesting(e),

            EventType.START_PROCESSING: lambda e: self.start_processing(e),
            EventType.END_PROCESSING: lambda e: self.end_processing(e),

            EventType.START_QC: lambda e: self.start_qc(e),
            EventType.END_QC: lambda e: self.end_qc(e),

            EventType.COLLECT: lambda e: self.collect(e),
        }[event.event_type](event)

    def process_arrival(self, event: Event) -> None:
        pass

    def harvest_arrival(self, event: Event) -> None:
        pass

    def qc_arrival(self, event: Event) -> None:
        pass

    def process_departure(self, event: Event) -> None:
        pass

    def harvest_departure(self, event: Event) -> None:
        pass

    def qc_departure(self, event: Event) -> None:
        pass

    def start_setup(self, event: Event) -> None:
        pass

    def end_setup(self, event: Event) -> None:
        pass

    def start_harvesting(self, event: Event) -> None:
        pass

    def end_harvesting(self, event: Event) -> None:
        pass

    def start_processing(self, event: Event) -> None:
        pass

    def end_processing(self, event: Event) -> None:
        pass

    def start_qc(self, event: Event) -> None:
        pass

    def end_qc(self, event: Event) -> None:
        pass

    def collect(self, event: Event) -> None:
        pass
