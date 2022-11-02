from util import BusyQueue, Queue

from config import Config
from job import Job, Patient
from machine import HarvestMachine, ProcessMachine, QCMachine
from operator import HarvestOperator, ProcessOperator
from event import Event, EventQueue


class Environment:
    def __init__(self, config: Config):
        self.clock = 0
        self.job_gen_count = 0
        self.config = config

        self.events = EventQueue()

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

        self.job_queue = Queue(
            [Job(Patient.random()) for _ in range(config.patient_count)]
        )

    def get_event(self):
        first_event = Event()

    def simulate(self):
        while self.clock <= self.config.simulation_time:
            if self.events.empty():
                break
            else:
            pass
