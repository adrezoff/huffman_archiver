import heapq
from collections import Counter
import pickle


class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

    def is_leaf(self):
        return self.left is None and self.right is None


class HuffmanTree:
    def __init__(self, codec=None):
        self.root = None
        self.frequency = Counter()
        self.codec = codec

    def _build_codes(self, node, prefix='', codes={}):
        if node is not None:
            if node.char is not None:
                codes[node.char] = prefix
            self._build_codes(node.left, prefix + '0', codes)
            self._build_codes(node.right, prefix + '1', codes)
        return codes

    def get_codes(self):
        if self.root is None:
            return {}

        if self.root.left is None and self.root.right is None:
            return {self.root.char: '1'}

        return self._build_codes(self.root)

    def decode(self, bit_sequence, count=-1):
        if self.root is None:
            return
        current_node = self.root

        if count >= 0:
            bit_sequence = bit_sequence[:-(8 + count)]

        if self.codec is None:
            decoded_data = bytearray()
        else:
            decoded_data = list()
        remaining_bits = ''

        for bit_str in bit_sequence:

            remaining_bits += bit_str

            if bit_str == '0':
                current_node = current_node.left
            else:
                current_node = current_node.right

            if current_node.is_leaf():
                decoded_data.append(current_node.char)
                remaining_bits = ''
                current_node = self.root

        if self.codec is None:
            decoded_data = bytes(decoded_data)
        else:
            decoded_data = ''.join(decoded_data)

        return decoded_data, remaining_bits

    def add_block(self, block):
        if not block:
            return
        self.frequency.update(block)

    def build_tree(self):
        if len(self.frequency) == 1:
            char, freq = next(iter(self.frequency.items()))
            self.root = HuffmanNode(char, freq)
            return
        else:
            priority_queue = [HuffmanNode(char, freq) for char, freq in self.frequency.items()]
            heapq.heapify(priority_queue)

            while len(priority_queue) > 1:
                left = heapq.heappop(priority_queue)
                right = heapq.heappop(priority_queue)
                merged = HuffmanNode(None, left.freq + right.freq)
                merged.left = left
                merged.right = right
                heapq.heappush(priority_queue, merged)

            self.root = priority_queue[0]

    def serialize_to_string(self):
        return pickle.dumps(self)

    def deserialize_from_string(self, serialized_tree_string):
        deserialized_tree = pickle.loads(serialized_tree_string)
        self.root = deserialized_tree.root
        self.codec = deserialized_tree.codec

    def get_codec(self):
        return self.codec
