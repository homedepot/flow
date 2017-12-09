from abc import ABCMeta, abstractmethod


class Metrics(metaclass=ABCMeta):
    @abstractmethod
    def write_metric(self, task, action):
        pass
