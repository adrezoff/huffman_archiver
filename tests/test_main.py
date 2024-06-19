import os
import tempfile
import unittest
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from huffman_method import MD5
from main import format_size, calculate_percentage, main, set_password


class TestMain(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()

        self.test_file = os.path.join(self.test_dir.name, 'test_file.txt')
        with open(self.test_file, 'w') as f:
            f.write('Test file content')

        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, 'input.txt')
        self.output_path = os.path.join(self.temp_dir.name, 'input.txt.huff')
        with open(self.input_path, 'w') as f:
            f.write('test data for compression')

    def tearDown(self):
        self.test_dir.cleanup()

    def test_percentage_when_size_path_in_zero(self):
        size_path_in = 0
        size_archive = 100
        result = calculate_percentage(size_path_in, size_archive)
        self.assertEqual(result, 0)

    def test_percentage_when_size_path_in_non_zero(self):
        size_path_in = 1000
        size_archive = 500
        result = calculate_percentage(size_path_in, size_archive)
        self.assertEqual(result, 50.0)

    def test_formatting(self):
        size_bytes = 0
        expected_formatted_size = '0.00 B'
        self.assertEqual(format_size(size_bytes), expected_formatted_size)

        size_bytes = 1023
        expected_formatted_size = '1023.00 B'
        self.assertEqual(format_size(size_bytes), expected_formatted_size)

        size_bytes = 1024
        expected_formatted_size = '1.00 KiB'
        self.assertEqual(format_size(size_bytes), expected_formatted_size)

        size_bytes = 1024 * 1024
        expected_formatted_size = '1.00 MiB'
        self.assertEqual(format_size(size_bytes), expected_formatted_size)

        size_bytes = 1024 * 1024 * 1024
        expected_formatted_size = '1.00 GiB'
        self.assertEqual(format_size(size_bytes), expected_formatted_size)

    @patch('sys.stdout', new_callable=StringIO)
    def test_compress_binary(self, mock_stdout):
        args = ['-c', '-b', self.input_path, self.output_path]
        with patch('sys.argv', ['program_name'] + args):
            main()
        self.assertTrue(os.path.exists(self.output_path))
        self.assertTrue(os.path.getsize(self.output_path) > 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_compress_text(self, mock_stdout):
        args = ['-c', '-t', self.input_path, self.temp_dir.name]
        with patch('sys.argv', ['program_name'] + args):
            main()
        self.assertTrue(os.path.exists(self.output_path))
        self.assertTrue(os.path.getsize(self.output_path) > 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_compress_bin(self, mock_stdout):
        args = ['-c', '-b', self.input_path, self.temp_dir.name]
        with patch('sys.argv', ['program_name'] + args):
            main()
        self.assertTrue(os.path.exists(self.output_path))
        self.assertTrue(os.path.getsize(self.output_path) > 0)

    @patch('sys.stdout', new_callable=StringIO)
    def test_decompress_text(self, mock_stdout):
        args = ['-c', '-t', self.input_path, self.temp_dir.name]
        with patch('sys.argv', ['program_name'] + args):
            main()

        decompressor_args = ['-d',
                             self.output_path,
                             os.path.join(self.temp_dir.name, 'decompressed')]
        with patch('sys.argv', ['program_name'] + decompressor_args):
            main()

        result = os.path.exists(os.path.join(self.temp_dir.name,
                                             'decompressed/input.txt'))
        self.assertTrue(result)
        with open(os.path.join(self.temp_dir.name,
                               'decompressed/input.txt'), 'r') as f:
            decompressed_data = f.read()
        self.assertEqual(decompressed_data, 'test data for compression')

    @patch('sys.stdout', new_callable=StringIO)
    def test_decompress_bin(self, mock_stdout):
        args = ['-c', '-b', self.input_path, self.temp_dir.name]
        with patch('sys.argv', ['program_name'] + args):
            main()

        decompressor_args = ['-d',
                             self.output_path,
                             os.path.join(self.temp_dir.name, 'decompressed')]
        with patch('sys.argv', ['program_name'] + decompressor_args):
            main()

        result = os.path.exists(os.path.join(self.temp_dir.name,
                                             'decompressed/input.txt'))
        self.assertTrue(result)
        with open(os.path.join(self.temp_dir.name,
                               'decompressed/input.txt'), 'r') as f:
            decompressed_data = f.read()
        self.assertEqual(decompressed_data, 'test data for compression')

    @patch('builtins.input')
    @patch('os.path.isdir', return_value=False)
    @patch('os.path.exists', side_effect=[True, True])
    @patch('getpass.getpass', side_effect=['password', 'password', ''])
    def test_set_password_success(self, mock_getpass,
                                  mock_exists,
                                  mock_isdir,
                                  mock_input):
        mock_input.side_effect = [self.input_path, '']

        hasher = MD5()
        hasher.hash(b'password')
        expected = {self.input_path: hasher.get_hash()}
        result = set_password(self.temp_dir.name)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
