import hashlib
import os
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from main import format_size, set_password, calculate_percentage


class TestCompressor(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.test_file = os.path.join(self.test_dir.name, 'test_file.txt')
        with open(self.test_file, 'w') as f:
            f.write('Test file content')

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

    @patch('main.getpass.getpass', return_value='password123')
    @patch('builtins.input', side_effect=['', ''])
    def test_password_setting(self, mock_input, mock_getpass):
        # Создаем временную директорию
        with TemporaryDirectory() as temp_dir:
            # Создаем временный файл
            test_file = os.path.join(temp_dir, 'test_file.txt')
            with open(test_file, 'w') as f:
                f.write('Test file content')

            # Вызываем функцию установки пароля
            passwords = set_password(temp_dir)

            # Проверяем, что пароль был установлен для созданного файла
            self.assertIn(test_file, passwords.keys())

            # Проверяем, что значение пароля непустое
            self.assertTrue(passwords[test_file])

            # Проверяем, что пароль правильно установлен
            self.assertEqual(passwords[test_file], '5f4dcc3b5aa765d61d8327deb882cf99')  # MD5 hash of 'password123'


if __name__ == '__main__':
    unittest.main()
