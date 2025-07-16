import base64
from cryptography.hazmat.primitives import serialization, hashes, hmac
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import padding as symmetric_padding
from config import DefaultConfig
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


CONFIG = DefaultConfig()


def _decrypt_symmetric_key(dataKey: str):
    with open("notifications.key", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

        # convert dataKey to bytes from base64
        dataKey_bytes = base64.b64decode(dataKey)

        # decrypt dataKey using private key
        decrypted_key = private_key.decrypt(
            dataKey_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )
        return decrypted_key


def _calculate_signature(key: bytes, data: bytes) -> str:
    data_bytes = base64.b64decode(data)
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data_bytes)
    signature = h.finalize()
    return base64.b64encode(signature).decode("utf-8")


def _decrypt_data(key: bytes, encrypted_data: str) -> str:
    """
    Decrypts the encrypted data using the provided symmetric key.
    """
    encrypted_bytes = base64.b64decode(encrypted_data)
    iv = key[:16]

    # Decrypt using the symmetric key
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_bytes) + decryptor.finalize()

    unpadder = symmetric_padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted_unpadded = unpadder.update(decrypted_data) + unpadder.finalize()

    return decrypted_unpadded.decode("utf-8")
