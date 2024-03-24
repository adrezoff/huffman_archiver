import os
from Huffman_method.huffman import HuffmanTree
from Interfaces.compress import CompressorABC
from Huffman_method.const_byte import *


class Compressor(CompressorABC):
    def __init__(self, codec=None, block_size=128):
        self.block_size = block_size
        self.version = 1
        self.codec = codec

        self.open_mode_files = str()
        if codec is None:
            self.open_mode = 'rb'
        else:
            self.open_mode = 'r'

    def compress(self, path_in, path_out):
        size_path_in = 0
        size_archive = 0
        os.makedirs(path_out, exist_ok=True)
        name_dir = os.path.basename(path_in)
        archive_file_path = os.path.join(path_out, f'{name_dir}.huff')

        with open(archive_file_path, 'wb') as outfile:
            outfile.write(MAGIC_BYTES)
            self.__make_header(outfile)

            if self.__is_file(path_in):
                size_path_in += os.path.getsize(path_in)
                self.__compress_file(outfile, path_in, path_in)
            else:
                for root, dirs, files in os.walk(path_in):
                    relative_dir = os.path.relpath(root, path_in)
                    if self.codec is None:
                        relative_dir = relative_dir.encode('utf-8')

                    if not dirs and not files:
                        self.__compress_empty_dir(outfile, relative_dir)
                        continue

                    for filename in files:
                        if filename == '.DS_Store':
                            continue

                        file_path = os.path.join(root, filename)
                        size_path_in += os.path.getsize(file_path)

                        self.__compress_file(outfile, file_path, path_in)
        return size_path_in - size_archive

    def __compress_file(self, outfile, file_path, main_dir):
        if file_path != main_dir:
            relative_path = os.path.relpath(file_path, main_dir)
            if self.codec is None:
                relative_path = relative_path.encode('utf-8')

        else:
            relative_path = ''

        tree = self.__generate_huffman_tree(file_path, relative_path)
        codes = tree.get_codes()
        serialized_tree = tree.serialize_to_string()
        outfile.write(serialized_tree)
        outfile.write(MAGIC_COOKIE_TREE)

        self.__write_directory(outfile, relative_path, codes)

        with open(file_path, self.open_mode) as file:
            buffer = ''

            while True:
                block = file.read(self.block_size)
                if not block:
                    break
                buffer += ''.join([codes[obj] for obj in block])

                buffer, compressed_block = self.__bits_to_bytes(buffer)
                outfile.write(compressed_block)

            if buffer:
                byte, byte_count = self.__adder_zero(buffer)
                outfile.write(byte)
                outfile.write(byte_count)
            else:
                outfile.write((0).to_bytes(1, byteorder='big'))

        outfile.write(MAGIC_COOKIE_DATA)

    def __make_header(self, outfile):
        header = bytearray(32)
        header[0] = self.version
        outfile.write(bytes(header))

    def __generate_huffman_tree(self, file_path, relative_path):
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
    def __bits_to_bytes(bits):
        bytes_list = []

        while len(bits) >= 8:
            byte = bits[:8]
            bits = bits[8:]
            bytes_list.append(int(byte, 2))

        return bits, bytes(bytes_list)

    @staticmethod
    def __adder_zero(bits):
        count = (8 - (len(bits) % 8)) % 8
        bits += '0' * count
        byte = int(bits, 2).to_bytes(1, byteorder='big')
        count_bits = count.to_bytes(1, byteorder='big')
        return byte, count_bits

    def __write_directory(self, outfile, relative_dir, codes):

        bits_relative_dir = ''.join([codes[obj] for obj in relative_dir])

        _bits, _bytes = self.__bits_to_bytes(bits_relative_dir)
        outfile.write(_bytes)

        if _bits:
            byte_with_zero, count_zero = self.__adder_zero(_bits)
            outfile.write(byte_with_zero)
            outfile.write(count_zero)
        else:
            outfile.write(int(0).to_bytes(1, byteorder='big'))

        outfile.write(MAGIC_COOKIE_DIR)

    def __compress_empty_dir(self, outfile, relative_dir):
        tree = HuffmanTree()
        tree.add_block(relative_dir)
        tree.build_tree()

        serialized_tree = tree.serialize_to_string()
        outfile.write(serialized_tree)
        outfile.write(MAGIC_COOKIE_TREE)

        codes = tree.get_codes()

        self.__write_directory(outfile, relative_dir, codes)
        outfile.write(MAGIC_COOKIE_DATA)

    @staticmethod
    def __is_file(path):
        _, extension = os.path.splitext(path)
        if extension:
            return True
        else:
            return False
