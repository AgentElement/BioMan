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
        self.blood_volume = np.random.uniform(low=pconfig.blood_vol_range[0],
                                              high=pconfig.blood_vol_range[1])
        self.target_blood_count = pconfig.conversion_factor * self.blood_volume
        self.pconfig = pconfig

    @staticmethod
    def random(pconfig: PatientConfig):
        """Generate a random patient"""
        gr = pconfig.gender_ratio
        gender = random.choices(P_Gender, weights=[gr, 1 - gr])[0]
        ptype = random.choices(P_Type, weights=pconfig.patient_rates)[0]
        return Patient(gender, ptype)

    def __str__(self):
        print(self.gender, self.ptype, self.blood_volume, self.target_blood_count)


class JobState(Enum):
    IDLE = 1
    SETUP = 2
    BUSY = 0


class Job(Queueable):
    def __init__(self, patient: Patient):
        super().__init__()
        self.patient = patient
        self.enter_time = -1
        self.leave_time = -1
        self.rework_times = []
        self.state = JobState.IDLE

    def enter_system(self, clock: float):
        if self.enter_time is not None:
            raise JobError
        self.enter_time = clock
        return self

    def leave_system(self, clock: float):
        if self.leave_time is not None or self.enter_time is None:
            raise JobError
        self.leave_time = clock
        return self

    def attempt_rework(self, rework_time: float):
        self.rework_times.append(rework_time)
        return self

    def set_state(self, state: JobState):
        self.state = state
        return self

    def rework_attempts(self):
        return len(self.rework_times)


class ProcessJob(Job):
    def __init__(self, patient: Patient):
        super().__init__(patient)

    @staticmethod
    def truncated_norm(lower, mu, sigma):
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

    def calculate_yield(self, duration, config: Config):
        target_bc = self.patient.target_bloodcount
        target_low = target_bc / config.slope.low
        target_high = target_low + config.delta_t
        target_zero = target_high + target_bc / config.slope.high

        if duration <= target_low:
            p_yield = config.slope.low * duration
        elif duration > target_low and duration <= target_high:
            p_yield = target_bc
        elif duration > target_high and duration <= target_zero:
            p_yield = target_bc - self.slope.high * (duration - target_high)
        elif duration > target_zero:
            p_yield = 0

        if p_yield > 0:
            mu = p_yield + 0.84 * config.yield_standard_deviation
            p_yield = self.truncated_norm(
                p_yield, mu, config.yield_standard_deviation
            )

        p_yield *= self.patient.ptype

        if p_yield <= target_bc:
            p_yield /= target_bc
        else:
            p_yield = 1

        return p_yield


class HarvestJob(Job):
    def __init__(self, patient: Patient):
        super().__init__(patient)
        pass
