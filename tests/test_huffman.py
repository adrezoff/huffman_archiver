import unittest
from collections import Counter

from huffman_method import HuffmanNode, HuffmanTree


class TestHuffmanNode(unittest.TestCase):

    def test_init(self):
        node = HuffmanNode('a', 5)
        self.assertEqual(node.char, 'a')
        self.assertEqual(node.freq, 5)
        self.assertIsNone(node.left)
        self.assertIsNone(node.right)

    def test_is_leaf(self):
        leaf_node = HuffmanNode('a', 5)
        self.assertTrue(leaf_node.is_leaf())

        internal_node = HuffmanNode(None, 10)
        internal_node.left = HuffmanNode('b', 4)
        internal_node.right = HuffmanNode('c', 6)
        self.assertFalse(internal_node.is_leaf())


class TestHuffmanTree(unittest.TestCase):

    def test_init(self):
        tree = HuffmanTree()
        self.assertIsNone(tree.root)
        self.assertEqual(tree.frequency, {})

    def test_build_tree(self):
        tree = HuffmanTree()
        tree.add_block(b'hello')
        tree.build_tree()
        self.assertIsNotNone(tree.root)

    def test_add_block(self):
        tree = HuffmanTree()
        tree.add_block('hello')
        tempfenq = Counter({'h': 1, 'e': 1, 'l': 2, 'o': 1})
        self.assertEqual(tree.frequency, tempfenq)

    def test_decode(self):
        tree = HuffmanTree()
        tree.add_block(b'hello')
        tree.build_tree()
        bit_sequence = '1001111100'
        decoded_data, remaining_bits = tree.decode(bit_sequence)
        self.assertEqual(decoded_data, b'hello')
        self.assertEqual(remaining_bits, '')

    def test_serialize_and_deserialize(self):
        tree = HuffmanTree()
        tree.add_block(b'hello')
        tree.build_tree()
        serialized_tree = tree.serialize_to_string()
        deserialized_tree = HuffmanTree()
        deserialized_tree.deserialize_from_string(serialized_tree)
        self.assertEqual(tree.get_codes(), deserialized_tree.get_codes())


if __name__ == '__main__':
    unittest.main()
