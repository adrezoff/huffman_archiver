from abc import ABC, abstractmethod


class ICompressor(ABC):
    """
    Абстрактный класс для компрессора.
    """

    @abstractmethod
    def compress(self, path_in: str, path_out: str) -> None:
        """
        Метод для сжатия файла.

        :param path_in: Путь к исходному файлу.
        :param path_out: Путь для сохранения сжатого файла.
        """
        pass
