import unittest
from Huffman_method.hasher import MD5


class TestMD5(unittest.TestCase):
    def setUp(self):
        self.md5 = MD5()

    def test_hash(self):
        test_string = b'hello world'
        self.md5.hash(test_string)
        expected_hash = b'\xb1\xfc\x12\x089\xc7\xf4\xef\xba\xff\xf8\r\xaf\xe1\x91\xd2'
        self.assertEqual(self.md5.get_hash(), expected_hash)

        self.md5 = MD5()
        self.md5.hash(b'')
        expected_hash = b'\x01#Eg\x89\xab\xcd\xef\xfe\xdc\xba\x98vT2\x10'
        self.assertEqual(self.md5.get_hash(), expected_hash)


if __name__ == '__main__':
    unittest.main()
