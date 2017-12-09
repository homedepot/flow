from abc import ABCMeta, abstractmethod


class Static_Quality_Analysis(metaclass=ABCMeta):
    @abstractmethod
    def scan_code(self):
        pass
