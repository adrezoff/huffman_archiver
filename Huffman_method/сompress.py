import os
from Huffman_method.huffman import HuffmanTree
from Interfaces.compress import CompressorABC
from Huffman_method.const_byte import *


class Compressor(CompressorABC):
    def __init__(self, block_size=33554432):
        self.block_size = block_size

    def compress(self, path_in, path_out):
        os.makedirs(path_out, exist_ok=True)
        name_dir = os.path.basename(path_in)
        archive_file_path = os.path.join(path_out, f'{name_dir}.huff')

        with open(archive_file_path, 'wb') as outfile:
            outfile.write(MAGIC_HEADER)
            outfile.write(SPECIAL_BYTES)

            # Обрабатываем каждый файл и директорию внутри основной директории
            for root, dirs, files in os.walk(path_in):
                # Записываем путь до текущей директории в архив
                relative_dir = os.path.relpath(root, path_in)

                # Если директория пустая, просто записываем маркер для директории и переходим к следующей
                if not dirs and not files:
                    self.__compress_empty_dir(outfile, relative_dir)
                    continue

                # Если директория не пустая, обрабатываем каждый файл внутри нее
                for filename in files:
                    if filename == '.DS_Store':
                        continue

                    file_path = os.path.join(root, filename)
                    self.__compress_file(file_path, outfile, path_in)

    def __compress_file(self, file_path, outfile, path_in):
        tree = HuffmanTree()

        # Добавляем путь к файлу в дерево
        relative_path = os.path.relpath(file_path, path_in)
        tree.add_block(relative_path)

        # Добавляем содержимое файла в дерево
        with open(file_path, 'rb') as file:
            while True:
                block = file.read(self.block_size)
                if not block:
                    break
                tree.add_block(block)

        tree.build_tree()
        codes = tree.get_codes()

        serialized_tree = tree.serialize_to_string()
        outfile.write(serialized_tree)
        outfile.write(MAGIC_COOKIE_TREE)

        print(relative_path)
        bits_relative_path = ''.join([codes[byte] for byte in relative_path])

        self.__write_directory(outfile, bits_relative_path)

        # Записываем содержимое файла в архив
        with open(file_path, 'rb') as file:
            buffer = ''
            while True:
                block = file.read(self.block_size)
                if not block:
                    break
                buffer += ''.join([codes[byte] for byte in block])
                buffer, compressed_block = self.__bits_to_bytes(buffer)
                outfile.write(compressed_block)
            if buffer:
                byte, byte_count = self.__adder_zero(buffer)
                outfile.write(byte)
                outfile.write(byte_count)
        outfile.write(MAGIC_COOKIE_DATA)

    @staticmethod
    def __bits_to_bytes(bits):
        bytes_list = []

        while len(bits) >= 8:
            byte = bits[:8]
            bits = bits[8:]
            bytes_list.append(int(byte, 2))

        return bits, bytes(bytes_list)

    @staticmethod
    def __adder_zero(bits):
        count = (8 - (len(bits) % 8)) % 8  # Количество нулей, которые нужно добавить
        bits += '0' * count  # Добавляем нули к последовательности битов
        byte = int(bits, 2).to_bytes(1, byteorder='big')
        count_bits = count.to_bytes(1, byteorder='big')
        return byte, count_bits

    def __write_directory(self, outfile, relative_dir):

        bits, bytes = self.__bits_to_bytes(relative_dir)
        outfile.write(bytes)

        count = int(0).to_bytes(1, byteorder='big')
        if bits:
            byte_with_add, count = self.__adder_zero(bits)
            outfile.write(byte_with_add)

        outfile.write(count)

        outfile.write(MAGIC_COOKIE_DIR)

    def __compress_empty_dir(self, outfile, relative_dir):
        tree = HuffmanTree()
        tree.add_block(relative_dir)
        tree.build_tree()

        serialized_tree = tree.serialize_to_string()
        outfile.write(serialized_tree)
        outfile.write(MAGIC_COOKIE_TREE)

        codes = tree.get_codes()
        encoded_path = ''.join([codes[byte] for byte in relative_dir])

        self.__write_directory(outfile, encoded_path)
        outfile.write(MAGIC_COOKIE_DATA)
