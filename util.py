from collections import deque


class QueueError(Exception):
    pass


# If in a queue, a queueable is queued
class Queueable:
    def __init__(self):
        self.__queued = False

    def set_queued(self, queue_state: bool):
        self.__queued: bool = queue_state
        return self

    def queued(self):
        return self.__queued


# Standard queue for Jobs, Machines, Operators (Queueables)
class Queue:
    def __init__(self,
                 init_elems: list[Queueable] = [],
                 inverting: bool = False):
        self.inverting = inverting
        self.__buf = deque(init_elems)

    def peek(self):
        if len(self.__buf) == 0:
            raise IndexError
        return self.__buf[0]

    def push(self, i: Queueable):
        if i.queued():
            raise QueueError

        i.set_queued(not self.inverting)
        self.__buf.append(i)

    def pop(self):
        popped = self.__buf.popleft()
        popped.set_queued(self.inverting)
        return popped


# Paired queue for Jobs, Machines, Operators (Queueables)
class BusyQueue:
    def __init__(self, init_elems: list[Queueable] = []):
        self.__busy_q = deque()
        map(lambda q: q.set_queued(False), init_elems)
        self.__free_q = deque(init_elems)

    def make_busy(self):
        queueable = self.__free_q.popleft().set_queued(True)
        self.__busy_q.append(queueable)
        return queueable

    def free(self):
        queueable = self.__busy_q.popleft().set_queued(False)
        self.__free_q.append(queueable)
        return queueable

    def push(self, i: Queueable):
        if i.queued():
            raise QueueError

        self.__free_q.append(i)

    def pop(self):
        return self.__free_q.popleft()
