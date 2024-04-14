import struct


class MD5:
    """
    Реализация алгоритма хеширования MD5.

    Атрибуты:
        a (int): Начальное значение A.
        b (int): Начальное значение B.
        c (int): Начальное значение C.
        d (int): Начальное значение D.
        k (list): Список констант, используемых в алгоритме MD5.
        s (list): Список сдвигов, используемых в алгоритме MD5.
        data (bytes): Данные для хеширования.
    """

    def __init__(self):
        """
        Инициализирует экземпляр MD5 значениями по умолчанию.
        """
        self.a = 0x67452301
        self.b = 0xEFCDAB89
        self.c = 0x98BADCFE
        self.d = 0x10325476

        self.k = [0x00000000] * 64
        self.s = [0] * 64

        for i in range(64):
            x = abs((2 ** 0.5 * abs((2 ** i) * (i + 1))) % 1)
            self.k[i] = int(2 ** 32 * x)
            self.s[i] = (7 * i) % 32 if i < 32 else (3 * i + 5) % 32

        self.data = b''

    @staticmethod
    def left_rotate(x, n):
        """
        Выполняет циклический сдвиг влево для заданного значения.

        Args:
            x (int): Значение для сдвига.
            n (int): Количество бит для сдвига.

        Returns:
            int: Сдвинутое значение.
        """
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

    @staticmethod
    def padding(message):
        """
        Применяет дополнение к входному сообщению.

        Args:
            message (bytes): Входное сообщение.

        Returns:
            bytes: Сообщение с дополнением.
        """
        if not message:
            return b''

        original_byte_len = len(message)
        original_bit_len = original_byte_len * 8

        message += b'\x80'

        while len(message) % 64 != 56:
            message += b'\x00'

        message += struct.pack('<Q', original_bit_len)

        return message

    def process_chunk(self, chunk):
        """
        Обрабатывает 64-байтный блок данных.

        Args:
            chunk (bytes): Входной блок данных.
        """
        a, b, c, d = self.a, self.b, self.c, self.d
        for i in range(64):
            if i < 16:
                f = (b & c) | ((~b) & d)
                g = i
            elif i < 32:
                f = (d & b) | ((~d) & c)
                g = (5 * i + 1) % 16
            elif i < 48:
                f = b ^ c ^ d
                g = (3 * i + 5) % 16
            else:
                f = c ^ (b | (~d))
                g = (7 * i) % 16

            temp = d
            d = c
            c = b
            temp = a + f + self.k[i]
            bytes = temp + struct.unpack('<I', chunk[g * 4:g * 4 + 4])[0]
            b = (b + self.left_rotate(bytes, self.s[i])) & 0xFFFFFFFF
            a = temp

        self.a = (self.a + a) & 0xFFFFFFFF
        self.b = (self.b + b) & 0xFFFFFFFF
        self.c = (self.c + c) & 0xFFFFFFFF
        self.d = (self.d + d) & 0xFFFFFFFF

    def hash(self, data):
        """
        Хеширует данные.

        Args:
            data (bytes): Данные для хеширования.
        """
        self.data += data
        while len(self.data) >= 64:
            chunk = self.data[:64]
            chunk = self.padding(chunk)
            self.process_chunk(chunk)
            self.data = self.data[64:]

    def get_hash(self):
        """
        Возвращает хеш.

        Returns:
            bytes: Хеш-значение.
        """
        if self.data:
            chunk = self.padding(self.data)
            self.process_chunk(chunk)
            self.data = b''
        return struct.pack('<LLLL', self.a, self.b, self.c, self.d)
