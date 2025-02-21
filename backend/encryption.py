from Crypto.Cipher import AES
import base64
from config import SECRET_KEY


def encrypt_message(message):
    cipher = AES.new(SECRET_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt_message(encrypted_message):
    raw_data = base64.b64decode(encrypted_message)
    nonce, tag, ciphertext = raw_data[:16], raw_data[16:32], raw_data[32:]
    cipher = AES.new(SECRET_KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()
