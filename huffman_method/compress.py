import os
from typing import Dict, Optional, Tuple, BinaryIO
from encryption.coding import aes_encrypt
from huffman_method.huffman import HuffmanTree
from interfaces.compress import ICompressor
from huffman_method.const_byte import *
from progress_bar import ProgressBar
from encryption.hasher import MD5


class Compressor(ICompressor):
    """
    Реализует сжатие файлов и директорий с использованием метода Хаффмана.
    """

    def __init__(self, codec: Optional[str] = None, block_size: int = 256):
        """
        Инициализирует объект компрессора.

        :param codec: Кодек для чтения файлов. По умолчанию None.
        :param block_size: Размер блока данных для чтения. По умолчанию 128.
        """
        self.block_size: int = block_size
        self.version: int = 2
        self.codec: Optional[str] = codec
        self.open_mode_files: str = ''
        if codec is None:
            self.open_mode: str = 'rb'
        else:
            self.open_mode: str = 'r'
        self.progress_bar: ProgressBar = ProgressBar()

    def compress(self,
                 path_in: str,
                 path_out: str,
                 protected_files: Optional[Dict[str, bytes]] = None
                 ) -> Tuple[int, int]:
        """
        Сжимает указанный файл или директорию.

        :param path_in: Путь к файлу или директории для сжатия.
        :param path_out: Путь к выходному архиву.
        :param protected_files: Зашифрованные файлы и пароли для них.
              По умолчанию None.
        :return: Кортеж, содержащий размер исходных данных и размер
                сжатого архива.
        """
        if not os.path.exists(path_in):
            raise ValueError(f'Файл или директория [{path_in}] не найдены')
        elif not path_out:
            raise ValueError(f'Пустая строка в качестве пути [{path_out}]')

        total_size, all_files = self.get_directory_info(path_in)

        self.progress_bar.reset(total_size)

        os.makedirs(path_out, exist_ok=True)
        name_dir = os.path.basename(os.path.normpath(path_in))
        archive_file_path = os.path.join(path_out, f'{name_dir}.huff')

        if os.path.exists(archive_file_path):
            raise ValueError(f'Архив [{archive_file_path}] уже существует')

        with open(archive_file_path, 'wb') as outfile:
            outfile.write(MAGIC_BYTES)

            try:
                self._make_header(outfile)
            except ValueError as e:
                raise e

            if not all_files:
                if os.path.isdir(path_in):
                    self.compress_empty_dir(outfile, path_in, path_in)
                else:
                    self.compress_file(outfile,
                                       path_in,
                                       path_in,
                                       protected_files)
            else:
                for path, item_type in all_files.items():
                    if item_type == 'empty_directory':
                        self.compress_empty_dir(outfile, path, path_in)
                    elif item_type == 'file':
                        self.compress_file(outfile, path,
                                           path_in,
                                           protected_files)

        return total_size, os.path.getsize(archive_file_path)

    def _make_header(self, outfile: BinaryIO) -> None:
        """
        Создает заголовок архива.

        :param outfile: Выходной файл для записи.
        """
        header = bytearray(32)
        header[0] = self.version
        supported_codec = {None: 0, 'utf-8': 1}
        if self.codec in supported_codec:
            header[1] = supported_codec[self.codec]
        else:
            raise ValueError(f'Кодек {self.codec} не поддерживается!')
        outfile.write(bytes(header))

    @staticmethod
    def compress_empty_dir(outfile: BinaryIO,
                           file_path: str,
                           path_in: str) -> None:
        """
        Сжимает пустую директорию.

        :param outfile: Выходной файл для записи.
        :param file_path: Путь к директории.
        :param path_in: Исходный путь директории.
        """
        relative_path = os.path.relpath(file_path, path_in)
        bytes_relative_path = relative_path.encode('utf-8')

        hasher = MD5()

        outfile.write(b'\x00'*3)

        outfile.write(bytes_relative_path)
        hasher.hash(bytes_relative_path)
        outfile.write(END_PATH)
        outfile.write(END_DATA)

        bytes_hash = hasher.get_hash()
        outfile.write(bytes_hash)

    def compress_file(self,
                      outfile: BinaryIO,
                      file_path: str,
                      path_in: str,
                      protected_files: Optional[Dict[str, bytes]]) -> None:
        """
        Сжимает файл.

        :param outfile: Выходной файл для записи.
        :param file_path: Путь к файлу.
        :param path_in: Исходный путь файла.
        :param protected_files: Зашифрованные файлы и пароли для них.
        """
        hasher = MD5()
        tree = None
        pass_hash = None
        if protected_files and (file_path in protected_files):
            pass_hash = protected_files[file_path]

        not_empty_file = self.write_header_file(outfile,
                                                file_path,
                                                path_in,
                                                hasher,
                                                pass_hash)

        if not_empty_file == b'\x01':
            tree = self.write_tree(outfile, file_path, hasher, pass_hash)
        self.write_data(outfile, file_path, hasher, tree)

    @staticmethod
    def write_header_file(outfile: BinaryIO,
                          file_path: str,
                          path_in: str,
                          hasher: MD5,
                          pass_hash: Optional[bytes]) -> bytes:
        """
        Записывает заголовок файла в архив.

        :param outfile: Выходной файл для записи.
        :param file_path: Путь к файлу.
        :param path_in: Исходный путь файла.
        :param hasher: Объект для хеширования.
        :param pass_hash: Пароль для зашифрованного файла.
        :return: Флаг, указывающий на наличие данных в файле.
        """
        relative_path = os.path.relpath(file_path, path_in)
        bytes_relative_path = relative_path.encode('utf-8')

        outfile.write(b'\x01')

        not_empty_file = b'\x01'

        if os.path.getsize(file_path) == 0:
            not_empty_file = b'\x00'

        outfile.write(not_empty_file)

        if pass_hash:
            outfile.write(b'\x01')
            auth_bytes = aes_encrypt(AUTH_BYTES, pass_hash)
            outfile.write(auth_bytes)
        else:
            outfile.write(b'\x00')

        outfile.write(bytes_relative_path)

        hasher.hash(bytes_relative_path)
        outfile.write(END_PATH)

        return not_empty_file

    def write_tree(self,
                   outfile: BinaryIO,
                   file_path: str,
                   hasher: MD5,
                   pass_hash: Optional[bytes]) -> HuffmanTree:
        """
        Записывает дерево Хаффмана в архив.

        :param outfile: Выходной файл для записи.
        :param file_path: Путь к файлу.
        :param hasher: Объект для хеширования.
        :param pass_hash: Пароль для зашифрованного файла.
        :return: Объект дерева Хаффмана.
        """
        tree = self._generate_huffman_tree(file_path)
        serialized_tree = tree.serialize_to_string()
        hasher.hash(serialized_tree)

        if pass_hash:
            while len(serialized_tree) >= 16:
                block = serialized_tree[:16]
                serialized_tree = serialized_tree[16:]
                outfile.write(aes_encrypt(block, pass_hash))

            count = 16 - len(serialized_tree)
            added_bytes = serialized_tree + (b'\x00' * count)
            outfile.write(aes_encrypt(added_bytes, pass_hash))

            outfile.write(count.to_bytes(1, byteorder='big'))
        else:
            outfile.write(serialized_tree)

        outfile.write(END_TREE)

        return tree

    def _generate_huffman_tree(self, file_path: str) -> HuffmanTree:
        """
        Генерирует дерево Хаффмана для файла.

        :param file_path: Путь к файлу.
        :return: Объект дерева Хаффмана.
        """
        tree = HuffmanTree(self.codec)

        with open(file_path, self.open_mode) as file:
            for block in iter(lambda: file.read(self.block_size), b''):
                if not block:
                    break
                tree.add_block(block)

        tree.build_tree()
        return tree

    def write_data(self,
                   outfile: BinaryIO,
                   file_path: str,
                   hasher: MD5,
                   tree: Optional[HuffmanTree]) -> None:
        """
        Записывает данные файла в архив.

        :param outfile: Выходной файл для записи.
        :param file_path: Путь к файлу.
        :param hasher: Объект для хеширования.
        :param tree: Объект дерева Хаффмана.
        """
        if tree:
            codes = tree.get_codes()

            with open(file_path, self.open_mode) as file:
                buffer = ''
                for block in iter(lambda: file.read(self.block_size), b''):
                    if not block:
                        break

                    if self.open_mode == 'rb':
                        hasher.hash(block)
                    else:
                        hasher.hash(block.encode())

                    if tree:
                        buffer += ''.join([codes[obj] for obj in block])

                    buffer, compressed_block = self._bits_to_bytes(buffer)
                    outfile.write(compressed_block)

                    self.progress_bar.update(len(block))

                if buffer:
                    byte, byte_count = self._adder_zero(buffer)
                    outfile.write(byte)
                    outfile.write(byte_count)
                else:
                    outfile.write(bytes([0]))

        outfile.write(END_DATA)
        outfile.write(hasher.get_hash())

    @staticmethod
    def _bits_to_bytes(bits: str) -> Tuple[str, bytes]:
        """
        Преобразует биты в байты.

        :param bits: Строка с битами.
        :return: Кортеж с оставшимися битами и байтами.
        """
        bytes_list = []

        while len(bits) >= 8:
            byte = bits[:8]
            bits = bits[8:]
            bytes_list.append(int(byte, 2))

        return bits, bytes(bytes_list)

    @staticmethod
    def _adder_zero(bits: str) -> Tuple[bytes, bytes]:
        """
        Добавляет нули в конец битовой строки.

        :param bits: Битовая строка.
        :return: Кортеж с байтом и количеством добавленных нулей.
        """
        count = (8 - (len(bits) % 8)) % 8
        bits += '0' * count
        byte = int(bits, 2).to_bytes(1, byteorder='big')
        count_bits = count.to_bytes(1, byteorder='big')
        return byte, count_bits

    @staticmethod
    def get_directory_info(path: str) -> Tuple[int, Dict[str, str]]:
        """
        Возвращает информацию о размере и содержимом директории.

        :param path: Путь к директории.
        :return: Кортеж, содержащий общий размер файлов в директории и
                словарь с информацией о каждом файле (путь к файлу: тип
                файла).
        """
        total_size: int = 0
        info_dict: Dict[str, str] = {}

        if os.path.isdir(path):
            stack = [path]

            while stack:
                current_path = stack.pop()

                contents = os.listdir(current_path)
                if len(contents) == 1 and contents[0] == '.DS_Store':
                    info_dict[current_path] = "empty_directory"
                else:
                    for item in contents:
                        item_path = os.path.join(current_path, item)

                        if os.path.isfile(item_path):
                            if item != '.DS_Store':
                                info_dict[item_path] = "file"
                                total_size += os.path.getsize(item_path)
                        elif os.path.isdir(item_path):
                            stack.append(item_path)
            return total_size, info_dict
        elif os.path.isfile(path):
            return os.path.getsize(path), {path: "file"}
        else:
            return 0, {}
