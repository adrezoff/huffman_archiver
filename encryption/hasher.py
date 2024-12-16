import struct
from typing import List, Union


class MD5:
    """
    Реализует алгоритм MD5 для хеширования данных.
    """

    def __init__(self) -> None:
        """
        Инициализирует объект класса MD5.
        """
        self.a: int = 0x67452301
        self.b: int = 0xEFCDAB89
        self.c: int = 0x98BADCFE
        self.d: int = 0x10325476

        self.k: List[int] = [0x00000000] * 64
        self.s: List[int] = [0] * 64

        for i in range(64):
            x: float = abs((2 ** 0.5 * abs((2 ** i) * (i + 1))) % 1)
            self.k[i] = int(2 ** 32 * x)
            self.s[i] = (7 * i) % 32 if i < 32 else (3 * i + 5) % 32

        self.data: bytes = b''

    @staticmethod
    def left_rotate(x: int, n: int) -> int:
        """
        Выполняет циклический сдвиг влево для 32-битового числа.

        :param x: Число, для которого выполняется сдвиг.
        :param n: Количество бит для сдвига.
        :return: Результат сдвига.
        """
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    @staticmethod
    def padding(message: bytes) -> bytes:
        """
        Добавляет дополнение к сообщению согласно алгоритму MD5.

        :param message: Сообщение для добавления дополнения.
        :return: Сообщение с дополнением.
        """
        if not message:
            return b''

        original_byte_len: int = len(message)
        original_bit_len: int = original_byte_len * 8

        message += b'\x80'

        while len(message) % 64 != 56:
            message += b'\x00'

        message += struct.pack('<Q', original_bit_len)

        return message

    def process_chunk(self, chunk: bytes) -> None:
        """
        Обрабатывает отдельный блок данных согласно алгоритму MD5.

        :param chunk: Блок данных для обработки.
        """
        a: int = self.a
        b: int = self.b
        c: int = self.c
        d: int = self.d

        for i in range(64):
            if i < 16:
                f: int = (b & c) | ((~b) & d)
                g: int = i
            elif i < 32:
                f = (d & b) | ((~d) & c)
                g = (5 * i + 1) % 16
            elif i < 48:
                f = b ^ c ^ d
                g = (3 * i + 5) % 16
            else:
                f = c ^ (b | (~d))
                g = (7 * i) % 16

            d, c, a = c, b, self.a
            temp: int = a + f + self.k[i]
            bytes_: int = temp + struct.unpack('<I',
                                               chunk[g * 4:g * 4 + 4])[0]
            b = (b + self.left_rotate(bytes_, self.s[i])) & 0xFFFFFFFF
            self.a = temp

        self.a = (self.a + a) & 0xFFFFFFFF
        self.b = (self.b + b) & 0xFFFFFFFF
        self.c = (self.c + c) & 0xFFFFFFFF
        self.d = (self.d + d) & 0xFFFFFFFF

    def hash(self, data: bytes) -> None:
        """
        Вычисляет хеш-значение для указанных данных.

        :param data: Данные для хеширования.
        """
        self.data += data
        while len(self.data) >= 64:
            chunk: bytes = self.data[:64]
            chunk: bytes = self.padding(chunk)
            self.process_chunk(chunk)
            self.data = self.data[64:]

    def get_hash(self) -> bytes:
        """
        Возвращает вычисленное 16 байтный хеш для переданных данных.

        :return: Хеш.
        """
        if self.data:
            chunk: bytes = self.padding(self.data)
            self.process_chunk(chunk)
            self.data = b''
        return struct.pack('<LLLL', self.a, self.b, self.c, self.d)
