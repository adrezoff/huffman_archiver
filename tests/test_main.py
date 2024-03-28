import unittest
from unittest.mock import patch
from io import StringIO
import os
import main
import tempfile


class TestMain(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, 'input.txt')
        self.output_path = os.path.join(self.temp_dir.name, 'input.txt.huff')
        with open(self.input_path, 'w') as f:
            f.write('test data for compression')

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('sys.stdout', new_callable=StringIO)
    def test_compress_binary(self, mock_stdout):
        args = ['-c', '-b', self.input_path, self.output_path]
        with patch('sys.argv', ['program_name'] + args):
            main.main()
        self.assertTrue(os.path.exists(self.output_path))
        self.assertTrue(os.path.getsize(self.output_path) > 0)
        self.assertIn('Compress time:', mock_stdout.getvalue())
        self.assertIn('Difference size:', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_compress_text(self, mock_stdout):
        args = ['-c', '-t', self.input_path, self.output_path]
        with patch('sys.argv', ['program_name'] + args):
            main.main()
        self.assertTrue(os.path.exists(self.output_path))
        self.assertTrue(os.path.getsize(self.output_path) > 0)
        self.assertIn('Compress time:', mock_stdout.getvalue())
        self.assertIn('Difference size:', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_decompress(self, mock_stdout):
        compressor_args = ['-c', '-t', self.input_path, self.temp_dir.name]
        with patch('sys.argv', ['program_name'] + compressor_args):
            main.main()

        decompressor_args = ['-d',
                             self.output_path,
                             os.path.join(self.temp_dir.name, 'decompressed')]
        with patch('sys.argv', ['program_name'] + decompressor_args):
            main.main()

        self.assertTrue(os.path.exists(self.input_path))
        with open(self.input_path, 'r') as f:
            decompressed_data = f.read()
        self.assertEqual(decompressed_data, 'test data for compression')
        self.assertIn('Decompress time:', mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
