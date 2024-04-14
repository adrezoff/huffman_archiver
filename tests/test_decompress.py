import unittest
from tempfile import TemporaryDirectory
from Huffman_method import *


class TestDecompressor(unittest.TestCase):
    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.archive_file = os.path.join(self.test_dir.name, 'test.huff')
        with open(self.archive_file, 'wb') as f:
            f.write(MAGIC_BYTES)
            f.write(b'\x01\x00')
            f.write(b'\x00' * 30)

        self.test_file = os.path.join(self.test_dir.name, 'test.bin')
        with open(self.test_file, 'w') as f:
            f.write('iefrhofkwdw[eofhwe[' * 100)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_decompress(self):
        compress = Compressor('utf-8')
        compress.compress(self.test_file, self.test_dir.name)
        decompressor = Decompressor()
        output_dir = os.path.join(self.test_dir.name, 'decompressed')
        archive_file = os.path.join(self.test_dir.name, 'test.bin.huff')
        decompressor.decompress(archive_file, output_dir)
        result = 'iefrhofkwdw[eofhwe[' * 100
        with open(output_dir + '/test.bin', 'r') as file:
            self.assertEqual(file.read(), result)

    def test_check_magic_header(self):
        decompressor = Decompressor()
        with open(self.archive_file, 'rb') as f:
            first_bytes = f.read(36)
            result = decompressor._check_magic_header(first_bytes)
        self.assertEqual(result, True)

    def test_read_tree(self):
        decompressor = Decompressor()
        tree_ser = HuffmanTree().serialize_to_string() + MAGIC_COOKIE_TREE
        flag, tree, remaining_bytes = decompressor._read_tree(tree_ser)
        self.assertEqual(flag, 2)
        self.assertIsInstance(tree, HuffmanTree)
        self.assertEqual(len(remaining_bytes), 0)

    def test_read_directory(self):
        decompressor = Decompressor()
        tree = HuffmanTree()
        tree.add_block(b'test_dir')
        tree.build_tree()
        data_bits = '0011010100111011010100' + '00' + '00000010'
        data_bytes = int(data_bits, 2).to_bytes(4, byteorder='big')
        block = data_bytes + MAGIC_COOKIE_DIR
        result = decompressor._read_directory(block, tree)
        flag, path, bits, remaining_bytes = result
        self.assertEqual(flag, 3)
        self.assertEqual(path, 'test_dir')
        self.assertEqual(bits, '')
        self.assertEqual(len(remaining_bytes), 0)

    def test_read_data(self):
        decompressor = Decompressor()
        tree = HuffmanTree()
        tree.add_block(b'test_data')
        tree.build_tree()
        data_bits = '1110001011101011001100' + '00' + '00000010'
        data_bytes = int(data_bits, 2).to_bytes(4, byteorder='big')
        block = data_bytes + MAGIC_COOKIE_DATA
        result = decompressor._read_data('', block, tree)
        flag, decoded_data, remaining_bits, remaining_bytes = result
        self.assertEqual(flag, 4)
        self.assertEqual(decoded_data, b'test_data')
        self.assertEqual(remaining_bits, '')
        self.assertEqual(len(remaining_bytes), 0)

    def test_is_file(self):
        decompressor = Decompressor()
        self.assertTrue(decompressor._is_file(self.archive_file))
        self.assertFalse(decompressor._is_file(self.test_dir.name))

    def test_bytes_to_bits(self):
        decompressor = Decompressor()
        data = b'\x48\x65\x6c\x6c\x6f'
        bits = decompressor._bytes_to_bits(data)
        self.assertEqual(bits, '0100100001100101011011000110110001101111')


if __name__ == '__main__':
    unittest.main()
