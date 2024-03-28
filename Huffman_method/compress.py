import os
from Huffman_method.huffman import HuffmanTree
from Interfaces.compress import CompressorABC
from Huffman_method.const_byte import *


class Compressor(CompressorABC):
    """Класс для сжатия файлов методом Хаффмана."""

    def __init__(self, codec=None, block_size=128):
        """Инициализация объекта сжатия.

        Args:
            codec (str): Кодировка для чтения файлов. По умолчанию None.
            block_size (int): Размер блока для чтения файла. По умолчанию 128.
        """
        self.block_size = block_size
        self.version = 1
        self.codec = codec
        self.open_mode_files = ''
        if codec is None:
            self.open_mode = 'rb'
        else:
            self.open_mode = 'r'

    def compress(self, path_in, path_out):
        """Сжимает файлы по указанному пути и записывает сжатые
        данные в новый архив.

        Args:
            path_in (str): Путь к файлу или директории для сжатия.
            path_out (str): Путь, по которому будет сохранен архив.

        Returns:
            int: Разница в размере между исходными данными и сжатыми данными.
        """
        size_path_in = 0
        os.makedirs(path_out, exist_ok=True)
        name_dir = os.path.basename(path_in)
        archive_file_path = os.path.join(path_out, f'{name_dir}.huff')

        with open(archive_file_path, 'wb') as outfile:
            outfile.write(MAGIC_BYTES)
            self._make_header(outfile)

            if self._is_file(path_in):
                size_path_in += os.path.getsize(path_in)
                self._compress_file(outfile, path_in, path_in)
            else:
                for root, dirs, files in os.walk(path_in):
                    relative_dir = os.path.relpath(root, path_in)
                    if self.codec is None:
                        relative_dir = relative_dir.encode('utf-8')

                    if not dirs and not files:
                        self._compress_empty_dir(outfile, relative_dir)
                        continue

                    for filename in files:
                        if filename == '.DS_Store':
                            continue

                        file_path = os.path.join(root, filename)
                        size_path_in += os.path.getsize(file_path)

                        self._compress_file(outfile, file_path, path_in)
        size_archive = os.path.getsize(archive_file_path)
        return size_path_in - size_archive

    def _compress_file(self, outfile, file_path, main_dir):
        """Сжимает файл и записывает его в архив.

        Args:
            outfile (file object): Объект файла для записи сжатых данных.
            file_path (str): Путь к файлу для сжатия.
            main_dir (str): Главная директория.
        """
        if file_path != main_dir:
            relative_path = os.path.relpath(file_path, main_dir)
            if self.codec is None:
                relative_path = relative_path.encode('utf-8')
        else:
            relative_path = ''

        tree = self._generate_huffman_tree(file_path, relative_path)
        codes = tree.get_codes()
        serialized_tree = tree.serialize_to_string()
        outfile.write(serialized_tree)
        outfile.write(MAGIC_COOKIE_TREE)

        self._write_directory(outfile, relative_path, codes)

        with open(file_path, self.open_mode) as file:
            buffer = ''
            while True:
                block = file.read(self.block_size)
                if not block:
                    break
                buffer += ''.join([codes[obj] for obj in block])

                buffer, compressed_block = self._bits_to_bytes(buffer)
                outfile.write(compressed_block)

            if buffer:
                byte, byte_count = self._adder_zero(buffer)
                outfile.write(byte)
                outfile.write(byte_count)
            else:
                outfile.write((0).to_bytes(1, byteorder='big'))

        outfile.write(MAGIC_COOKIE_DATA)

    def _make_header(self, outfile):
        """Создает заголовок архива.

        Args:
            outfile (file object): Объект файла для записи архива.
        """
        header = bytearray(32)
        header[0] = self.version
        outfile.write(bytes(header))

    def _generate_huffman_tree(self, file_path, relative_path):
        """Генерирует дерево Хаффмана для сжатия файла.

        Args:
            file_path (str): Путь к файлу для сжатия.
            relative_path (str): Относительный путь к файлу.

        Returns:
            HuffmanTree: Дерево Хаффмана.
        """
        if self.codec is None:
            tree = HuffmanTree()
        else:
            tree = HuffmanTree(self.codec)

        tree.add_block(relative_path)
        with open(file_path, self.open_mode) as file:
            while True:
                block = file.read(self.block_size)
                if not block:
                    break
                tree.add_block(block)

        tree.build_tree()
        return tree

    @staticmethod
    def _bits_to_bytes(bits):
        """Конвертирует биты в байты.

        Args:
            bits (str): Последовательность битов.

        Returns:
            tuple: Кортеж с оставшимися битами и байтами, полученными из битов.
        """
        bytes_list = []

        while len(bits) >= 8:
            byte = bits[:8]
            bits = bits[8:]
            bytes_list.append(int(byte, 2))

        return bits, bytes(bytes_list)

    @staticmethod
    def _adder_zero(bits):
        """Добавляет недостающие нули к последовательности битов и
        конвертирует ее в байты.

        Args:
            bits (str): Последовательность битов.

        Returns:
            tuple: Кортеж с байтами, полученными из битов с добавленными
            нулями, и байтом с количеством добавленных нулей.
        """
        count = (8 - (len(bits) % 8)) % 8
        bits += '0' * count
        byte = int(bits, 2).to_bytes(1, byteorder='big')
        count_bits = count.to_bytes(1, byteorder='big')
        return byte, count_bits

    def _write_directory(self, outfile, relative_dir, codes):
        """
        Записывает директорию в архив.

        Args:
            outfile (file object): Объект файла для записи архива.
            relative_dir (str): Относительный путь к директории.
            codes (dict): Словарь кодов символов.
        """
        bits_relative_dir = ''.join([codes[obj] for obj in relative_dir])

        _bits, _bytes = self._bits_to_bytes(bits_relative_dir)
        outfile.write(_bytes)

        if _bits:
            byte_with_zero, count_zero = self._adder_zero(_bits)
            outfile.write(byte_with_zero)
            outfile.write(count_zero)
        else:
            outfile.write(int(0).to_bytes(1, byteorder='big'))

        outfile.write(MAGIC_COOKIE_DIR)

    def _compress_empty_dir(self, outfile, relative_dir):
        """
        Сжимает пустую директорию и записывает ее в архив.

        Args:
            outfile (file object): Объект файла для записи архива.
            relative_dir (str): Относительный путь к директории.
        """
        tree = HuffmanTree()
        tree.add_block(relative_dir)
        tree.build_tree()

        serialized_tree = tree.serialize_to_string()
        outfile.write(serialized_tree)
        outfile.write(MAGIC_COOKIE_TREE)

        codes = tree.get_codes()

        self._write_directory(outfile, relative_dir, codes)
        outfile.write(MAGIC_COOKIE_DATA)

    @staticmethod
    def _is_file(path):
        """
        Проверяет, является ли путь файлом.

        Args:
            path (str): Путь к файлу.

        Returns:
            bool: True, если путь указывает на файл, False в противном случае.
        """
        _, extension = os.path.splitext(path)
        if extension:
            return True
        else:
            return False
