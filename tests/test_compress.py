import unittest
import tempfile
import os
from Huffman_method import Compressor, HuffmanTree, MAGIC_COOKIE_DIR


class TestCompressor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.test_dir.name, 'test.txt')
        with open(self.test_file, 'w') as f:
            f.write('asdfghjklqwertyui' * 10000)
    def tearDown(self):
        self.test_dir.cleanup()

    def test_compress_file(self):
        compressor = Compressor()
        output_file = os.path.join(self.test_dir.name, 'test.huff')
        size_diff = compressor.compress(self.test_file, output_file)
        self.assertTrue(os.path.exists(output_file))
        self.assertGreater(size_diff, 0)

    def test_compress_empty_directory(self):
        compressor = Compressor()
        output_dir = os.path.join(self.test_dir.name, 'empty_dir')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'empty_dir.huff')
        size_diff = compressor.compress(output_dir, output_file)
        self.assertTrue(os.path.exists(output_file))
        epsilon = 1024
        self.assertGreater(epsilon, abs(size_diff))

    def test_make_header(self):
        compressor = Compressor()
        with open(os.path.join(self.test_dir.name, 'header.huff'), 'wb') as f:
            compressor._make_header(f)
        with open(os.path.join(self.test_dir.name, 'header.huff'), 'rb') as f:
            header = f.read(32)
            self.assertEqual(header[0], compressor.version)

    def test_generate_huffman_tree(self):
        compressor = Compressor()
        tree = compressor._generate_huffman_tree(self.test_file, '')
        self.assertIsInstance(tree, HuffmanTree)

    def test_bits_to_bytes(self):
        compressor = Compressor()
        bits = '11001100'
        remaining_bits, byte = compressor._bits_to_bytes(bits)
        self.assertEqual(remaining_bits, '')
        self.assertEqual(byte, b'\xcc')

    def test_adder_zero(self):
        compressor = Compressor()
        bits = '110011'
        result_byte = int('11001100', 2).to_bytes(1, byteorder='big')
        byte, count = compressor._adder_zero(bits)
        self.assertEqual(byte, result_byte)
        self.assertEqual(count, b'\x02')

    def test_write_directory(self):
        compressor = Compressor()
        codes = {'a': '101', 'b': '011', 'c': '111'}
        result_in_bits = '1010111110000000' + '00000111'
        result_byte = int(result_in_bits, 2).to_bytes(3, byteorder='big')
        path = os.path.join(self.test_dir.name, 'directory.huff')
        with open(path, 'wb') as f:
            compressor._write_directory(f, 'abc', codes)
        with open(path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, result_byte + MAGIC_COOKIE_DIR)

    def test_is_file(self):
        compressor = Compressor()
        self.assertTrue(compressor._is_file(self.test_file))
        self.assertFalse(compressor._is_file(self.test_dir.name))

    def test_compress_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_files = ['file1.txt', 'file2.txt']
            huge_string = 'abcyqtroyfihsldf' * 10000
            for file_name in test_files:
                with open(os.path.join(temp_dir, file_name), 'w') as f:
                    f.write(huge_string)

            with tempfile.TemporaryDirectory() as output_dir:
                compressor = Compressor()
                diff_size = compressor.compress(temp_dir, output_dir)
                self.assertTrue(diff_size > 0)

                for file_name in test_files:
                    os.unlink(os.path.join(temp_dir, file_name))


if __name__ == '__main__':
    unittest.main()
