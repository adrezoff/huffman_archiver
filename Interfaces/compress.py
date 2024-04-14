from abc import ABC, abstractmethod


class ICompressor(ABC):
    @abstractmethod
    def compress(self, path_in, path_out):
        pass
