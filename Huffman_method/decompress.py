import os
from Huffman_method.huffman import HuffmanTree
from Interfaces.decompress import DecompressorABC
from Huffman_method.const_byte import *


class Decompressor(DecompressorABC):
    def __init__(self, block_size=33554432):
        self.block_size = block_size

    def decompress(self, archive_file, out_path):
        name_dir = os.path.splitext(os.path.basename(archive_file))[0]
        out_path = str(os.path.join(out_path, name_dir))
        os.makedirs(out_path, exist_ok=True)

        buffer = bytes()
        flag = 1
        current_tree = HuffmanTree()
        path_out_file = ''

        print('----------')

        with open(archive_file, 'rb') as file:
            while True:
                buffer += file.read(self.block_size)
                if not buffer:
                    break

                current_tree = HuffmanTree()
                if flag == 1:
                    flag, buffer = self.__check_magic_header(buffer)
                if flag == 2:
                    flag, current_tree, buffer = self.__read_tree(buffer)
                if flag == 3:
                    flag, current_path, bits, buffer = self.__read_directory(buffer, current_tree)
                    path_out_file = os.path.join(out_path, current_path)
                if flag == 4:
                    flag, decoded_data, bits, buffer = self.__reed_data(bits, buffer, current_tree)
                    if flag == 2 and not decoded_data:
                        os.makedirs(path_out_file, exist_ok=True)
                    else:
                        with open(path_out_file, 'w') as out_file:
                            out_file.write(decoded_data)

    @staticmethod
    def __check_magic_header(block):
        len_all_header = len(MAGIC_HEADER.__add__(SPECIAL_BYTES))
        if len(block) >= len_all_header:
            if block[:len(MAGIC_HEADER)] == MAGIC_HEADER:
                if block[len(MAGIC_HEADER):len_all_header] == SPECIAL_BYTES:
                    return 2, block[len_all_header:]
                else:
                    raise ValueError("Invalid identify archive format")
            else:
                raise ValueError("Invalid identify archive format")

        return 1, block

    @staticmethod
    def __read_tree(block):
        cookie_tree = block.find(MAGIC_COOKIE_TREE)
        if cookie_tree >= 0:
            serializable_tree = block[:cookie_tree]
            try:
                tree = HuffmanTree()
                tree.deserialize_from_string(serializable_tree)
                return 3, tree, block[cookie_tree + len(MAGIC_COOKIE_TREE):]
            except Exception as e:
                print(f"Failed to deserialize Huffman tree: {e}")

        return 2, None, block

    def __read_directory(self, block, tree):
        cookie_dir = block.find(MAGIC_COOKIE_DIR)
        if cookie_dir >= 0:
            path_dir = block[:cookie_dir]
            bits = self.__bytes_to_bits(path_dir)
            count = bits[-8:]
            decoded_path, other_bits = tree.decode(bits, int(count, 2))
            block = block[cookie_dir + len(MAGIC_COOKIE_DIR):]
            return 4, decoded_path, other_bits, block
        else:
            return 3, None, None, block

    def __reed_data(self, bits, block, tree):
        cookie_data = block.find(MAGIC_COOKIE_DATA)

        if cookie_data >= 0:
            last_data = block[:cookie_data]
            bits += self.__bytes_to_bits(last_data)
            count = bits[-8:]

            if count:
                decoded_data, other_bits = tree.decode(bits, int(count, 2))
            else:
                decoded_data, other_bits = tree.decode(bits)

            block = block[cookie_data + len(MAGIC_COOKIE_DATA):]
            return 2, decoded_data, other_bits, block
        else:
            bits += self.__bytes_to_bits(block)
            decoded_data, other_bits = tree.decode(bits)
            return 4, decoded_data, other_bits, bytes()

    @staticmethod
    def __bytes_to_bits(data):
        # Преобразование каждого байта в последовательность битов
        bits = ''.join(format(byte, '08b') for byte in data)
        return bits

    @staticmethod
    def __bits_to_bytes(bits, huffman_tree):
        decoded_chars = []
        current_bits = ''
        for bit in bits:
            current_bits += bit
            symbol = huffman_tree.decode(current_bits)
            if symbol is not None:
                decoded_chars.append(symbol)
                current_bits = ''
        decoded_data = ''.join(decoded_chars)
        return decoded_data, current_bits
