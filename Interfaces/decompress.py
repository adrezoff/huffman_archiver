from abc import ABC, abstractmethod


class IDecompressor(ABC):
    @abstractmethod
    def decompress(self, archive_file, out_path):
        pass
