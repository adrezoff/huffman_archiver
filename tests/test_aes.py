import unittest
from encryption.coding import aes_encrypt, aes_decrypt


class TestAES(unittest.TestCase):
    def test_encrypt_decrypt(self):
        plaintext = b'qwertyuiopasdfgh'
        key = b'l1ksh7cgqp,sjhd9'

        encrypted = aes_encrypt(plaintext, key)

        self.assertNotEqual(plaintext, encrypted)

        decrypted = aes_decrypt(encrypted, key)

        self.assertEqual(plaintext, decrypted)

    def test_long_encrypt_decrypt(self):
        plaintext = (b'This is a longer plaintext message '
                     b'to test AES encryption and'
                     b' decryption with a longer text.')
        key = b'AnotherSecretKey'

        encrypted = aes_encrypt(plaintext, key)

        decrypted = aes_decrypt(encrypted, key)

        self.assertEqual(plaintext, decrypted)


if __name__ == '__main__':
    unittest.main()
