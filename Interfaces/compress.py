from abc import ABC, abstractmethod


class CompressorABC(ABC):
    @abstractmethod
    def compress(self, path_in, path_out):
        pass