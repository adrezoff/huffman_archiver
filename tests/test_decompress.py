import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from Huffman_method import *


class TestDecompressor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = TemporaryDirectory()
        cls.test_file = os.path.join(cls.test_dir.name, 'test.bin')
        cls.archive_file = os.path.join(cls.test_dir.name, 'test.bin.huff')

        with open(cls.test_file, 'w') as f:
            f.write('iefrhofkwdw[eofhwe[' * 100)

        compressor = Compressor()
        compressor.compress(cls.test_file, cls.test_dir.name)

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
        self.assertIsNone(result)

    def test_check_file_type(self):
        decompressor = Decompressor()
        with open(self.archive_file, 'rb') as f:
            f.seek(36)
            file_type_byte = f.read(1)
            result = decompressor.check_file_type(BytesIO(file_type_byte))
        self.assertEqual(result, b'\x01')


if __name__ == '__main__':
    unittest.main()
