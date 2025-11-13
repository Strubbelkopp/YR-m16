from abc import ABC, abstractmethod

class Device(ABC):
    def __init__(self, name, min_address, max_address, io_type):
        self.name = name
        self.min_address = min_address
        self.max_address = max_address
        self.io_type = io_type
        self.clock_cycle = 0

    def tick(self):
        self.clock_cycle += 1
