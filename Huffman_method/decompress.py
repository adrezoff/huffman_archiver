import os
import getpass
from typing import Tuple, Optional, BinaryIO, Union, TextIO

from Huffman_method.hasher import MD5
from Huffman_method.coding import aes_decrypt
from Huffman_method.huffman import HuffmanTree
from Interfaces.decompress import IDecompressor
from Huffman_method.const_byte import *
from Huffman_method.progress_bar import ProgressBar


class Decompressor(IDecompressor):
    """
    Класс для декомпрессии архива методом Хаффмана.
    """

    def __init__(self, block_size: int = 512) -> None:
        """
        Инициализирует объект Decompressor.

        :param block_size: Размер блока для чтения данных из архива.
        """
        self.block_size = block_size
        self.version = 2
        self.codec = None
        self.open_mode = ''
        self.progress_bar = ProgressBar()
        self.out_path = ''
        self.archive_path = ''

    def decompress(self, archive_path: str, out_path: str) -> bool:
        """
        Декомпрессия архива.

        :param archive_path: Путь к архиву.
        :param out_path: Путь для извлечения файлов из архива.
        :return: Результат операции (True - успешно, False - ошибка).
        """
        if os.path.isfile(out_path):
            raise ValueError(f'{out_path} is file')
        if not os.path.exists(archive_path):
            raise ValueError(f'No search archive file [{archive_path}]')
        if not out_path:
            raise ValueError(f'Is empty string [{out_path}]')

        self.out_path = out_path
        self.archive_path = archive_path

        total_size = os.path.getsize(archive_path)
        self.progress_bar.reset(total_size)

        with open(archive_path, 'rb') as file:
            self.check_magic_bytes(file)
            self.check_header(file)
            while (file.tell() + 1) <= total_size:
                try:
                    file_type = self.check_file_type(file)
                    if file_type == b'\x01':
                        self.__decompress(file)
                    elif file_type == b'\x00':
                        self.decompress_empty_dir(file)
                    else:
                        raise ValueError(f'Ошибка структуры архива '
                                         f'[Неверный тип файла]!')
                except ValueError as e:
                    print(f'\n{e.args[0]}')
                    return False
        return True

    def check_magic_bytes(self, file: BinaryIO) -> bool:
        """
        Проверяет магические байты архива.

        :param file: Объект файла.
        """
        magic_bytes = file.read(len(MAGIC_BYTES))
        self.progress_bar.update(len(MAGIC_BYTES))
        if magic_bytes != MAGIC_BYTES:
            raise ValueError(f'Не удалось распознать архив!')
        return True

    def check_header(self, file: BinaryIO) -> bool:
        """
        Проверяет заголовок архива.

        :param file: Файловый объект архива.
        :raises ValueError: Если версия архива не поддерживается
               или кодировка архива недопустима.
        """
        header = file.read(32)

        arch_version = header[0]

        if arch_version != self.version:
            raise ValueError(f'Не поддерживаемая версия архива!')

        flag_codec = header[1]

        supported_codec = [None, 'utf-8']
        if 0 <= flag_codec < len(supported_codec):
            self.codec = supported_codec[flag_codec]

            if self.codec is None:
                self.open_mode = 'ab'
            else:
                self.open_mode = 'a'
        else:
            raise ValueError(f'Неподдерживаемая кодировка архива!')

        self.progress_bar.update(len(header))
        return True

    def check_file_type(self, file):
        type_file = file.read(1)
        if type_file == b'\x00' or type_file == b'\x01':
            self.progress_bar.update(len(type_file))
            return type_file
        raise ValueError(f'Неожиданный тип файла')

    def __decompress(self, file: BinaryIO) -> None:
        """
        Выполняет процесс разархивации файла.

        :param file: Файловый объект архива.
        :raises ValueError: Если тип файла недопустим или
               возникает другая ошибка во время разархивации.
        """
        file_is_not_empty = file.read(1)
        self.progress_bar.update(1)
        try:
            if file_is_not_empty == b'\x00':
                self.decompress_empty_file(file)
            elif file_is_not_empty == b'\x01':
                self.decompress_file(file)
            else:
                raise ValueError(f'Invalid file type')
        except ValueError as e:
            raise e

    def decompress_common_actions(self, file: BinaryIO) -> \
            [Tuple[str, bytes, MD5, bytes, Union[bytes, None]]]:
        """
        Выполняет общие действия при распаковке файла из архива.

        :param file: Файловый объект архива.
        :return: Кортеж с путем и буфером данных.
        :raises ValueError: Если файл не корректен или поврежден.
        """
        level_protect = file.read(1)
        self.progress_bar.update(1)

        hasher = MD5()

        try:
            if level_protect == b'\x01':
                auth_bytes = file.read(16)
                self.progress_bar.update(16)
                out_dir, buffer = self.get_path(file, hasher)
                result, hash_pass = self.authentication(out_dir, auth_bytes)
                if not result:
                    self.skip_file(file, buffer)
                    return None, None, None, None, None
                return out_dir, buffer, hasher, level_protect, hash_pass
            else:
                out_dir, buffer = self.get_path(file, hasher)
                return out_dir, buffer, hasher, level_protect, None
        except ValueError as e:
            raise e

    def decompress_empty_file(self, file: BinaryIO) -> None:
        """
        Распаковывает пустой файл из архива.

        :param file: Файловый объект архива.
        :raises ValueError: Если файл не корректен или поврежден.
        """
        (out_dir, buffer, hasher,
         level_protect, hash_pass) = self.decompress_common_actions(file)

        try:
            if out_dir is None:
                return

            end_data = buffer[:4]
            if len(end_data) < 4:
                chunk = file.read(4 - len(end_data))
                self.progress_bar.update(len(chunk))
                buffer += chunk

            if end_data == END_DATA:
                buffer = buffer[4:]
                self.check_hash(file, hasher, out_dir, buffer)

                dir_path = os.path.dirname(os.path.normpath(out_dir))
                os.makedirs(dir_path, exist_ok=True)
                open(out_dir, 'wb').close()
            else:
                raise ValueError(f'Ошибка идентификации конца файла')
        except ValueError as e:
            raise e

    def decompress_file(self, file: BinaryIO) -> None:
        """
        Распаковывает файл из архива.

        :param file: Файловый объект архива.
        :raises ValueError: Если файл не корректен или поврежден.
        """
        (out_dir, buffer, hasher,
         level_protect, hash_pass) = self.decompress_common_actions(file)

        try:
            if out_dir is None:
                return

            if level_protect == b'\x01':
                tree, buffer = self.get_tree(file, hasher, hash_pass, buffer)
            else:
                tree, buffer = self.get_tree(file, hasher, buffer=buffer)

            buffer = self.read_data(file, tree, hasher, out_dir, buffer)
            self.check_hash(file, hasher, out_dir, buffer)
        except ValueError as e:
            raise e

    def decompress_empty_dir(self, file: BinaryIO) -> None:
        """
        Распаковывает пустой каталог из архива.

        :param file: Файловый объект архива.
        :raises ValueError: Если файл не корректен или поврежден.
        """
        hasher = MD5()

        is_emtpy = file.read(1)
        level_protected = file.read(1)
        if is_emtpy != b'\x00' and level_protected != b'\x00':
            raise ValueError('Ошибка флагов пустой директории')

        out_dir, buffer = self.get_path(file, hasher)
        os.makedirs(out_dir, exist_ok=False)

        end_data = buffer[:4]
        if end_data != END_DATA:
            raise ValueError('Ошибка идентификации '
                             'конца пустой директории')

        buffer = buffer[4:]

        try:
            self.check_hash(file, hasher, out_dir, buffer)
        except ValueError as e:
            raise e

    def get_path(self, file: BinaryIO,
                 hasher: MD5,
                 buffer: bytes = b'') -> Tuple[str, bytes]:
        """
        Извлекает путь из буфера данных и возвращает путь и оставшийся буфер.

        :param file: Файловый объект для чтения данных.
        :param hasher: Объект для вычисления хеша.
        :param buffer: Буфер для обработки данных.
        :return: Кортеж, содержащий извлеченный путь и оставшийся
                буфер данных.
        """
        bytes_path, buffer = self.finder_ends(file, buffer, END_PATH)

        relative_path = bytes_path.decode('utf-8')
        hasher.hash(bytes_path)

        if relative_path == '.':
            relative_path = ''
        full_arch_name = os.path.basename(self.archive_path)
        arch_name = os.path.splitext(full_arch_name)[0]
        out_dir = os.path.join(self.out_path, arch_name, relative_path)
        out_dir = os.path.normpath(out_dir)

        return out_dir, buffer

    def get_tree(self, file: BinaryIO,
                 hasher: MD5,
                 hash_pass: Optional[bytes] = None,
                 buffer: bytes = b'') -> Tuple[HuffmanTree, bytes]:
        """
        Получает дерево Хаффмана из файла и возвращает его.

        :param out_dir:
        :param file: Файловый объект для чтения данных.
        :param hasher: Объект для вычисления хеша.
        :param hash_pass: Байтовая строка с хешем для защищенного дерева.
        :param buffer: Буфер для обработки данных.
        :return: Кортеж, содержащий дерево Хаффмана и оставшийся буфер данных.
        """
        serialized_tree, buffer = self.finder_ends(file, buffer, END_TREE )

        if hash_pass:
            tree = self.get_protected_tree(serialized_tree, hash_pass, hasher)
        else:
            hasher.hash(serialized_tree)
            tree = HuffmanTree()
            tree.deserialize_from_string(serialized_tree)

        return tree, buffer

    @staticmethod
    def get_protected_tree(serialized_tree: bytes,
                           hash_pass: bytes,
                           hasher: MD5) -> HuffmanTree:
        """
        Декодирует дерево по ключу алгоритмом AES

        :param serialized_tree: Закодированное дерево.
        :param hash_pass: Симметричный ключ.
        :param hasher: Объект для вычисления хеша.
        :return: Объект дерева.
        """
        count = int.from_bytes(serialized_tree[-1:], byteorder='big')
        decoded_tree = b''
        while len(serialized_tree) >= 16:
            block = serialized_tree[:16]
            decoded_tree += aes_decrypt(block, hash_pass)
            serialized_tree = serialized_tree[16:]
        decoded_tree = decoded_tree[:-count]
        hasher.hash(decoded_tree)
        tree = HuffmanTree()
        tree.deserialize_from_string(decoded_tree)
        return tree

    def read_data(self, file: BinaryIO,
                  tree: HuffmanTree,
                  hasher: MD5,
                  out_file: str,
                  buffer: bytes) -> bytes:
        """
        Читает данные из файла и декодирует с использованием дерева Хаффмана.

        :param file: Файловый объект, из которого читаются данные.
        :param tree: Дерево Хаффмана для декодирования.
        :param hasher: Объект для вычисления хеша.
        :param out_file: Путь к файлу, в который будут записаны
              раскодированные данные.
        :param buffer: Буфер данных для обработки.
        :return: Оставшийся буфер данных.
        """
        dir_path = os.path.dirname(os.path.normpath(out_file))
        os.makedirs(dir_path, exist_ok=True)

        bits = ''
        with open(out_file, self.open_mode) as outfile:
            end_data = buffer.find(END_DATA)
            if end_data < 0:
                buffer, bits = self.decoded_block(outfile,
                                                  bits,
                                                  buffer,
                                                  end_data,
                                                  tree,
                                                  hasher)
                for block in iter(lambda: file.read(self.block_size), b''):
                    if not block:
                        raise ValueError(f'Файл поврежден [Не удалось '
                                         f'найти конец файла]')

                    self.progress_bar.update(len(block))
                    buffer = buffer[-5:] + block
                    end_data = buffer.find(END_DATA)
                    buffer, bits = self.decoded_block(outfile,
                                                      bits,
                                                      buffer,
                                                      end_data,
                                                      tree,
                                                      hasher)
                    if end_data >= 0:
                        return buffer
            else:
                buffer, bits = self.decoded_block(outfile,
                                                  bits,
                                                  buffer,
                                                  end_data,
                                                  tree,
                                                  hasher)
        return buffer

    def decoded_block(self,
                      outfile: Union[BinaryIO, TextIO],
                      bits: str,
                      buffer: bytes,
                      end_data: int,
                      tree: HuffmanTree,
                      hasher: MD5) -> Tuple[bytes, str]:
        """
        Декодирует блок данных и записывает результат в файл.

        :param outfile: Файл для записи раскодированных данных.
        :param bits: Биты, представляющие закодированные данные.
        :param buffer: Буфер данных.
        :param end_data: Позиция окончания данных в буфере.
        :param tree: Дерево Хаффмана.
        :param hasher: Объект для вычисления хеша.
        :return: Оставшийся буфер данных и оставшиеся биты.
        """
        if end_data >= 0:
            encoded_data = buffer[:end_data-1]
            last_byte = buffer[end_data-1]
            count = last_byte
            buffer = buffer[end_data + 4:]
        else:
            encoded_data = buffer[:-5]
            count = -1
            buffer = buffer[-5:]
        bits += self._bytes_to_bits(encoded_data)
        decoded_data, bits = tree.decode(bits, count)
        outfile.write(decoded_data)

        if self.codec is None:
            hasher.hash(decoded_data)
        else:
            hasher.hash(decoded_data.encode(self.codec))

        return buffer, bits

    def check_hash(self,
                   file: BinaryIO,
                   hasher: MD5,
                   out_path: str,
                   buffer: bytes = b'') -> None:
        """
        Проверяет целостность файла.

        :param file: Объект файла архива.
        :param hasher: Объект для вычисления хеша.
        :param out_path: Путь к файлу.
        :param buffer: Буфер данных.
        """
        if len(buffer) < 16:
            chunk = file.read(16 - len(buffer))
            buffer += chunk

        _hash_file = hasher.get_hash()

        if _hash_file != buffer[:16]:
            raise ValueError(f'Файл [{out_path}] поврежден!')

        buffer = buffer[16:]

        pointer = file.tell()
        file.seek(pointer-len(buffer))
        self.progress_bar.update_with_point(file.tell())
        return

    def skip_file(self, file: BinaryIO, buffer: bytes = b'') -> None:
        """
        Пропускает файл в архиве.

        :param file: Объект файла архива.
        :param buffer: Буфер данных.
        """
        pointer = file.tell()

        end_data = buffer.find(END_DATA)
        if end_data >= 0:
            file.seek(pointer - len(buffer) + end_data + len(END_DATA) + 16)
            self.progress_bar.update_with_point(file.tell())
            return

        for block in iter(lambda: file.read(self.block_size), b''):
            if not block:
                raise ValueError(f'Ошибка структуры архива '
                                 f'[Не удалось найти конец файла]')
            pointer = file.tell()
            buffer = buffer[-3:] + block
            end_data = buffer.find(END_DATA)
            if end_data >= 0:
                offset = pointer - len(buffer) + end_data + len(END_DATA) + 16
                file.seek(offset)
                self.progress_bar.update_with_point(file.tell())
                return

    @staticmethod
    def authentication(path: str,
                       auth_bytes: bytes
                       ) -> Tuple[bool, Optional[bytes]]:
        """
        Аутентификация пользователя для защищенного файла.

        :param path: Путь к файлу.
        :param auth_bytes: Зашифрованный хэш пароля.
        :return: Кортеж, содержащий результат аутентификации
                и хэш пароля (если успешно).
        """
        print(f'\nВведите пароль от файла {path} '
              '(или пустую строку чтобы пропустить файл):')

        for i in range(3):
            password = getpass.getpass()
            if not password:
                print(f'\nВы пропустили файл {path}')
                return False, None

            hasher = MD5()
            hasher.hash(password.encode())
            hash_pass = hasher.get_hash()
            if AUTH_BYTES == aes_decrypt(auth_bytes, hash_pass):
                return True, hash_pass
            else:
                print(f'Не верный пароль. Осталось {2 - i} попытка(-ки)')
                continue

        print(f'Попытки закончились. Файл автоматически пропускается.')
        return False, None

    @staticmethod
    def _bytes_to_bits(data: bytes) -> str:
        """
        Преобразует байты в биты.

        :param data: Байты для преобразования.
        :return: Строка, содержащая биты.
        """
        bits = ''.join(format(byte, '08b') for byte in data)
        return bits

    def finder_ends(self, file: BinaryIO,
                    buffer: bytes,
                    end_str: bytes) -> Tuple[bytes, bytes]:
        """
        Ведет поиск конца блока данных.

        :param file: Файловый объект для чтения данных.
        :param buffer: Буфер для обработки данных.
        :param end_str: Искомые байты.
        :return: Кортеж, содержащий данные и оставшийся буфер.
        """
        end_entry = buffer.find(end_str)

        if end_entry >= 0:
            _bytes, buffer = buffer[:end_entry], buffer[end_entry:]
            if len(buffer) < 4:
                self.progress_bar.update(4 - len(buffer))
                buffer += file.read(4 - len(buffer))
            buffer = buffer[len(end_str):]
        else:
            _bytes = buffer
            for block in iter(lambda: file.read(self.block_size), b''):
                if not block:
                    raise ValueError(f'Файл поврежден [Не удалось '
                                     f'найти конец структуры]')

                block = _bytes[-3:] + block
                end_entry = block.find(end_str)

                if end_entry >= 0:
                    _bytes = _bytes[:-3] + block[:end_entry]
                    block = block[end_entry:]

                    if len(block) < 4:
                        self.progress_bar.update(4 - len(block))
                        block += file.read(4 - len(block))
                        self.progress_bar.update_with_point(file.tell())
                    buffer = block[len(end_str):]
                    break

                _bytes = _bytes[:-3] + block
                self.progress_bar.update_with_point(file.tell())

        return _bytes, buffer
