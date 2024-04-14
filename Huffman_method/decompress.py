import os
import getpass

from Huffman_method.hasher import MD5
from Huffman_method.coding import aes_decrypt
from Huffman_method.huffman import HuffmanTree
from Interfaces.decompress import IDecompressor
from Huffman_method.const_byte import *
from Huffman_method.progress_bar import ProgressBar


class Decompressor(IDecompressor):
    def __init__(self, block_size=512):
        self.block_size = block_size
        self.version = 2
        self.codec = None
        self.open_mode = ''
        self.progress_bar = ProgressBar()
        self.out_path = ''
        self.archive_path = ''

    def decompress(self, archive_path, out_path):
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
                        raise ValueError(f'Archive is damaged[invalid type file]')
                except ValueError as e:
                    print(f'\n{e.args[0]}')
                    return False
        return True

    def check_magic_bytes(self, file):
        magic_bytes = file.read(len(MAGIC_BYTES))
        self.progress_bar.update(len(MAGIC_BYTES))
        if magic_bytes != MAGIC_BYTES:
            raise ValueError(f'File is not huffman archive')

    def check_header(self, file):
        header = file.read(32)

        arch_version = header[0]

        if arch_version != self.version:
            raise ValueError(f'This decompressor do not supported this archive version')

        flag_codec = header[1]

        supported_codec = [None, 'utf-8']
        if 0 <= flag_codec < len(supported_codec):
            self.codec = supported_codec[flag_codec]

            if self.codec is None:
                self.open_mode = 'ab'
            else:
                self.open_mode = 'a'
        else:
            raise ValueError(f'This decompressor do not supported this archive codec')

        self.progress_bar.update(len(header))

    def check_file_type(self, file):
        type_file = file.read(1)
        if type_file == b'\x00' or type_file == b'\x01':
            self.progress_bar.update(len(type_file))
            return type_file
        raise ValueError(f'Archive is damaged')

    def __decompress(self, file):
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

    def decompress_empty_file(self, file):
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
                    return
            else:
                out_dir, buffer = self.get_path(file, hasher)

            end_data = buffer[:4]
            if len(end_data) < 4:
                chunk = file.read(4 - len(end_data))
                self.progress_bar.update(len(chunk))
                buffer += chunk

            if end_data == END_DATA:
                self.check_hash(file, hasher, out_dir, buffer)
            else:
                raise ValueError(f'File is damage')
        except ValueError as e:
            raise e

    def decompress_file(self, file):
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
                    return
                tree, buffer = self.get_tree(file, hasher, hash_pass, buffer)
            else:
                out_dir, buffer = self.get_path(file, hasher)
                tree, buffer = self.get_tree(file, hasher, buffer=buffer)

            buffer = self.read_data(file, tree, hasher, out_dir, buffer)
            self.check_hash(file, hasher, out_dir, buffer)
        except ValueError as e:
            raise e

    def decompress_empty_dir(self, file):
        hasher = MD5()

        is_emtpy = file.read(1)
        level_protected = file.read(1)
        if is_emtpy != b'\x00' and level_protected != b'\x00':
            raise ValueError('File is not correct')

        out_dir, buffer = self.get_path(file, hasher)

        end_data = buffer[:4]
        if end_data != END_DATA:
            raise ValueError('File is damaged!')

        buffer = buffer[4:]

        try:
            self.check_hash(file, hasher, out_dir, buffer)
        except ValueError as e:
            raise e

    def get_path(self, file, hasher, buffer=b''):
        end_path = buffer.find(END_PATH)

        if end_path < 0:
            try:
                buffer += file.read(self.block_size)
                return self.get_path(file, hasher, buffer)
            except ValueError as e:
                raise e
        else:
            bytes_path = buffer[:end_path]
            hasher.hash(bytes_path)
            self.progress_bar.update(len(buffer))

            relative_path = bytes_path.decode('utf-8')
            if relative_path == '.':
                relative_path = ''
            full_arch_name = os.path.basename(self.archive_path)
            arch_name = os.path.splitext(full_arch_name)[0]
            out_dir = os.path.join(self.out_path, arch_name, relative_path)

            return out_dir, buffer[end_path + len(END_PATH):]

    def get_tree(self, file, hasher, hash_pass=None, buffer=b''):
        end_tree = buffer.find(END_TREE)

        if end_tree >= 0:
            serialized_tree, buffer = buffer[:end_tree], buffer[end_tree:]
            if len(buffer) < 4:
                self.progress_bar.update(4 - len(buffer))
                buffer += file.read(4 - len(buffer))
            buffer = buffer[len(END_TREE):]
        else:
            serialized_tree = buffer
            for block in iter(lambda: file.read(self.block_size), b''):
                if not block:
                    raise ValueError(f'File is damaged.')

                self.progress_bar.update(len(block))

                end_tree_block = block.find(END_TREE)
                if end_tree_block >= 0:
                    serialized_tree += block[:end_tree_block]
                    buffer = block[end_tree_block + 4:]
                    break
                serialized_tree += block

        if hash_pass:
            tree = self.get_protected_tree(serialized_tree, hash_pass, hasher)
        else:
            hasher.hash(serialized_tree)
            tree = HuffmanTree()
            tree.deserialize_from_string(serialized_tree)

        return tree, buffer

    @staticmethod
    def get_protected_tree(serialized_tree, hash_pass, hasher):
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

    def read_data(self, file, tree, hasher, out_file, buffer):
        dir_path = os.path.dirname(out_file)
        os.makedirs(dir_path, exist_ok=True)
        bits = ''
        with open(out_file, self.open_mode) as outfile:
            end_data = buffer.find(END_DATA)
            if end_data < 0:
                buffer, bits = self.decoded_block(outfile, bits, buffer, end_data, tree, hasher)
                for block in iter(lambda: file.read(self.block_size), b''):
                    if not block:
                        raise ValueError(f'File is damaged..')
                    self.progress_bar.update(len(block))
                    buffer = buffer[-3:] + block
                    end_data = buffer.find(END_DATA)
                    buffer, bits = self.decoded_block(outfile, bits, buffer, end_data, tree, hasher)
                    if end_data >= 0:
                        return buffer
            else:
                buffer, bits = self.decoded_block(outfile, bits, buffer, end_data, tree, hasher)
        return buffer

    def decoded_block(self, outfile, bits, buffer, end_data, tree, hasher):
        if end_data >= 0:
            encoded_data = buffer[:end_data-1]
            last_byte = buffer[end_data-1]
            count = last_byte
            buffer = buffer[end_data + 4:]
        else:
            encoded_data = buffer[:-3]
            count = -1
            buffer = buffer[-3:]
        bits += self._bytes_to_bits(encoded_data)

        decoded_data, bits = tree.decode(bits, count)
        outfile.write(decoded_data)

        if self.codec is None:
            hasher.hash(decoded_data)
        else:
            hasher.hash(decoded_data.encode(self.codec))

        return buffer, bits

    def check_hash(self, file, hasher, out_path, buffer=b''):
        if len(buffer) < 16:
            chunk = file.read(16 - len(buffer))
            buffer += chunk

        _hash_file = hasher.get_hash()

        if _hash_file != buffer[:16]:
            raise ValueError(f'File [{out_path}] is damaged!')

        buffer = buffer[16:]

        pointer = file.tell()
        file.seek(pointer-len(buffer))
        self.progress_bar.update_with_point(file.tell())
        return

    def skip_file(self, file, buffer=b''):
        pointer = file.tell()

        end_data = buffer.find(END_DATA)
        if end_data >= 0:
            file.seek(pointer - len(buffer) + end_data + len(END_DATA) + 16)
            self.progress_bar.update_with_point(file.tell())
            return

        for block in iter(lambda: file.read(self.block_size), b''):
            if not block:
                raise ValueError(f'Archive is damaged.[not search end data file]')
            pointer = file.tell()
            buffer = buffer[-3:] + block
            end_data = buffer.find(END_DATA)
            if end_data >= 0:
                file.seek(pointer - len(buffer) + end_data + len(END_DATA) + 16)
                self.progress_bar.update_with_point(file.tell())
                return

    @staticmethod
    def authentication(path, auth_bytes):
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
    def get_pass_hash(name):
        print(f'\nВведите пароль от файла {name} '
              '(или пустую строку чтобы пропустить файл):')

        password = getpass.getpass()
        if not password:
            print(f'\nВы пропустили файл {name}')
            return None

        hasher = MD5()
        hasher.hash(password.encode())
        pass_hash = hasher.get_hash()

        return pass_hash

    @staticmethod
    def _bytes_to_bits(data):
        bits = ''.join(format(byte, '08b') for byte in data)
        return bits

    @staticmethod
    def _bits_to_bytes(bits, tree):
        decoded_chars = []
        current_bits = ''
        for bit in bits:
            current_bits += bit
            symbol = tree.decode(current_bits)
            if symbol is not None:
                decoded_chars.append(symbol)
                current_bits = ''
        decoded_data = ''.join(decoded_chars)
        return decoded_data, current_bits
