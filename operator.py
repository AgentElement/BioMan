from util import Queueable


# An operator is a Queueable that can be busy working a machine.
# That's literally it
class Operator(Queueable):
    def __init__(self):
        super().__init__()
        self.__busy = False

    def make_busy(self, busy: bool):
        self.__busy = busy
        return self


class HarvestOperator(Queueable):
    def __init__(self):
        super().__init__()


class ProcessOperator(Queueable):
    def __init__(self):
        super().__init__()
