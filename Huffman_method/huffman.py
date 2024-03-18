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


class HuffmanTree:
    def __init__(self):
        self.root = None
        self.frequency = Counter()

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

    def add_block(self, block):
        if not block:
            return
        self.frequency.update(block)

    def build_tree(self):
        if len(self.frequency) == 1:
            char = next(iter(self.frequency.keys()))
            self.root = HuffmanNode(char, 1)
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
        return pickle.dumps(self.root)

    def deserialize_from_string(self, serialized_tree_string):
        self.root = pickle.loads(serialized_tree_string)
