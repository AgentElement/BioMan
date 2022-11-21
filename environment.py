import numpy as np

from config import Config
from util import Queue
from op import HarvestOperator, ProcessOperator
from job import Job, Patient
from machine import HarvestMachine, ProcessMachine, QCMachine
from event import Event, EventQueue, EventType


class Environment:
    def __init__(self, config: Config):
        self.clock = 0
        self.job_gen_count = 0
        self.config = config

        self.pending_events = EventQueue()
        self.initial_job_queue = None
        self.populate_initial_events_and_jobs()

        self.events = []
        self.finished_jobs = []

        self.harvest_machine_queue = Queue(
            [HarvestMachine(i) for i in range(config.harvest_machine_count)]
        )

        self.process_machine_queue = Queue(
            [ProcessMachine(i) for i in range(config.harvest_machine_count)]
        )

        self.harvest_operator_queue = Queue(
            [HarvestOperator(i) for i in range(config.harvest_operator_count)]
        )

        self.process_operator_queue = Queue(
            [ProcessOperator(i) for i in range(config.process_operator_count)]
        )

        # If a job is awaiting an operator, it is placed in this queue
        self.harvest_operator_job_queue = Queue()
        self.process_operator_job_queue = Queue()

        # If a job and operator are awaiting a machine, the operator
        # is placed in this queue
        self.harvest_machine_job_queue = Queue()
        self.process_machine_job_queue = Queue()

        self.qc_machine = QCMachine()

        self.qc_job_queue = Queue()

    def get_next_event(self) -> Event:
        next_event = self.pending_events.pop()
        if self.clock < next_event.time:
            self.clock = next_event.clock
        return next_event

    def populate_initial_events_and_jobs(self) -> None:
        jobs = [Job(Patient.random(), i)
                for i in range(self.config.patient_count)]
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
        return self.initial_job_queue

    def assign_jobs_to_operators(self) -> None:
        while job := self.harvest_operator_job_queue.pop():
            if self.harvest_operator_queue.busy():
                break
            operator = self.process_operator_queue.pop()
            operator.job = job
            event = Event(EventType.HARVEST_DEPARTURE, self.clock) \
                .job(job) \
                .operator(operator)
            self.pending_events.push(event)

        while job := self.process_operator_job_queue.pop():
            if self.harvest_operator_queue.busy():
                break
            operator = self.process_operator_queue.pop()
            operator.job = job
            event = Event(EventType.PROCESS_DEPARTURE, self.clock) \
                .job(job) \
                .operator(operator)
            self.pending_events.push(event)

    def assign_operators_to_machines(self) -> None:
        while operator := self.harvest_machine_job_queue.pop():
            if self.harvest_machine_queue.busy():
                break
            machine = self.harvest_machine_queue.pop()
            machine.initialize(operator)
            event = Event(EventType.START_SETUP, self.clock) \
                .job(operator.job) \
                .operator(operator) \
                .machine(machine)
            self.pending_events.push(event)

        while operator := self.process_operator_job_queue.pop():
            if self.process_machine_queue.busy():
                break
            machine = self.process_machine_queue.pop()
            machine.initialize(operator)
            event = Event(EventType.START_SETUP, self.clock) \
                .job(operator.job) \
                .operator(operator) \
                .machine(machine)
            self.pending_events.push(event)

    def simulate(self) -> None:
        while self.clock <= self.config.simulation_time:
            self.assign_jobs_to_operators()
            self.assign_operators_to_machines()
            if self.pending_events.empty():
                break
            event = self.get_next_event()
            print(event)
            self.process_event(event)
            self.events.append(event)

    def process_event(self, event: Event) -> None:
        {
            EventType.HARVEST_ARRIVAL: lambda e: self.harvest_arrival(e),
            EventType.HARVEST_DEPARTURE: lambda e: self.harvest_departure(e),
            EventType.START_HARVEST_SETUP: lambda e: self.start_harvest_setup(e),
            EventType.END_HARVEST_SETUP: lambda e: self.end_harvest_setup(e),
            EventType.START_HARVESTING: lambda e: self.start_harvesting(e),
            EventType.END_HARVESTING: lambda e: self.end_harvesting(e),

            EventType.PROCESS_ARRIVAL: lambda e: self.process_arrival(e),
            EventType.PROCESS_DEPARTURE: lambda e: self.process_departure(e),
            EventType.START_PROCESS_SETUP: lambda e: self.start_process_setup(e),
            EventType.END_PROCESS_SETUP: lambda e: self.end_process_setup(e),
            EventType.START_PROCESSING: lambda e: self.start_processing(e),
            EventType.END_PROCESSING: lambda e: self.end_processing(e),

            EventType.COLLECT: lambda e: self.collect(e),

            EventType.QC_ARRIVAL: lambda e: self.qc_arrival(e),
            EventType.QC_DEPARTURE: lambda e: self.qc_departure(e),
            EventType.START_QC: lambda e: self.start_qc(e),
            EventType.END_QC: lambda e: self.end_qc(e),
        }[event.event_type](event)

    def harvest_arrival(self, event: Event) -> None:
        self.harvest_operator_job_queue.push(event.job)

    def harvest_departure(self, event: Event) -> None:
        self.harvest_machine_job_queue.push(event.job)

    def start_harvest_setup(self, event: Event) -> None:
        event.machine.start_setup()
        setup_duration = np.random.randint(1, 3)
        next_event = Event(EventType.END_SETUP, self.clock + setup_duration) \
            .job(event.job) \
            .operator(event.operator) \
            .machine(event.machine)
        self.pending_events.push(next_event)

    def end_harvest_setup(self, event: Event) -> None:
        event.machine.end_setup()
        next_event = Event(EventType.START_HARVESTING, self.clock) \
            .job(event.job) \
            .machine(event.machine)
        self.harvest_operator_queue.push(event.operator.clear())
        self.pending_events.push(next_event)

    def start_harvesting(self, event: Event) -> None:
        event.machine.start_work()
        harvest_duration = event.job.calculate_harvest_duration()
        next_event = Event(
            EventType.END_HARVESTING, self.clock + harvest_duration) \
            .job(event.job) \
            .machine(event.machine)
        self.pending_events.push(next_event)

    def end_harvesting(self, event: Event) -> None:
        event.machine.end_work()
        event.machine.clear()
        next_event = Event(EventType.PROCESS_ARRIVAL, self.clock) \
            .job(event.job)
        self.harvest_machine_queue.push(event.machine)
        self.pending_events.push(next_event)

    def process_arrival(self, event: Event) -> None:
        self.process_operator_job_queue.push(event)

    def process_departure(self, event: Event) -> None:
        self.process_machine_job_queue.push(event)

    def start_process_setup(self, event: Event) -> None:
        event.machine.start_setup()
        setup_duration = np.random.randint(1, 3)
        next_event = Event(EventType.END_SETUP, self.clock + setup_duration) \
            .job(event.job) \
            .operator(event.operator) \
            .machine(event.machine)
        self.pending_events.push(next_event)

    def end_process_setup(self, event: Event) -> None:
        event.machine.end_setup()
        next_event = Event(EventType.START_PROCESSING, self.clock) \
            .job(event.job) \
            .machine(event.machine)
        self.harvest_operator_queue.push(event.operator.clear())
        self.pending_events.push(next_event)

    def start_processing(self, event: Event) -> None:
        event.machine.start_work()
        process_duration = event.job.calculate_process_duration(self.config)
        next_event = Event(
            EventType.END_PROCESSING, self.clock + process_duration) \
            .job(event.job) \
            .machine(event.machine)
        event.job \
            .set_process_times(self.clock, self.clock + process_duration) \
            .calculate_yield_after_process(self.config)
        self.pending_events.push(next_event)

    def end_processing(self, event: Event) -> None:
        event.machine \
            .end_work() \
            .clear()
        next_event = Event(EventType.COLLECT, self.clock) \
            .job(event.job)
        self.harvest_machine_queue.push(event.machine)
        self.pending_events.push(next_event)

    def collect(self, event: Event) -> None:
        if event.job.process_yield <= 0:
            job = event.job.attempt_rework(self.clock)
            next_event = Event(EventType.HARVEST_ARRIVAL, self.clock).job(job)
        else:
            event.job \
                .set_collect_time(self.clock) \
                .calculate_yield_after_collect(self.clock)
            next_event = Event(EventType.QC_ARRIVAL, self.clock).job(job)
        self.pending_events.push(next_event)

    def qc_arrival(self, event: Event) -> None:
        self.qc_job_queue.push(event.job)
        next_event = Event(EventType.QC_DEPARTURE, self.clock) \
            .job(event.job)
        self.pending_events.push(next_event)

    def qc_departure(self, event: Event) -> None:
        next_event = Event(EventType.START_QC, self.clock) \
            .job(event.job)
        self.pending_events.push(next_event)

    def start_qc(self, event: Event) -> None:
        qc_duration = 0.5
        if self.qc_machine.quality_policy():
            next_event = Event(EventType.END_QC, self.clock + qc_duration) \
                .job(event.job)
            self.pending_events.push(next_event)
        else:
            if event.job.rework_attempts() <= self.config.max_rework_count:
                next_event = Event(EventType.HARVEST_ARRIVAL, self.clock + qc_duration) \
                    .job(event.job.attempt_rework(self.clock))
                self.pending_events.push(next_event)
            else:
                self.finished_jobs.append(event.job)

    def end_qc(self, event: Event) -> None:
        self.finished_jobs.append(event.job)
