import os

from Huffman_method.coding import aes_encrypt
from Huffman_method.huffman import HuffmanTree
from Interfaces.compress import ICompressor
from Huffman_method.const_byte import *
from Huffman_method.progress_bar import ProgressBar
from Huffman_method.hasher import MD5


class Compressor(ICompressor):
    def __init__(self, codec=None, block_size=128):
        self.block_size = block_size
        self.version = 2
        self.codec = codec
        self.open_mode_files = ''
        if codec is None:
            self.open_mode = 'rb'
        else:
            self.open_mode = 'r'
        self.progress_bar = ProgressBar()

    def compress(self, path_in, path_out, protected_files=None):
        if not os.path.exists(path_in):
            raise ValueError(f'No search file or dir [{path_in}]')
        elif not path_out:
            raise ValueError(f'Is empty string [{path_out}]')

        total_size, all_files = self.get_directory_info(path_in)

        self.progress_bar.reset(total_size)

        os.makedirs(path_out, exist_ok=True)
        name_dir = os.path.basename(os.path.normpath(path_in))
        archive_file_path = os.path.join(path_out, f'{name_dir}.huff')

        if os.path.exists(archive_file_path):
            raise ValueError(f'Archive [{archive_file_path}] is exists')

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
                    self.compress_file(outfile, path_in, path_in, protected_files)
            else:
                for path, item_type in all_files.items():
                    if item_type == 'empty_directory':
                        self.compress_empty_dir(outfile, path, path_in)
                    elif item_type == 'file':
                        self.compress_file(outfile, path, path_in, protected_files)

        return total_size, os.path.getsize(archive_file_path)

    def _make_header(self, outfile):
        header = bytearray(32)
        header[0] = self.version
        supported_codec = {None: 0, 'utf-8': 1}
        if self.codec in supported_codec:
            header[1] = supported_codec[self.codec]
        else:
            raise ValueError(f'Codec {self.codec} is not supported!')
        outfile.write(bytes(header))

    @staticmethod
    def compress_empty_dir(outfile, file_path, path_in):
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

    def compress_file(self, outfile, file_path, path_in, protected_files):
        hasher = MD5()
        tree = None
        pass_hash = None
        if protected_files and (file_path in protected_files):
            pass_hash = protected_files[file_path]

        not_empty_file = self.write_header_file(outfile, file_path, path_in, hasher, pass_hash)

        if not_empty_file == b'\x01':
            tree = self.write_tree(outfile, file_path, hasher, pass_hash)
        self.write_data(outfile, file_path, hasher, tree)

    @staticmethod
    def write_header_file(outfile, file_path, path_in, hasher, pass_hash=None):
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

    def write_tree(self, outfile, file_path, hasher, pass_hash):
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

    def _generate_huffman_tree(self, file_path):
        tree = HuffmanTree(self.codec)

        with open(file_path, self.open_mode) as file:
            for block in iter(lambda: file.read(self.block_size), b''):
                if not block:
                    break
                tree.add_block(block)

        tree.build_tree()
        return tree

    def write_data(self, outfile, file_path, hasher, tree=None):
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
    def _bits_to_bytes(bits):
        bytes_list = []

        while len(bits) >= 8:
            byte = bits[:8]
            bits = bits[8:]
            bytes_list.append(int(byte, 2))

        return bits, bytes(bytes_list)

    @staticmethod
    def _adder_zero(bits):
        count = (8 - (len(bits) % 8)) % 8
        bits += '0' * count
        byte = int(bits, 2).to_bytes(1, byteorder='big')
        count_bits = count.to_bytes(1, byteorder='big')
        return byte, count_bits

    @staticmethod
    def get_directory_info(path):
        if os.path.isdir(path):
            stack = [path]
            total_size = 0
            info_dict = {}

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
