import argparse
import time
import os
import getpass
from typing import Dict

from encryption.hasher import MD5
from huffman_method import Decompressor, Compressor


def calculate_percentage(size_path_in: int, size_archive: int) -> float:
    """
    Вычисляет процент сжатия данных.

    :param size_path_in: Исходный размер данных.
    :param size_archive: Размер сжатых данных.
    :return: Процент сжатия.
    """
    if size_path_in == 0:
        return 0
    return ((size_path_in - size_archive) / size_path_in) * 100


def set_password(directory: str) -> Dict[str, bytes]:
    """
    Устанавливает пароль для файлов.

    :param directory: Директория с файлами.
    :return: Словарь паролей для файлов.
    """
    passwords = {}
    while True:
        if directory in passwords:
            break
        print('\nУкажите файлы для установки пароля '
              '(или пустую строку для продолжения сжатия):')
        path = input()
        if not path:
            return passwords
        dir_exists = os.path.isdir(path)
        if dir_exists:
            print('Ошибка. Это директория.')
            continue
        path_exists = os.path.exists(path)
        if not path_exists:
            print('Ошибка. Файл не существует.')
            continue
        absolute_path_path = os.path.abspath(path)
        absolute_path_dir = os.path.abspath(directory)
        file_stat = os.stat(absolute_path_path)
        dir_stat = os.stat(absolute_path_dir)
        path_exists_and_belongs = file_stat.st_dev == dir_stat.st_dev
        hasher = MD5()
        if path_exists_and_belongs:
            print('Придумайте пароль:')
            try:
                password = getpass.getpass()
            except UnicodeDecodeError:
                password = getpass.getpass(
                    prompt="Enter password:",
                    stream=None
                )
            while True:
                print('Введите пароль еще раз:')
                try:
                    password_accept = getpass.getpass()
                except UnicodeDecodeError:
                    password_accept = getpass.getpass(
                        prompt="Enter password:",
                        stream=None
                    )
                if not password_accept:
                    break
                if password == password_accept:
                    hasher.hash(password.encode())
                    passwords[path] = hasher.get_hash()
                    break
                print('Ошибка. Пароли не совпадают')
        else:
            print('Ошибка. Файл не принадлежит указанной директории.')
    return passwords


def format_size(size_bytes: int) -> str:
    """
    Форматирует размер файла в удобный для чтения формат.

    :param size_bytes: Размер файла в байтах.
    :return: Отформатированный размер файла.
    """
    size_units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    i = 0
    while size_bytes >= 1024 and i < len(size_units) - 1:
        size_bytes /= 1024.0
        i += 1
    return "{:.2f} {}".format(size_bytes, size_units[i])


def main() -> None:
    """
    Основная функция, выполняющая архивацию или разархивацию файлов.
    """
    parser = argparse.ArgumentParser(
        description='Huffman archiver'
    )
    parser.add_argument(
        '-c', '--compress',
        action='store_true',
        help='Операция сжатия'
    )
    parser.add_argument(
        '-d', '--decompress',
        action='store_true',
        help='Операция распаковки'
    )
    parser.add_argument(
        '-b', '--bin',
        action='store_true',
        help='Сжатие в бинарном виде'
    )
    parser.add_argument(
        '-t', '--text',
        action='store_true',
        help='Сжатие текстовых данных'
    )
    parser.add_argument(
        '-p', '--protect',
        action='store_true',
        help='Установка защиты на файлы'
    )
    parser.add_argument(
        'input_path',
        help='Путь к файлу/директории'
    )
    parser.add_argument(
        'output_path',
        help='Путь для сохранения архива/разархивированных данных'
    )

    args = parser.parse_args()

    if args.compress:
        method = '-b' if args.bin else '-t'
        compressor = Compressor() if method == '-b' else Compressor('utf-8')
        _input = args.input_path
        output = args.output_path
        protected_files = None
        if args.protect:
            protected_files = set_password(_input)
        time1 = time.time()

        try:
            size_path, size_arch = compressor.compress(_input,
                                                       output,
                                                       protected_files)
        except ValueError as e:
            print(f'\n{e.args[0]}')
            return

        time2 = time.time()
        percents = calculate_percentage(size_path, size_arch)

        print(f'\nВремя сжатия: {round(time2 - time1, 2)} сек.')
        print(f'Разница в размере: {format_size(size_path - size_arch)}')
        print(f'Процент сжатия: {round(percents, 2)} %')

    elif args.decompress:
        decompressor = Decompressor()
        time1 = time.time()
        if decompressor.decompress(args.input_path, args.output_path):
            time2 = time.time()
            print(f'\nВремя разжатия: {time2 - time1} сек.')
            print('Успешное завершение')
        else:
            print('Неудачное завершение')


if __name__ == "__main__":
    main()
