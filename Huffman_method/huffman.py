import heapq
from collections import Counter
import pickle


class HuffmanNode:
    """
    Класс, представляющий узел в дереве Хаффмана.

    Args:
        char (str): Символ, представленный текущим узлом.
        freq (int): Частота символа.

    Attributes:
        left (HuffmanNode): Левый дочерний узел.
        right (HuffmanNode): Правый дочерний узел.
    """

    def __init__(self, char, freq):
        """
        Инициализирует узел в дереве Хаффмана.

        Args:
            char (str): Символ, представленный текущим узлом.
            freq (int): Частота символа.
        """
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        """
        Сравнивает текущий узел с другим узлом по частоте.

        Args:
            other (HuffmanNode): Другой узел для сравнения.

        Returns:
            bool: True, если частота текущего узла меньше,
            чем у другого узла, иначе False.
        """
        return self.freq < other.freq

    def is_leaf(self):
        """
        Проверяет, является ли текущий узел листом.

        Returns:
            bool: True, если текущий узел лист, иначе False.
        """
        return self.left is None and self.right is None


class HuffmanTree:
    """
    Класс, представляющий дерево Хаффмана.

    Attributes:
        root (HuffmanNode): Корневой узел дерева.
        frequency (Counter): Счетчик частот символов.
        codec (any): Кодек для сериализации/десериализации дерева.
    """

    def __init__(self, codec=None):
        """
        Инициализирует дерево Хаффмана.

        Args:
            codec (str): Кодек для сериализации/десериализации
             дерева. По умолчанию None.
        """
        self.root = None
        self.frequency = Counter()
        self.codec = codec

    def _build_codes(self, node, prefix='', codes={}):
        """
        Рекурсивно строит коды символов на основе дерева Хаффмана.

        Args:
            node (HuffmanNode): Текущий узел дерева.

            prefix (str): Префикс для текущего пути.
            По умолчанию ''.

            codes (dict): Словарь кодов символов.
            По умолчанию {}.

        Returns:
            dict: Словарь кодов символов.
        """
        if node is not None:
            if node.char is not None:
                codes[node.char] = prefix
            self._build_codes(node.left, prefix + '0', codes)
            self._build_codes(node.right, prefix + '1', codes)
        return codes

    def get_codes(self):
        """
        Возвращает коды символов, построенные на основе дерева
        Хаффмана.

        Returns:
            dict: Словарь кодов символов.
        """
        if self.root is None:
            return {}

        if self.root.left is None and self.root.right is None:
            return {self.root.char: '1'}

        return self._build_codes(self.root)

    def decode(self, bit_sequence, count=-1):
        """
        Декодирует битовую последовательность с использованием дерева
        Хаффмана.

        Args:
            bit_sequence (str): Битовая последовательность
            для декодирования.

            count (int): Количество дополнительных битов,
            которые следует проигнорировать.
                По умолчанию -1.

        Returns:
            tuple: Декодированные данные и оставшиеся биты.
        """
        if self.root is None:
            return
        current_node = self.root

        if count >= 0:
            bit_sequence = bit_sequence[:-(8 + count)]

        if self.codec is None:
            decoded_data = bytearray()
        else:
            decoded_data = []
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
        """
        Обновляет частоты символов на основе переданного блока.

        Args:
            block (str): Блок данных для обновления частот.
        """
        if not block:
            return
        self.frequency.update(block)

    def build_tree(self):
        """
        Строит дерево Хаффмана на основе частот символов.
        """
        if len(self.frequency) == 1:
            char, freq = next(iter(self.frequency.items()))
            self.root = HuffmanNode(char, freq)
            return
        else:
            priority_queue = []
            for char, freq in self.frequency.items():
                priority_queue.append(HuffmanNode(char, freq))
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
        """
        Сериализует дерево Хаффмана в строку.

        Returns:
            bytes: Сериализованное представление дерева Хаффмана.
        """
        return pickle.dumps(self)

    def deserialize_from_string(self, serialized_tree_string):
        """
        Десериализует дерево Хаффмана из строки.

        Args:
            serialized_tree_string (bytes): Строка, содержащая
            сериализованное представление дерева Хаффмана.
        """
        deserialized_tree = pickle.loads(serialized_tree_string)
        self.root = deserialized_tree.root
        self.codec = deserialized_tree.codec

    def get_codec(self):
        """
        Возвращает кодек, используемый для сериализации/десериализации
        дерева.

        Returns:
            any: Кодек для сериализации/десериализации дерева.
        """
        return self.codec
