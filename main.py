import argparse
import time

from Huffman_method import Decompressor, Compressor


def calculate_percentage(size_path_in, size_archive):
    """
    Вычисляет процент сжатия.
    Args:
        size_path_in (int): Размер исходных данных.
        size_archive (int): Размер архива.

    Returns:
        int: Процент сжатия в диапазоне [0,100).
    """
    if size_path_in == 0:
        return 0  # Избегаем деления на ноль
    return ((size_path_in - size_archive) / size_path_in) * 100


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
        time1 = time.time()
        input = args.input_path
        output = args.output_path
        size_path, size_arch = compressor.compress(input, output)
        time2 = time.time()
        percents = calculate_percentage(size_path, size_arch)

        print(f'\nCompress time: {time2 - time1} sec.')
        print(f'Difference size: {size_path - size_arch} bytes')
        print(f'Percents compress: {percents} %')

    elif args.decompress:
        decompressor = Decompressor()
        time1 = time.time()
        decompressor.decompress(args.input_path, args.output_path)
        time2 = time.time()
        print(f'\nDecompress time: {time2 - time1} sec.')


if __name__ == "__main__":
    main()
