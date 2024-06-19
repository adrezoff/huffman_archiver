import unittest
from unittest.mock import patch

from huffman_method.progress_bar import ProgressBar
from io import StringIO


class TestProgressBar(unittest.TestCase):
    def setUp(self):
        self.progress_bar = ProgressBar(total=100, length=10)

    def test_update(self):
        self.progress_bar.update(10)
        self.assertEqual(self.progress_bar.progress, 10)

    def test_update_with_point(self):
        self.progress_bar.update_with_point(50)
        self.assertEqual(self.progress_bar.progress, 50)

    @patch('sys.stdout', new_callable=StringIO)
    def test_drawer(self, mock_stdout):
        self.progress_bar.drawer(0.5)
        expected_output = '\r[#####     ] 50.00%'
        self.assertEqual(mock_stdout.getvalue(), expected_output)

    def test_reset(self):
        self.progress_bar.reset(200)
        self.assertEqual(self.progress_bar.total, 200)
        self.assertEqual(self.progress_bar.progress, 0)


if __name__ == '__main__':
    unittest.main()
