import os
from Huffman_method.huffman import HuffmanTree
from Interfaces.compress import CompressorABC
from Huffman_method.const_byte import *


class Compressor(CompressorABC):
    def __init__(self, block_size=33554432):
        self.block_size = block_size

    def compress(self, path_in, path_out):
        last_directory = os.path.basename(path_in)
        os.makedirs(path_out, exist_ok=True)
        archive_file_path = os.path.join(path_out, f'{last_directory}.huff')

        with open(archive_file_path, 'wb') as outfile:
            outfile.write(MAGIC_HEADER)
            outfile.write(SPECIAL_BYTES)

            # Обрабатываем каждый файл в директории path_in
            for path_file in self.__iter_dir(path_in):
                # Создаем дерево Хаффмана для текущего файла
                tree = HuffmanTree()
                relative_path = os.path.relpath(path_file, path_in)

                self.__create_tree(path_file, relative_path ,tree)

                codes = tree.get_codes()

                serialized_tree = tree.serialize_to_string()
                outfile.write(serialized_tree)
                outfile.write(MAGIC_COOKIE_TREE)

                # Если это пустая директория, записываем сразу маркер для данных
                if os.path.isdir(path_file):
                    outfile.write(MAGIC_COOKIE_DATA)
                else:
                    compress_path = self.__compress(codes, relative_path)
                    outfile.write(compress_path)
                    outfile.write(MAGIC_COOKIE_DIR)

                # Обрабатываем каждый блок данных в текущем файле
                for block in self.__iter_file(path_file):
                    # Преобразуем блок из байтов в строку
                    block_str = block.decode('latin1')
                    compress_data = self.__compress(codes, block_str)
                    outfile.write(compress_data)

    def __compress(self, codes, block):
        encoded_data = ''.join([codes[char] for char in block])
        # Преобразуем битовые строки в байты
        compressed_data = self.__bits_to_bytes(encoded_data)
        return compressed_data

    @staticmethod
    def __bits_to_bytes(bits):
        # Добавляем нулевой бит, если количество битов не кратно 8
        bits += '0' * (8 - len(bits) % 8)
        # Разбиваем битовую строку на байты и преобразуем в соответствующие байты
        bytes_list = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
        # Преобразуем список байтов в байтовую строку
        return bytes(bytes_list)

    @staticmethod
    def __iter_dir(path):
        for root, dirs, files in os.walk(path):
            for directory in dirs:
                dir_path = os.path.join(root, directory)
                yield dir_path
            for filename in files:
                file_path = os.path.join(root, filename)
                yield file_path

    def __iter_file(self, path):
        if os.path.isfile(path):  # Проверяем, является ли путь файлом
            with open(path, 'rb') as file:
                while True:
                    block = file.read(self.block_size)
                    if not block:
                        break
                    yield block
        else:
            None

    def __create_tree(self, path, reletive_path, tree):
        tree.add_block(str(reletive_path))

        for block in self.__iter_file(path):
            # Преобразуем блок из байтов в строку
            block_str = block.decode('latin1')
            tree.add_block(block_str)

        tree.build_tree()