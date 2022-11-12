from collections import namedtuple

Range = namedtuple('Range', ['low', 'high'])
Rates = namedtuple('Rates', ['bad', 'average', 'good'])
GenderedPair = namedtuple('GenderedPair', ['male', 'female'])


class ConfigError(Exception):
    pass


class PatientConfig:
    def __init__(self):
        self.conversion_factor = 140000
        self.blood_vol_range = GenderedPair(Range(5.0, 7.5), Range(3.5, 6.0))
        self.gender_ratio = 0.5

        # Default value from an unstressed system
        self.patient_rates = Rates(8, 1, 1)

    def set_patient_rates(self, bad: int, average: int, good: int):
        self.patient_rates = Rates(bad, average, good)
        return self


class Config:
    def __init__(self):
        self.patient_count = 20
        self.simulation_time: int = 3000
        self.max_rework_count: int = 3
        self.patient_arrival_distribution: int = 0

        self.patient_config = PatientConfig()

        # Everything here is modifiable, defaults are from an unstressed sustem
        self.manufacturing_duration_percentage = Rates(0.5, 0.25, 0.25)
        self.slope = Range(100000, 4000)
        self.harvest_machine_count = 4
        self.harvest_operator_count = 2
        self.process_machine_count = 8
        self.process_operator_count = 4

        # Not entirely sure what this is
        self.delta_t = 5

        # true normal std dev is ~0.693, but I'm copying the spec
        self.yield_standard_deviation = 0.7

        self.qc_reject_threshold_policy = 0.5

    def set_mfg_dur_pct(self, bad: float, average: float, good: float):
        if bad + average + good != 1.0:
            raise ConfigError
        self.manufacturing_duration_percentage = Rates(bad, average, good)
        return self

    def set_slope(self, low: int, high: int):
        self.slope = Range(low, high)
        return self

    def set_harvest_machine_count(self, count: int):
        self.harvest_machine_count = count
        return self

    def set_harvest_operator_count(self, count: int):
        self.harvest_operator_count = count
        return self

    def set_process_machine_count(self, count: int):
        self.process_machine_count = count
        return self

    def set_process_operator_count(self, count: int):
        self.process_operator_count = count
        return self
