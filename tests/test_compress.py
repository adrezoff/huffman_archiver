import unittest
import os
import tempfile
from io import BytesIO
from unittest.mock import patch

from huffman_method import (Compressor, HuffmanTree,
                            END_PATH, END_DATA, MD5, MAGIC_BYTES)


class TestCompressorMethods(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.test_dir.name, 'test.txt')
        with open(self.test_file, 'w') as f:
            f.write('This is a test file.' * 100)
        self.compressor = Compressor()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_bits_to_bytes(self):
        bits = "0100100001100101011011000110110001101111"
        remaining_bits, byte = self.compressor._bits_to_bytes(bits)

        self.assertEqual(remaining_bits, "")
        self.assertEqual(byte, b"Hello")

    def test_adder_zero(self):
        bits = "1101"
        byte, count_bits = self.compressor._adder_zero(bits)

        self.assertEqual(byte, b"\xd0")
        self.assertEqual(count_bits, b"\x04")

    def test_get_directory_info(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file1_path = os.path.join(tmp_dir, "file1.txt")
            with open(file1_path, "w") as file:
                file.write("test data")

            file2_path = os.path.join(tmp_dir, "file2.txt")
            with open(file2_path, "w") as file:
                file.write("more test data")

            size, info_dict = self.compressor.get_directory_info(tmp_dir)

            self.assertEqual(size, os.path.getsize(file1_path) +
                             os.path.getsize(file2_path))
            self.assertEqual(info_dict,
                             {file1_path: "file", file2_path: "file"})

    def test_compress_empty_dir(self):
        with (tempfile.TemporaryDirectory() as tmp_dir):
            outfile = BytesIO()
            file_path = os.path.join(tmp_dir, "empty_dir")

            self.compressor.compress_empty_dir(outfile, file_path, file_path)

            hasher = MD5()
            hasher.hash('.'.encode('utf-8'))
            expected_result = b'\x00\x00\x00.' + END_PATH + \
                              END_DATA + hasher.get_hash()

            outfile.seek(0)
            data_in_file = outfile.read()
            self.assertEqual(data_in_file, expected_result)

    def test_generate_huffman_tree(self):
        with tempfile.NamedTemporaryFile() as tmp_file:
            file_path = tmp_file.name
            with open(file_path, "w") as file:
                file.write("test data")

            tree1 = self.compressor._generate_huffman_tree(file_path)

            with open(file_path, "r") as file:
                data = file.read()
            tree2 = HuffmanTree()
            tree2.add_block(data)
            tree2.build_tree()

            self.assertEqual(tree1.get_codes(), tree2.get_codes())

    def test_write_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test.txt")

            test = b'test'
            tree = HuffmanTree()
            tree.add_block(test)
            tree.build_tree()

            with open(file_path, "wb") as file:
                file.write(test)

            outfile = BytesIO()

            self.compressor.write_data(outfile, file_path, MD5(), tree)

            outfile.seek(0)
            data_in_file = outfile.read()
            hasher = MD5()
            hasher.hash(test)

            self.assertEqual(data_in_file, b'\x70\x02' +
                             END_DATA + hasher.get_hash())

    def test_make_header(self):
        outfile = BytesIO()

        self.compressor._make_header(outfile)

        expected_header = bytes([self.compressor.version, 0]) + b'\x00' * 30
        outfile.seek(0)
        data_in_file = outfile.read()
        self.assertEqual(data_in_file, expected_header)

    @patch('os.path.getsize')
    def test_compress_file(self, mock_getsize):
        with (tempfile.TemporaryDirectory() as tmp_dir):
            file_path = os.path.join(tmp_dir, "file.txt")
            test = 'test'
            with open(file_path, "w") as file:
                file.write(test)

            tree = HuffmanTree()
            tree.add_block(test.encode())
            tree.build_tree()

            mock_getsize.return_value = 10

            outfile = BytesIO()

            path_in = tmp_dir
            relative_path = os.path.relpath(file_path, path_in)
            expected_header = b'\x01\x01\x00' + \
                              relative_path.encode('utf-8') + \
                              END_PATH

            self.compressor.compress_file(outfile, file_path, path_in, None)

            outfile.seek(0)
            header = outfile.read(len(expected_header))
            ser_tree = tree.serialize_to_string()
            ser_tree_in_file = outfile.read(len(ser_tree))
            self.assertEqual(header, expected_header)
            self.assertEqual(ser_tree_in_file, ser_tree)

    def test_compress_directory_with_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file1_path = os.path.join(tmp_dir, "file1.txt")
            with open(file1_path, "w") as file:
                file.write("Test data 1")

            file2_path = os.path.join(tmp_dir, "file2.txt")
            with open(file2_path, "w") as file:
                file.write("Test data 2")

            original_size, compressed_size = self.compressor.compress(
                tmp_dir, tmp_dir)

            self.assertGreater(original_size, 0)
            self.assertGreater(compressed_size, 0)

    def test_compress(self):
        compressor = Compressor()
        output_dir = self.test_dir.name
        output_file = os.path.join(output_dir, 'test.txt.huff')
        compressor.compress(self.test_file, output_dir)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'rb') as f:
            magic_header = f.read(len(MAGIC_BYTES))
            self.assertEqual(magic_header, MAGIC_BYTES)

    def test_compress_directory(self):
        compressor = Compressor()
        output_dir = self.test_dir.name
        name = os.path.basename(output_dir)
        output_file = os.path.join(output_dir, name + '.huff')
        compressor.compress(self.test_dir.name, output_dir)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'rb') as f:
            magic_header = f.read(len(MAGIC_BYTES))
            self.assertEqual(magic_header, MAGIC_BYTES)


if __name__ == '__main__':
    unittest.main()
