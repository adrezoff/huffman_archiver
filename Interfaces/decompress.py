from abc import ABC, abstractmethod


class DecompressorABC(ABC):
    @abstractmethod
    def decompress(self, file, path):
        pass
