import argparse
import time
import os
import getpass
from Huffman_method.hasher import MD5
from Huffman_method import Decompressor, Compressor


def calculate_percentage(size_path_in, size_archive):
    if size_path_in == 0:
        return 0
    return ((size_path_in - size_archive) / size_path_in) * 100


def set_password(directory):
    passwords = {}
    while True:
        if dir in passwords:
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


def format_size(size_bytes):
    size_units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    i = 0
    while size_bytes >= 1024 and i < len(size_units) - 1:
        size_bytes /= 1024.0
        i += 1
    return "{:.2f} {}".format(size_bytes, size_units[i])


def main():
    parser = argparse.ArgumentParser(
        description='Huffman archiver'
    )
    parser.add_argument(
        '-c', '--compress',
        action='store_true',
        help='Compress operation'
    )
    parser.add_argument(
        '-d', '--decompress',
        action='store_true',
        help='Decompress operation'
    )
    parser.add_argument(
        '-b', '--bin',
        action='store_true',
        help='Binary method'
    )
    parser.add_argument(
        '-t', '--text',
        action='store_true',
        help='Text method'
    )
    parser.add_argument(
        '-p', '--protect',
        action='store_true',
        help='file protect'
    )
    parser.add_argument(
        'input_path',
        help='Input file/directory path'
    )
    parser.add_argument(
        'output_path',
        help='Output file/directory path'
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
            size_path, size_arch = compressor.compress(
                _input,
                output,
                protected_files
            )
        except ValueError as e:
            print(f'\n{e.args[0]}')
            return

        time2 = time.time()
        percents = calculate_percentage(size_path, size_arch)

        print(f'\nCompress time: {round(time2 - time1, 2)} sec.')
        print(f'Difference size: {format_size(size_path - size_arch)}')
        print(f'Percents compress: {round(percents, 2)} %')

    elif args.decompress:
        decompressor = Decompressor()
        time1 = time.time()
        if decompressor.decompress(args.input_path, args.output_path):
            time2 = time.time()
            print(f'\nDecompress time: {time2 - time1} sec.')
            print('Successful finished')
        else:
            print('Unsuccessful finished')


if __name__ == "__main__":
    main()
