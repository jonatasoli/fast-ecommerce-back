from cryptography.fernet import Fernet
from loguru import logger


def encrypt(message, key):
    logger.debug(f'Token Enc - {message}')
    logger.debug(f'Key Enc - {key}')
    return Fernet(key).encrypt(message)


def decrypt(token, key):
    logger.debug(f'Token - {token}')
    logger.debug(f'Key - {key}')
    return Fernet(key).decrypt(token)
