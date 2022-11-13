from __future__ import annotations

import random

from scipy import stats
import numpy as np

from enum import Enum
from util import Queueable
from config import Config, PatientConfig


class JobError(Exception):
    pass


class P_Gender(Enum):
    MALE = 0
    FEMALE = 1


class P_Type(Enum):
    # Each value associated with the enum is the yield multiplier. See
    # calculate_yield() below
    BAD = 0.5
    AVERAGE = 0.8
    GOOD = 1.0


class Patient:
    def __init__(self,
                 gender: P_Gender,
                 ptype: P_Type,
                 pconfig: PatientConfig):
        self.gender = gender
        self.ptype = ptype
        self.blood_volume = np.random.uniform(
            low=pconfig.blood_vol_range[gender.value].low,
            high=pconfig.blood_vol_range[gender.value].high
        )
        self.target_blood_count = pconfig.conversion_factor * self.blood_volume
        self.pconfig = pconfig

    @staticmethod
    def random(pconfig: PatientConfig):
        """Generate a random patient"""
        gr = pconfig.gender_ratio
        gender = random.choices(list(P_Gender), weights=[gr, 1 - gr])[0]
        ptype = random.choices(list(P_Type), weights=pconfig.patient_rates)[0]
        return Patient(gender, ptype, pconfig)

    def __str__(self) -> str:
        return f"Patient [{self.gender.name}, {self.ptype.name}, " \
            f"{self.blood_volume}, {self.target_blood_count}]"


class JobStatus(Enum):
    IDLE = 0
    AWAIT_HARVEST = 1
    HARVESTING = 2
    HARVESTED = 3
    AWAIT_PROCESS = 4
    PROCESSING = 5
    PROCESSED = 6
    DONE = 5


class Job(Queueable):
    def __init__(self, patient: Patient, id: int):
        super().__init__()
        self.patient = patient
        self.start_process_time = -1
        self.end_process_time = -1
        self.collect_time = -1
        self.rework_times = []
        self.status = JobStatus.IDLE
        self.process_yield = 0
        self.id = id

    def __str__(self):
        return f"Job {self.id}\n"\
                f"\t with patient :{self.patient}"

    def set_status(self, status: JobStatus) -> Job:
        self.status = status
        return self

    def harvest_yield(self) -> float:
        return 0.8 * self.patient.target_blood_count

    def attempt_rework(self, rework_time: float) -> Job:
        self.process_time = -1
        self.collect_time = -1
        self.status = JobStatus.IDLE
        self.process_yield = 0
        self.rework_times.append(rework_time)
        return self

    def rework_attempts(self) -> int:
        return len(self.rework_times)

    def set_process_times(self, start: float, end: float) -> Job:
        self.start_process_time = start
        self.end_process_time = end
        return self

    def set_collect_time(self, clock: float) -> Job:
        self.collect_time = clock
        return self

    @staticmethod
    def truncated_norm(lower, mu, sigma) -> float:
        """
        Generates a random number from a truncated normal distribution.

        Parameters:
        lower(float): a lower bound for the disribution
        mu (float): the desired mean
        sigma (float): the desired standard deviation to use to generate the
                       distribution.

        Returns:
        float: randomly genereated number.
        """
        upper = mu + (mu - lower)
        # Generates a random variable/randomizer based on a truncated normal
        # distribution.
        X = stats.truncnorm(
            (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
        # Genereates an array of random numbers of size 1 and grabs the first
        # number from the array.
        res = X.rvs(1)[0]
        return res

    def targets(self, config: Config) -> tuple(float, float, float, float):
        target_bc = self.patient.target_blood_count
        target_low = target_bc / config.slope.low
        target_high = target_low + config.delta_t
        target_zero = target_high + target_bc / config.slope.high

        return target_low, target_high, target_zero

    def calculate_harvest_duration(self) -> int:
        return np.random.randint(6, 9)

    def calculate_process_duration(self, config: Config) -> float:
        target_bc, target_low, target_high, target_zero = self.targets(config)
        process_duration = random.choices([
            np.random.uniform(0, target_low),
            np.random.uniform(target_low, target_high),
            np.random.uniform(target_high, target_zero + 4)],
            weights=self.mfg_dura_perc)[0]
        process_duration_in_hours = process_duration * 24
        return process_duration_in_hours

    def calculate_yield(self, config: Config) -> float:
        if self.status not in [JobStatus.PROCESSED, JobStatus.DONE]:
            raise JobError

        duration = self.collect_time - self.process_time

        target_bc = self.patient.target_blood_count
        target_low, target_high, target_zero = self.targets(config)

        if duration <= target_low:
            p_yield = config.slope.low * duration
        elif duration > target_low and duration <= target_high:
            p_yield = target_bc
        elif duration > target_high and duration <= target_zero:
            p_yield = target_bc - config.slope.high * (duration - target_high)
        elif duration > target_zero:
            p_yield = 0

        if p_yield > 0:
            mu = p_yield + 0.84 * config.yield_standard_deviation
            p_yield = self.truncated_norm(
                p_yield, mu, config.yield_standard_deviation
            )

        p_yield *= self.patient.ptype.value

        if p_yield <= target_bc:
            p_yield /= target_bc
        else:
            p_yield = 1

        return p_yield

    def calculate_yield_after_process(self, config: Config) -> Job:
        self.process_yield = self.calculate_yield(
            self.end_process_time - self.start_process_time, config)
        return self

    def calculate_yield_after_collect(self, config: Config) -> Job:
        self.process_yield = self.calculate_yield(
            self.collect_time - self.start_process_time, config)
        return self
                self.collect_time - self.start_process_time, config)
        return self
