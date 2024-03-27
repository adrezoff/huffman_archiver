import unittest
import tempfile
import os
from Huffman_method import Compressor


class TestCompressor(unittest.TestCase):

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
