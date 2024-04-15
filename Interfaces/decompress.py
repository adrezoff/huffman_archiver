from abc import ABC, abstractmethod


class IDecompressor(ABC):
    """
    Абстрактный класс для декомпрессора.
    """

    @abstractmethod
    def decompress(self, archive_file: str, out_path: str) -> None:
        """
        Метод для разархивирования файла.

        :param archive_file: Путь к архивному файлу.
        :param out_path: Путь для сохранения разархивированных файлов.
        """
        pass
