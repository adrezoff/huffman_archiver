import argparse
import time

from Huffman_method import Decompressor, Compressor


def main():
    parser = argparse.ArgumentParser(description='Huffman archiver')
    parser.add_argument('-c', '--compress', action='store_true', help='Compress operation')
    parser.add_argument('-d', '--decompress', action='store_true', help='Decompress operation')
    parser.add_argument('-b', '--bin', action='store_true', help='Binary method')
    parser.add_argument('-t', '--text', action='store_true', help='Text method')
    parser.add_argument('input_path', help='Input file/directory path')
    parser.add_argument('output_path', help='Output file/directory path')

    args = parser.parse_args()

    if args.compress:
        method = '-b' if args.bin else '-t'
        compressor = Compressor() if method == '-b' else Compressor('utf-8')
        time1 = time.time()
        diff_size = compressor.compress(args.input_path, args.output_path)
        time2 = time.time()
        print(f'Compress time: {time2 - time1} sec.')
        print(f'Difference size: {diff_size} bytes')

    elif args.decompress:
        decompressor = Decompressor()
        time1 = time.time()
        decompressor.decompress(args.input_path, args.output_path)
        time2 = time.time()
        print(f'Decompress time: {time2 - time1} sec.')


if __name__ == "__main__":
    main()
