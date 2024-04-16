import os.path
import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from Huffman_method import *


class TestDecompressor(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.test_file = os.path.join(self.test_dir.name, 'test.bin')
        self.archive_file = os.path.join(self.test_dir.name, 'test.bin.huff')

        self.test_file2 = os.path.join(self.test_dir.name, 'test2.bin')
        self.archive_file2 = os.path.join(self.test_dir.name, 'test2.bin.huff')

        self.test_file3 = os.path.join(self.test_dir.name, 'test3.bin')
        self.archive_file3 = os.path.join(self.test_dir.name, 'test3.bin.huff')

        self.empty_dir = TemporaryDirectory()

        with open(self.test_file, 'w') as f:
            f.write('iefrhofkwdw[eofhw1e[' * 100)

        with open(self.test_file2, 'w') as f:
            f.write('fwjef[jdkfjwiojasj19127' * 100)

        open(self.test_file3, 'ab').close()

        compressor = Compressor()
        compressor.compress(self.test_file, self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_check_magic_bytes(self):
        decompressor = Decompressor()
        with open(self.archive_file, 'rb') as f:
            result = decompressor.check_magic_bytes(f)
        self.assertEqual(result, True)

    def test_check_header(self):
        decompressor = Decompressor()
        with open(self.archive_file, 'rb') as f:
            f.seek(4)
            header_bytes = f.read(32)
            result = decompressor.check_header(BytesIO(header_bytes))
        self.assertTrue(result)

    def test_check_file_type(self):
        decompressor = Decompressor()
        with open(self.archive_file, 'rb') as f:
            f.seek(36)
            file_type_byte = f.read(1)
            result = decompressor.check_file_type(BytesIO(file_type_byte))
        self.assertEqual(result, b'\x01')

    def test_decompress_empty_file(self):
        compressor = Compressor()
        compressor.compress(self.test_file3, self.test_dir.name)

        decompressor = Decompressor()
        out_dir = os.path.join(self.test_dir.name, 'out')
        decompressor.decompress(self.archive_file3, out_dir)

        out = os.path.join(out_dir, 'test3.bin')

        self.assertTrue(os.path.isfile(out))
        self.assertTrue(os.path.getsize(out) == 0)

    def test_decompress_empty_dir(self):
        compressor = Compressor()
        name = os.path.basename(self.empty_dir.name)
        compressor.compress(self.empty_dir.name, self.test_dir.name)

        file = os.path.join(self.test_dir.name, f'{name}.huff')

        decompressor = Decompressor()
        decompressor.decompress(file, self.test_dir.name)

        out = os.path.join(self.test_dir.name, name)

        self.assertTrue(os.path.exists(out))
        self.assertTrue(os.path.isdir(out))
        self.assertTrue(os.path.getsize(out) > 0)

    @patch('getpass.getpass', side_effect=['pasdwdasd'])
    def test_decompress_protected(self, get_pass):
        compressor = Compressor()
        hasher = MD5()
        hasher.hash(b'pasdwdasd')
        protected = {self.test_file2: hasher.get_hash()}
        compressor.compress(self.test_file2,
                            self.test_dir.name,
                            protected)

        decompressor = Decompressor()
        out_dir = os.path.join(self.test_dir.name, 'out')

        decompressor.decompress(self.archive_file2, out_dir)
        out_file = os.path.join(out_dir, 'test2.bin')

        self.assertTrue(os.path.isfile(out_file))

        data_before = b''
        with open(self.test_file2, 'rb') as file:
            data_before = file.read()
        data_after = b''
        with open(out_file, 'rb') as file:
            data_after = file.read()

        self.assertEqual(data_before, data_after)

    @patch('getpass.getpass', side_effect=[''])
    def test_skip(self, get_pass):
        compressor = Compressor()
        hasher = MD5()
        hasher.hash(b'pasdwdasd')
        protected = {self.test_file2: hasher.get_hash()}
        compressor.compress(self.test_file2,
                            self.test_dir.name,
                            protected)

        decompressor = Decompressor()
        out_dir = os.path.join(self.test_dir.name, 'out')

        decompressor.decompress(self.archive_file2, out_dir)
        out_file = os.path.join(out_dir, 'test1.bin')

        self.assertFalse(os.path.isfile(out_file))

    def test_bytes_to_bits_empty(self):
        data = b''
        expected = ''
        result = Decompressor._bytes_to_bits(data)
        self.assertEqual(result, expected)

    def test_bytes_to_bits_single_byte(self):
        data = b'\x00'
        expected = '00000000'
        result = Decompressor._bytes_to_bits(data)
        self.assertEqual(result, expected)

    def test_bytes_to_bits_multiple_bytes(self):
        data = b'\x01\x02\x03'
        expected = '000000010000001000000011'
        result = Decompressor._bytes_to_bits(data)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
