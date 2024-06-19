import heapq
from collections import Counter
import pickle
from typing import Dict, Tuple, Union, Optional


class HuffmanNode:
    """
    Сущность узла в дереве Хаффмана.
    """

    def __init__(self, char: Optional[str], freq: int):
        """
        Инициализирует объект класса HuffmanNode.

        :param char: Символ, связанный с узлом.
        :param freq: Частота встречаемости символа.
        """
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other: 'HuffmanNode') -> bool:
        """
        Сравнивает два объекта HuffmanNode на основе их частот.

        :param other: Другой объект HuffmanNode для сравнения.
        :return: True, если частота текущего узла меньше частоты другого,
         иначе False.
        """
        return self.freq < other.freq

    def is_leaf(self) -> bool:
        """
        Проверяет, является ли узел листом.

        :return: True, если узел является листом, иначе False.
        """
        return self.left is None and self.right is None


class HuffmanTree:
    """
    Сущность дерева кодирования Хаффмана.
    """

    def __init__(self, codec: Optional[str] = None):
        """
        Инициализирует объект класса HuffmanTree.

        :param codec: Кодек, используемый для декодирования. По умолчанию None.
        """
        self.root = None
        self.frequency = Counter()
        self.codec = codec

    def _build_codes(self,
                     node: HuffmanNode, prefix: str = '',
                     codes: Dict[str, str] = {}) -> Dict[str, str]:
        """
        Рекурсивно строит коды Хаффмана для символов в дереве.

        :param node: Текущий узел, который обрабатывается.
        :param prefix: Префиксный код, сгенерированный на данный момент.
        :param codes: Словарь для хранения кодов Хаффмана.
        :return: Словарь, содержащий коды Хаффмана для символов.
        """
        if node is not None:
            if node.char is not None:
                codes[node.char] = prefix
            self._build_codes(node.left, prefix + '0', codes)
            self._build_codes(node.right, prefix + '1', codes)
        return codes

    def get_codes(self) -> Dict[str, str]:
        """
        Генерирует коды Хаффмана для всех символов в дереве.

        :return: Словарь, содержащий коды Хаффмана для символов.
        """
        if self.root is None:
            return {}

        if self.root.left is None and self.root.right is None:
            return {self.root.char: '1'}

        return self._build_codes(self.root)

    def decode(self,
               bit_sequence: str,
               count: int = -1) -> Tuple[Union[bytes, str], str]:
        """
        Декодирует последовательность битов с использованием дерева Хаффмана.

        :param bit_sequence: Последовательность битов для декодирования.
        :param count: Количество битов для декодирования. По умолчанию -1.
        :return: Кортеж, содержащий декодированные данные и оставшиеся биты.
        """
        if self.root is None:
            raise ValueError('Дерево Хаффмана пусто. '
                             'невозможно декодировать данные')

        current_node = self.root

        if count >= 1:
            bit_sequence = bit_sequence[:-count]

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

    def add_block(self, block: Union[str, bytes]) -> None:
        """
        Добавляет блок данных в счетчик частот.

        :param block: Блок данных для добавления.
        """
        if not block:
            return
        self.frequency.update(block)

    def build_tree(self) -> None:
        """
        Строит дерево Хаффмана на основе счетчика частот.
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

    def serialize_to_string(self) -> bytes:
        """
        Сериализует дерево Хаффмана в строку с использованием pickle.

        :return: Сериализованное дерево в виде строки.
        """
        return pickle.dumps(self)

    def deserialize_from_string(self, serialized_tree_string: bytes) -> None:
        """
        Десериализует строку для восстановления дерева Хаффмана.

        :param serialized_tree_string: Сериализованная строка дерева.
        """
        deserialized_tree = pickle.loads(serialized_tree_string)
        self.root = deserialized_tree.root
        self.codec = deserialized_tree.codec

    def get_codec(self) -> Optional[str]:
        """
        Возвращает кодек, используемый для кодирования и декодирования.

        :return: Кодек, используемый для кодирования и декодирования.
        """
        return self.codec
