import os
from Huffman_method.huffman import HuffmanTree
from Interfaces.decompress import DecompressorABC
from Huffman_method.const_byte import *


class Decompressor(DecompressorABC):
    def __init__(self, block_size=33554432):
        self.block_size = block_size

    def decompress(self, archive_file, out_path):
        os.makedirs(out_path, exist_ok=True)
        buffer = bytes()
        with open(archive_file, 'rb') as file:
            pass

    @staticmethod
    def __check_magic_header(block):
        magic_list = [MAGIC_HEADER, SPECIAL_BYTES]
        for magic_entry in magic_list:
            if len(block) >= len(MAGIC_HEADER.__add__(SPECIAL_BYTES)):
                if block[:len(magic_entry)] == magic_entry:
                    return True, block[len(magic_entry):]
                else:
                    raise ValueError("Invalid identify archive format")

            return False, block

    @staticmethod
    def __read_tree(block):
        cookie_tree = block.find(MAGIC_COOKIE_TREE)
        if cookie_tree >= 0:
            serializable_tree = block[:cookie_tree]
            try:
                tree = HuffmanTree()
                tree.deserialize_from_string(serializable_tree)
                return True, tree, block
            except Exception as e:
                print(f"Failed to deserialize Huffman tree: {e}")

        return False, None, block

    def __read_directory(self, block):
        cookie_dir = block.find(MAGIC_COOKIE_DIR)
        if cookie_dir >= 0:
            path_dir = block[:cookie_dir]
            pass # доделать
        else:
            return False, None, block

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

        # обработать символы которые остаются в конце


        return ''.join(decoded_chars)

    def __iter_file(self, file_obj):
        while True:
            block = file_obj.read(self.block_size)
            if not block:
                break
            yield block
