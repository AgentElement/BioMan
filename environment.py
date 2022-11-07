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

        self.processed_job_queue = Queue()

        self.harvested_job_queue = Queue()

        self.done_job_queue = Queue()

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
            event = Event(EventType.ARRIVAL, elapsed_arrival_time).job(job)
            self.pending_events.push(event)
            elapsed_arrival_time += np.random.randint(2, 5)

    def simulate(self):
        while self.clock <= self.config.simulation_time \
                or self.pending_events.empty():
            next_event = self.get_next_event()
            self.process_event(next_event)

        # cleanup

    # TODO: add more events
    def process_event(self, event: Event):
        {
            EventType.ARRIVAL: lambda e: self.process_arrival_event(e),
        }[event.event_type](event)

    def process_arrival_event(self, event: Event):
        if event.event_type != EventType.ARRIVAL:
            raise EventException
