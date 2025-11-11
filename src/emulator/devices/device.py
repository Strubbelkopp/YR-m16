from abc import ABC, abstractmethod

class Device(ABC):
    def __init__(self, name, min_address, max_address):
        self.name = name
        self.min_address = min_address
        self.max_address = max_address
        self.clock_cycle = 0

    @abstractmethod
    def read_byte(self, addr):
        pass

    @abstractmethod
    def write_byte(self, addr, value):
        pass

    def tick(self):
        self.clock_cycle += 1
